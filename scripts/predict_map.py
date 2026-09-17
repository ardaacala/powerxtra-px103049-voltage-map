"""Uc durumun tam %0-100 araligi icin birlesik mapping tablosu uretir.

ONEMLI: bu script OLCUM URETMEZ. Olculen araligin disini doldurur ve her
hucreyi kaynagina gore isaretler:

  measured      -> o yonun kendi olcumunden dogrusal interpolasyon
  bridged       -> DIGER yonun olcumunden, iki yon arasindaki sabit
                   rho oraniyla cevrildi (veriyle dogrulandi, ~%2 hata)
  extrapolated  -> her iki yonun da verisi yok; o yonun rho egilimi
                   dogrusal olarak uzatildi. En zayif sinif.

Cikti:  data/lookup-combined.csv   (%1 adimli, 101 satir)
Kullanim:  python scripts/predict_map.py
"""

from __future__ import annotations

import csv
import statistics as st
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

# Gerilim olcegi (firmware'deki BatteryConfig.h ile ayni).
EMPTY_MV = 3000.0
FULL_MV = 4200.0

# Sarj IC'sinin sabit gerilim tavani. Terminal gerilimi bunu asamaz.
CHARGER_CEILING_MV = 4200.0

# rho orani yalnizca sarjin sabit akim (CC) bolgesinde anlamli. CV'ye
# gecince sarj akimi dustugu icin oran bozulur; ust sinir buradan.
CC_MAX_OCV = 3835.0
# Alt satirlar 60 s'de oturmadigi icin (README sinir 1) orana katilmaz.
RELIABLE_MIN_OCV = 3520.0


def rested_mv(pct: float) -> float:
    return EMPTY_MV + (FULL_MV - EMPTY_MV) * pct / 100.0


def load_runs() -> tuple[list[tuple[float, float, float]], list[tuple[float, float, float]]]:
    """(ocv, terminal, |sapma|) uclulerini ocv'ye gore artan sirada dondurur."""
    def read(name: str, term_col: str, rest_col: str):
        rows = []
        with (ROOT / "data" / name).open(encoding="utf-8") as handle:
            for raw in csv.DictReader(handle):
                if raw["complete"] != "1" or not raw[rest_col]:
                    continue
                rows.append((float(raw[rest_col]), float(raw[term_col]),
                             abs(float(raw["delta_mv"]))))
        return sorted(rows)

    charge = read("measurements.csv", "charging_mv", "rested_mv")
    discharge = read("measurements-discharge.csv", "loaded_mv", "recovered_mv")
    return charge, discharge


def rho(terminal_mv: float, abs_delta_mv: float) -> float:
    """Ic direnc gostergesi: |sapma|/terminal. Yukun direncine bolunmus
    R_ic ile orantili, o yuzden birimsiz (1000x olcekli)."""
    return 1000.0 * abs_delta_mv / terminal_mv


def interp(points: list[tuple[float, ...]], x: float, index: int) -> float | None:
    """Olculen araligin *icinde* dogrusal interpolasyon; disinda None."""
    for a, b in zip(points, points[1:]):
        if a[0] <= x <= b[0]:
            span = b[0] - a[0]
            f = 0.0 if span == 0 else (x - a[0]) / span
            return a[index] + f * (b[index] - a[index])
    return None


def lsq(xs: list[float], ys: list[float]) -> tuple[float, float, float]:
    """Dogrusal en kucuk kareler -> (kesim, egim, kalinti_sd)."""
    mx, my = st.mean(xs), st.mean(ys)
    sxx = sum((x - mx) ** 2 for x in xs)
    slope = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / sxx
    intercept = my - slope * mx
    residuals = [y - (intercept + slope * x) for x, y in zip(xs, ys)]
    return intercept, slope, st.pstdev(residuals)


def rho_ratio(charge, discharge) -> tuple[float, float]:
    """rho_sarj / rho_yuk, ayni ocv'de, yalnizca guvenilir CC bolgesinde."""
    ratios = []
    lo = max(RELIABLE_MIN_OCV, charge[0][0], discharge[0][0])
    hi = min(CC_MAX_OCV, charge[-1][0], discharge[-1][0])
    ocv = lo
    while ocv <= hi:
        tc, dc = interp(charge, ocv, 1), interp(charge, ocv, 2)
        tl, dl = interp(discharge, ocv, 1), interp(discharge, ocv, 2)
        if None not in (tc, dc, tl, dl):
            ratios.append(rho(tc, dc) / rho(tl, dl))
        ocv += 25.0
    return st.mean(ratios), st.pstdev(ratios)


def delta_from_rho(rho_value: float, ocv: float, charging: bool) -> float:
    """rho tanimi terminal gerilimine gore oldugu icin sapma ters cozulur.

    Sarjda  terminal = ocv + d  ve  rho = 1000*d/terminal -> d = rho*ocv/(1000-rho)
    Yukte   terminal = ocv - d                            -> d = rho*ocv/(1000+rho)
    """
    return rho_value * ocv / ((1000.0 - rho_value) if charging else (1000.0 + rho_value))


def main() -> None:
    charge, discharge = load_runs()
    ratio, ratio_sd = rho_ratio(charge, discharge)

    # Her yonun kendi rho egilimi -- olculen araligin disi icin.
    lo_fit = lsq([o for o, _, _ in discharge], [rho(t, d) for _, t, d in discharge])
    print(f"rho_yuk  = {lo_fit[0]:.3f} {lo_fit[1]:+.6f}*ocv   kalinti sd={lo_fit[2]:.2f}")
    print(f"rho orani (sarj CC / yuk) = {ratio:.3f} +/- {ratio_sd:.3f}")

    # Uzatma, uyumun *egimini* kullanir ama *seviyesini* olculen uc noktaya
    # sabitler. Boylece sinirda sicrama olmaz; ham uyum orada olcumden
    # ~%6 sapiyor ve grafikte yapay bir kirik yaratiyordu.
    edge_lo = (discharge[0][0], rho(discharge[0][1], discharge[0][2]))
    edge_hi = (discharge[-1][0], rho(discharge[-1][1], discharge[-1][2]))

    def rho_load_outside(ocv: float) -> float:
        anchor = edge_lo if ocv < edge_lo[0] else edge_hi
        return anchor[1] + lo_fit[1] * (ocv - anchor[0])

    # Kopru dogrulamasi: sarjin en alt olculen noktasini yukten uretip karsilastir.
    probe = charge[0][0]
    rl = interp(discharge, probe, 2), interp(discharge, probe, 1)
    if None not in rl:
        est = delta_from_rho(ratio * rho(rl[1], rl[0]), probe, charging=True)
        print(f"kopru dogrulamasi @ ocv={probe:.1f}: tahmin {est:.1f} mV, "
              f"olculen {charge[0][2]:.1f} mV, hata {est - charge[0][2]:+.1f} mV")

    ch_lo, ch_hi = charge[0][0], charge[-1][0]
    ld_lo, ld_hi = discharge[0][0], discharge[-1][0]
    obs_lo, obs_hi = min(ch_lo, ld_lo), max(ch_hi, ld_hi)

    out = ROOT / "data" / "lookup-combined.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["voltage_pct", "rested_mv", "charging_mv", "loaded_mv",
                         "charging_src", "loaded_src", "rested_observed"])
        for step in range(101):
            pct = float(step)
            ocv = rested_mv(pct)

            # --- sarj yonu ---
            d = interp(charge, ocv, 2)
            if d is not None:
                ch_src = "measured"
            else:
                dl, tl = interp(discharge, ocv, 2), interp(discharge, ocv, 1)
                if dl is not None and ocv <= CC_MAX_OCV:
                    # Diger yonun olcumu var: kopru.
                    d = delta_from_rho(ratio * rho(tl, dl), ocv, charging=True)
                    ch_src = "bridged"
                elif ocv > ch_hi:
                    # CV bolgesi: sarj tavanina dogru dogrusal kapanis.
                    term = charge[-1][1] + (CHARGER_CEILING_MV - charge[-1][1]) * \
                        (ocv - ch_hi) / (CHARGER_CEILING_MV - ch_hi)
                    d = max(0.0, min(term, CHARGER_CEILING_MV) - ocv)
                    ch_src = "extrapolated"
                else:
                    d = delta_from_rho(ratio * rho_load_outside(ocv), ocv,
                                       charging=True)
                    ch_src = "extrapolated"
            charging = min(ocv + d, CHARGER_CEILING_MV)

            # --- yuk yonu ---
            d = interp(discharge, ocv, 2)
            if d is not None:
                ld_src = "measured"
            else:
                # Kopru burada KULLANILMAZ: ocv > 3883 bolgesinde sarj kosusu
                # CV'de oldugu icin oran gecersiz. Kendi rho egilimi uzatilir.
                d = delta_from_rho(rho_load_outside(ocv), ocv, charging=False)
                ld_src = "extrapolated"
            loaded = max(0.0, ocv - d)

            writer.writerow([
                f"{pct:.0f}", f"{ocv:.1f}", f"{charging:.1f}", f"{loaded:.1f}",
                ch_src, ld_src, "yes" if obs_lo <= ocv <= obs_hi else "no",
            ])

    print(f"\nyazildi: {out.relative_to(ROOT)}")
    print(f"olculen sarj araligi : {ch_lo:.1f} - {ch_hi:.1f} mV (dinlenmis)")
    print(f"olculen yuk araligi  : {ld_lo:.1f} - {ld_hi:.1f} mV (dinlenmis)")
    print(f"hucrenin gozlendigi  : {obs_lo:.1f} - {obs_hi:.1f} mV (dinlenmis)")


if __name__ == "__main__":
    main()
