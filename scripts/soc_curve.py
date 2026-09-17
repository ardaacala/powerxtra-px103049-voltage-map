"""Gercek sarj durumu (SoC) eksenini desarj kosusundan coulomb sayimiyla uretir.

Neden gerekli: gerilim indeksi (%) gerilimde dogrusaldir, yani dinlenmis egri
tanim geregi duz bir kosegen cikar ve bataryanin karakteristik plato + uc diz
sekli hic gorunmez. Gercek SoC ekseni bunu ortaya cikarir.

Yontem -- yalnizca desarj kosusu kullanilir, cunku olculebilir olan o:
  yuk sabit direnc  ->  I = V_yuk / R_load
  firmware yuk-acik suresini ayri tutuyor (total_load_ms), dinlenmeler dahil
  degil  ->  Q = integral(I dt) = integral(V_yuk dt) / R_load
R_load normalize edilince sadelesir, yani SoC'nin *sekli* icin bilinmesi
gerekmiyor.

Sarj kosusu bu eksene KATILMAZ: sabit gerilim (CV) asamasinda akim bilinmiyor,
Q ~ t varsayimi orada gecersiz. Sarj kosusunun gerilimleri OCV uzerinden bu
eksene tasinir (OCV->SoC hucrenin ozelligi, yonden bagimsiz).

Cikti:  data/soc-curve.csv
Kullanim:  python scripts/soc_curve.py
"""

from __future__ import annotations

import csv
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(Path(__file__).resolve().parent))

from predict_map import build_estimator  # noqa: E402  (ROOT kurulduktan sonra)

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


def soc_from_coulombs() -> list[tuple[float, float]]:
    """(ocv_mv, soc_pct) ciftleri, ocv'ye gore artan.

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

    out = ROOT / "data" / "soc-curve.csv"
    with out.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["soc_pct", "rested_mv", "charging_mv", "loaded_mv",
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
    print(f"SoC ekseni olculen pencere: dinlenmis "
          f"{ocv_soc[0][0]:.1f} mV (%0) -> {ocv_soc[-1][0]:.1f} mV (%100)")
    print("\nSoC  dinlenmis(mV)   -- gerilim indeksiyle kiyas")
    for soc in range(0, 101, 10):
        ocv = interp(soc_ocv, float(soc))
        vi = 100.0 * (ocv - 3000.0) / 1200.0
        print(f"{soc:4d}  {ocv:10.1f}      gerilim indeksi %{vi:.1f}")


if __name__ == "__main__":
    main()
