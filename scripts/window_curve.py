"""Desarj kosusunun kapasite penceresini coulomb sayimiyla uretir.

Neden gerekli: gerilim indeksi (%) gerilimde dogrusaldir, yani dinlenmis egri
tanim geregi duz bir kosegen cikar ve bataryanin karakteristik plato + uc diz
sekli hic gorunmez. Kapasite ekseni bunu ortaya cikarir.

Yontem -- yalnizca desarj kosusu kullanilir, cunku olculebilir olan o:
  yuk sabit direnc  ->  I = V_yuk / R_load
  firmware yuk-acik suresini ayri tutuyor (total_load_ms), dinlenmeler dahil
  degil  ->  Q = integral(I dt) = integral(V_yuk dt) / R_load
R_load normalize edilince sadelesir, yani egrinin *sekli* icin bilinmesi
gerekmiyor.

Sarj kosusu eksene KATILMAZ: sabit gerilim (CV) asamasinda akim bilinmiyor,
Q ~ t varsayimi orada gecersiz. Sarj kosusunun gerilimleri dinlenmis gerilim
uzerinden eksene tasinir (dinlenmis->kapasite hucrenin ozelligi, yonden
bagimsiz).

DIKKAT -- window_pct MUTLAK SoC DEGILDIR. %100 kosunun basi (dinlenmis
3887 mV), %0 kosunun sonu (yuk altinda 2995 mV). Kosu dolu hucreden
baslamadi: hucre sarjda dinlenmis 4089 mV'a kadar cikmisti. Sarj suresi
argumaniyla bu pencere hucrenin %36-53'u cikiyor (asagida hesaplaniyor),
yani pencereyi 0-100 SoC gibi sunmak ekseni 1,9-2,8 kat gerdirir. O yuzden
sutun adi soc_pct DEGIL window_pct.

Cikti:  data/window-curve.csv
Kullanim:  python scripts/window_curve.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from predict_map import (  # noqa: E402  (ROOT kurulduktan sonra)
    CC_MAX_OCV, RELIABLE_MIN_OCV, build_estimator, rho,
)

# Desarj kosusunun baslangici: yuk hic baglanmadan okunan dinlenmis deger.
# raw_dump-discharge.log icindeki "# BASELINE,...,battery_mv=3887.19"
BASELINE_MV = 3887.19


def discharge_rows() -> list[tuple[int, float, float]]:
    """(total_load_ms, loaded_mv, recovered_mv), yuk suresine gore artan."""
    rows = []
    with (ROOT / "data" / "measurements-discharge.csv").open(encoding="utf-8") as h:
        for r in csv.DictReader(h):
            if r["complete"] != "1" or not r["recovered_mv"]:
                continue
            rows.append((int(r["total_load_ms"]), float(r["loaded_mv"]),
                         float(r["recovered_mv"])))
    return sorted(rows)


def window_capacity() -> float:
    """Kosunun bosalttigi toplam yuk (mV*s / R_load)."""
    rows = discharge_rows()
    q = 0.0
    prev_t, prev_v = 0, rows[0][1]
    for t, v, _ in rows:
        q += 0.5 * (prev_v + v) * (t - prev_t) / 1000.0
        prev_t, prev_v = t, v
    return q


def charge_rows() -> list[tuple[float, float, float, float]]:
    """(ocv, terminal, |sapma|, total_charge_ms), ocv'ye gore artan."""
    rows = []
    with (ROOT / "data" / "measurements.csv").open(encoding="utf-8") as h:
        for r in csv.DictReader(h):
            if r["complete"] != "1" or not r["rested_mv"]:
                continue
            rows.append((float(r["rested_mv"]), float(r["charging_mv"]),
                         abs(float(r["delta_mv"])), float(r["total_charge_ms"])))
    return sorted(rows)


def window_share_bounds() -> tuple[float, float]:
    """Pencerenin hucrenin yuzde kacini kapsadigini SINIRLAR (alt, ust).

    Ust bantta (kosu basi -> sarj kosusunun tepesi) sarj CV asamasinda ve
    akim bilinmiyor. Ama CV'de akim yalnizca DUSER, o yuzden sarj kosusunun
    olculen suresi iki tarafli sinir verir:
      kapasite ust siniri: butun sure boyunca CC akimi akmis olsa
      kapasite alt siniri: butun sure boyunca son (en kucuk) akim akmis olsa
    Akimlar desarj birimiyle yazilir (I ~ 1000*sapma/rho), R_load sadelesir.
    """
    ld = discharge_rows()                       # (t_ms, loaded, recovered)
    rho_by_ocv = sorted((ocv, rho(v, ocv - v)) for _, v, ocv in ld)
    ch = charge_rows()
    q_win = window_capacity()

    cc = [1000.0 * d / r
          for ocv, _, d, _ in ch
          if (r := interp(rho_by_ocv, ocv)) is not None
          and RELIABLE_MIN_OCV <= ocv <= CC_MAX_OCV]
    i_cc = sum(cc) / len(cc)

    # Kosu basindaki dinlenmis gerilime denk gelen sarj suresi.
    run_start_ocv = max(o for _, _, o in ld)
    t_at = interp([(ocv, t) for ocv, _, _, t in ch], run_start_ocv)
    t_top = (ch[-1][3] - t_at) / 1000.0

    i_end = 1000.0 * ch[-1][2] / rho_by_ocv[-1][1]   # en ust rho duz kabul

    q_hi, q_lo = i_cc * t_top, i_end * t_top
    return (100.0 * q_win / (q_win + q_hi),
            100.0 * q_win / (q_win + q_lo))


def soc_from_coulombs() -> list[tuple[float, float]]:
    """(ocv_mv, window_pct) ciftleri, ocv'ye gore artan.

    Q birimi mV*s; R_load'a bolunmus haldedir ve normalize edilince gider.
    """
    rows = discharge_rows()

    # Kumulatif bosalan yuk. Ilk noktaya kadar da yuk akti: baseline'dan
    # ilk olcume kadar V_yuk ilk olculen degere yakin kabul edilir.
    cumulative = []
    q = 0.0
    prev_t, prev_v = 0, rows[0][1]
    for t, v, ocv in rows:
        q += 0.5 * (prev_v + v) * (t - prev_t) / 1000.0
        cumulative.append((ocv, q))
        prev_t, prev_v = t, v
    q_total = q

    # SoC %100 kosunun basi (baseline, hic yuk cekilmemis), %0 kosunun sonu.
    points = [(BASELINE_MV, 100.0)]
    points += [(ocv, 100.0 * (1.0 - qq / q_total)) for ocv, qq in cumulative]

    # Ayni ocv'ye iki nokta dusmesin; artan sirada tek degerli kalsin.
    points.sort()
    cleaned: list[tuple[float, float]] = []
    for ocv, soc in points:
        if cleaned and ocv <= cleaned[-1][0]:
            continue
        cleaned.append((ocv, soc))
    return cleaned


def interp(points: list[tuple[float, float]], x: float) -> float | None:
    """Olculen araligin icinde dogrusal interpolasyon; disinda None."""
    for a, b in zip(points, points[1:]):
        if a[0] <= x <= b[0]:
            span = b[0] - a[0]
            f = 0.0 if span == 0 else (x - a[0]) / span
            return a[1] + f * (b[1] - a[1])
    return None


def main() -> None:
    ocv_soc = soc_from_coulombs()
    soc_ocv = sorted((soc, ocv) for ocv, soc in ocv_soc)

    # Sarjda/yukte degerleri ve kaynaklari dogrudan olcumden hesaplanir --
    # lookup-combined.csv'nin 12 mV'lik izgarasindan odunc alinmaz, cunku
    # o izgara veri sinirina denk gelmeyip SoC %0'i bos birakiyordu.
    est = build_estimator()

    out = ROOT / "data" / "window-curve.csv"
    with out.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["window_pct", "rested_mv", "charging_mv", "loaded_mv",
                    "charging_src", "loaded_src"])
        for step in range(101):
            ocv = interp(soc_ocv, float(step))
            if ocv is None:
                continue
            ch, ch_src = est.charging_at(ocv)
            ld, ld_src = est.loaded_at(ocv)
            w.writerow([
                f"{step}", f"{ocv:.1f}",
                "" if ch is None else f"{ch:.1f}",
                "" if ld is None else f"{ld:.1f}",
                ch_src, ld_src,
            ])

    print(f"yazildi: {out.relative_to(ROOT)}")
    print(f"pencere: dinlenmis {ocv_soc[0][0]:.1f} mV (%0) -> "
          f"{ocv_soc[-1][0]:.1f} mV (%100)")

    lo, hi = window_share_bounds()
    print(f"\nBu pencere hucrenin %{lo:.0f}-{hi:.0f}'unu kapsiyor "
          f"(sarj suresi argumaniyla iki tarafli sinir).")
    print(f"Yani pencereyi 0-100 SoC gibi sunmak ekseni "
          f"{100/hi:.1f}-{100/lo:.1f} kat gerdirir -- window_pct mutlak SoC DEGIL.")

    print("\nwindow_pct  dinlenmis(mV)   -- gerilim indeksiyle kiyas")
    for step in range(0, 101, 10):
        ocv = interp(soc_ocv, float(step))
        vi = 100.0 * (ocv - 3000.0) / 1200.0
        print(f"{step:10d}  {ocv:10.1f}      gerilim indeksi %{vi:.1f}")


if __name__ == "__main__":
    main()
