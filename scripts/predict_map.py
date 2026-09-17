"""Uc durumun tam %0-100 araligi icin birlesik mapping tablosu uretir.

ONEMLI: bu script OLCUM URETMEZ. Olculen araligin disini doldurur ve her
hucreyi kaynagina gore isaretler:

  measured      -> o yonun kendi olcumunden dogrusal interpolasyon
  bridged       -> DIGER yonun olcumunden, iki yon arasindaki sabit
                   rho oraniyla cevrildi (veriyle dogrulandi, ~%2 hata)
  extrapolated  -> veri yok; o yonun rho egilimi uzatildi. YALNIZCA UST
                   ucta kullanilir (sarj tavanina dogru daralma).
  no_data       -> hucre bos. Alt uc icin ekstrapolasyon YAPILMAZ.

ALT UC KURALI: olculen araligin altinda tahmin uretilmez. Onceki surum
rho egilimini asagi uzatiyordu ve sarj sapmasini +204 mV'a cikariyordu;
olculen en buyuk sapma 165,6 mV. Yani veride olmayan bir acilma
uyduruluyordu. Artik alt sinirda tablo biter.

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


class Estimator:
    """Verilen dinlenmis gerilimde uc durumu ve her birinin kaynagini verir.

    soc_curve.py da bunu kullanir: iki script de dogrudan olcumden hesaplar,
    yani birinin ciktisini digerine 12 mV'lik izgarayla aktarmaktan dogan
    sinir kopmasi olmaz.
    """

    def __init__(self, charge, discharge) -> None:
        self.charge, self.discharge = charge, discharge
        self.ratio, self.ratio_sd = rho_ratio(charge, discharge)
        self.lo_fit = lsq([o for o, _, _ in discharge],
                          [rho(t, d) for _, t, d in discharge])
        # Uzatma, uyumun *egimini* kullanir ama *seviyesini* olculen uc
        # noktaya sabitler. Ham uyum sinirda olcumden ~%6 sapip grafikte
        # yapay bir kirik yaratiyordu.
        self._edge = (discharge[-1][0], rho(discharge[-1][1], discharge[-1][2]))
        self.ch_lo, self.ch_hi = charge[0][0], charge[-1][0]
        self.ld_lo, self.ld_hi = discharge[0][0], discharge[-1][0]

    def rho_load_outside(self, ocv: float) -> float:
        return self._edge[1] + self.lo_fit[1] * (ocv - self._edge[0])

    def charging_at(self, ocv: float) -> tuple[float | None, str]:
        d = interp(self.charge, ocv, 2)
        if d is not None:
            return min(ocv + d, CHARGER_CEILING_MV), "measured"

        dl, tl = interp(self.discharge, ocv, 2), interp(self.discharge, ocv, 1)
        if dl is not None and ocv <= CC_MAX_OCV:
            d = delta_from_rho(self.ratio * rho(tl, dl), ocv, charging=True)
            return min(ocv + d, CHARGER_CEILING_MV), "bridged"

        if ocv > self.ch_hi:
            # CV bolgesi: terminal gerilimi sarj tavanina dogru kapanir.
            term = self.charge[-1][1] + \
                (CHARGER_CEILING_MV - self.charge[-1][1]) * \
                (ocv - self.ch_hi) / (CHARGER_CEILING_MV - self.ch_hi)
            return min(term, CHARGER_CEILING_MV), "extrapolated"

        return None, "no_data"   # alt uc: uydurulmaz

    def loaded_at(self, ocv: float) -> tuple[float | None, str]:
        d = interp(self.discharge, ocv, 2)
        if d is not None:
            return max(0.0, ocv - d), "measured"
        if ocv > self.ld_hi:
            # Kopru burada KULLANILMAZ: sarj kosusu bu bolgede CV'de oldugu
            # icin oran gecersiz. Kendi rho egilimi uzatilir.
            d = delta_from_rho(self.rho_load_outside(ocv), ocv, charging=False)
            return max(0.0, ocv - d), "extrapolated"
        return None, "no_data"   # alt uc: uydurulmaz


def build_estimator() -> Estimator:
    charge, discharge = load_runs()
    return Estimator(charge, discharge)


def main() -> None:
    est = build_estimator()
    print(f"rho_yuk  = {est.lo_fit[0]:.3f} {est.lo_fit[1]:+.6f}*ocv   "
          f"kalinti sd={est.lo_fit[2]:.2f}")
    print(f"rho orani (sarj CC / yuk) = {est.ratio:.3f} +/- {est.ratio_sd:.3f}")

    # Kopru dogrulamasi: sarjin en alt olculen noktasini yukten uretip karsilastir.
    probe = est.ch_lo
    dl, tl = interp(est.discharge, probe, 2), interp(est.discharge, probe, 1)
    if None not in (dl, tl):
        d = delta_from_rho(est.ratio * rho(tl, dl), probe, charging=True)
        print(f"kopru dogrulamasi @ ocv={probe:.1f}: tahmin {d:.1f} mV, "
              f"olculen {est.charge[0][2]:.1f} mV, hata {d - est.charge[0][2]:+.1f} mV")

    obs_lo = min(est.ch_lo, est.ld_lo)
    obs_hi = max(est.ch_hi, est.ld_hi)

    out = ROOT / "data" / "lookup-combined.csv"
    with out.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["voltage_pct", "rested_mv", "charging_mv", "loaded_mv",
                         "charging_src", "loaded_src", "rested_observed"])
        for step in range(101):
            ocv = rested_mv(float(step))
            charging, ch_src = est.charging_at(ocv)
            loaded, ld_src = est.loaded_at(ocv)
            writer.writerow([
                f"{step}", f"{ocv:.1f}",
                "" if charging is None else f"{charging:.1f}",
                "" if loaded is None else f"{loaded:.1f}",
                ch_src, ld_src, "yes" if obs_lo <= ocv <= obs_hi else "no",
            ])

    print(f"\nyazildi: {out.relative_to(ROOT)}")
    print(f"olculen sarj araligi : {est.ch_lo:.1f} - {est.ch_hi:.1f} mV (dinlenmis)")
    print(f"olculen yuk araligi  : {est.ld_lo:.1f} - {est.ld_hi:.1f} mV (dinlenmis)")
    print(f"hucrenin gozlendigi  : {obs_lo:.1f} - {obs_hi:.1f} mV (dinlenmis)")


if __name__ == "__main__":
    main()
