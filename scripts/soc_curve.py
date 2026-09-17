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
Kullanim:  python scripts/soc_curve.py   (once predict_map.py calismis olmali)
"""

from __future__ import annotations

import csv
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent

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


def load_combined() -> list[dict]:
    path = ROOT / "data" / "lookup-combined.csv"
    if not path.exists():
        raise SystemExit("data/lookup-combined.csv yok -> once scripts/predict_map.py")
    with path.open(encoding="utf-8") as h:
        return list(csv.DictReader(h))


def main() -> None:
    ocv_soc = soc_from_coulombs()
    soc_ocv = sorted((soc, ocv) for ocv, soc in ocv_soc)
    combined = load_combined()

    # OCV -> sarjda / yukte degerleri birlesik tablodan tasinir.
    charging_pairs = sorted((float(r["rested_mv"]), float(r["charging_mv"]))
                            for r in combined)
    loaded_pairs = sorted((float(r["rested_mv"]), float(r["loaded_mv"]))
                          for r in combined)

    # Kaynak etiketi kosularin KENDI olculen araliklarindan hesaplanir.
    # Birlesik tablonun %1'lik izgarasindan odunc alinirsa sinirda bir
    # adim kayiyor (or. SoC %0'da yuk olcum oldugu halde extrapolated
    # gorunuyordu).
    ch_range = (3260.81, 4089.25)   # sarj kosusunun dinlenmis araligi
    ld_range = (3074.19, 3883.00)   # desarj kosusunun dinlenmis araligi
    CC_MAX_OCV = 3835.0             # kopru yalnizca sabit akim bolgesinde
    TOL = 0.05                      # yuvarlama toleransi

    def source(ocv: float, own: tuple[float, float],
               other: tuple[float, float], can_bridge: bool) -> str:
        if own[0] - TOL <= ocv <= own[1] + TOL:
            return "measured"
        if can_bridge and other[0] - TOL <= ocv <= other[1] + TOL \
                and ocv <= CC_MAX_OCV:
            return "bridged"
        return "extrapolated"

    out = ROOT / "data" / "soc-curve.csv"
    with out.open("w", encoding="utf-8", newline="") as h:
        w = csv.writer(h)
        w.writerow(["soc_pct", "rested_mv", "charging_mv", "loaded_mv",
                    "charging_src", "loaded_src"])
        for step in range(101):
            soc = float(step)
            ocv = interp(soc_ocv, soc)
            if ocv is None:
                continue
            ch = interp(charging_pairs, ocv)
            ld = interp(loaded_pairs, ocv)
            w.writerow([
                f"{soc:.0f}", f"{ocv:.1f}",
                "" if ch is None else f"{ch:.1f}",
                "" if ld is None else f"{ld:.1f}",
                source(ocv, ch_range, ld_range, can_bridge=True),
                source(ocv, ld_range, ch_range, can_bridge=False),
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
