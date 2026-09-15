"""Power-Xtra PX103049 sarj/duragan gerilim haritasi grafikleri.

data/measurements.csv dosyasini okur, su ciktilari uretir:
  graphs/voltage_overlay-light.png / -dark.png / .svg  -> iki gerilim ust uste
  data/lookup.csv                                      -> 10 mV adimli arama tablosu

Kullanim:  python scripts/plot_voltage.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "measurements.csv"
OUT = ROOT / "graphs"

# Bu deneyin gerilim olcegi (firmware'deki BatteryConfig.h ile ayni).
EMPTY_MV = 3000.0
FULL_MV = 4200.0

# Renkler: dogrulanmis kategorik paletin 1. ve 2. yuvasi (mavi / turuncu).
THEMES = {
    "light": dict(
        surface="#fcfcfb", text="#0b0b0b", muted="#52514e",
        grid="#e3e2dd", charging="#2a78d6", rested="#eb6834", band="#2a78d6",
    ),
    "dark": dict(
        surface="#1a1a19", text="#ffffff", muted="#c3c2b7",
        grid="#34332f", charging="#3987e5", rested="#d95926", band="#3987e5",
    ),
}


def load_rows() -> list[dict]:
    """Yalnizca tamamlanmis (complete=1) olcum ciftlerini dondurur."""
    rows = []
    with DATA.open(encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if raw["complete"] != "1" or not raw["rested_mv"]:
                continue
            rows.append({
                "threshold_pct": int(raw["threshold_pct"]),
                "charging_mv": float(raw["charging_mv"]),
                "rested_mv": float(raw["rested_mv"]),
                "delta_mv": float(raw["delta_mv"]),
                "total_charge_h": int(raw["total_charge_ms"]) / 3_600_000,
            })
    rows.sort(key=lambda r: r["charging_mv"])
    return rows


def voltage_pct(mv: float) -> float:
    """Dogrusal gerilim indeksi -- gercek doluluk degil."""
    return max(0.0, min(100.0, 100.0 * (mv - EMPTY_MV) / (FULL_MV - EMPTY_MV)))


def build_map(rows: list[dict]) -> list[tuple[float, float]]:
    """Sarj gerilimi artan siradaki noktalar; plato/gurultu noktalari atilir."""
    points: list[tuple[float, float]] = []
    for row in rows:
        if points and row["charging_mv"] <= points[-1][0]:
            continue  # sabit gerilim platosu: harita tek degerli kalmali
        points.append((row["charging_mv"], row["rested_mv"]))
    return points


def write_lookup(points: list[tuple[float, float]], step_mv: int = 10) -> Path:
    """Olculen araligi parca-parca dogrusal doldurur; disina tasmaz."""
    path = ROOT / "data" / "lookup.csv"
    low = math.ceil(points[0][0] / step_mv) * step_mv
    high = math.floor(points[-1][0] / step_mv) * step_mv
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow(["charging_mv", "est_rested_mv", "voltage_pct"])
        for mv in range(low, high + 1, step_mv):
            for (x0, y0), (x1, y1) in zip(points, points[1:]):
                if x0 <= mv <= x1:
                    est = y0 + (y1 - y0) * (mv - x0) / (x1 - x0)
                    writer.writerow([mv, f"{est:.1f}", f"{voltage_pct(est):.1f}"])
                    break
    return path


def render(rows: list[dict], theme_name: str, svg: bool = False) -> Path:
    t = THEMES[theme_name]
    x = [r["threshold_pct"] for r in rows]
    charging = [r["charging_mv"] / 1000 for r in rows]
    rested = [r["rested_mv"] / 1000 for r in rows]
    delta = [r["delta_mv"] for r in rows]

    fig, (ax, ax_delta) = plt.subplots(
        2, 1, figsize=(10, 7.4), sharex=True,
        gridspec_kw=dict(height_ratios=[3.1, 1], hspace=0.13),
    )
    fig.patch.set_facecolor(t["surface"])
    for axis in (ax, ax_delta):
        axis.set_facecolor(t["surface"])
        axis.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
        axis.set_axisbelow(True)
        for side in ("top", "right"):
            axis.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            axis.spines[side].set_color(t["grid"])
        axis.tick_params(colors=t["muted"], labelsize=10)

    # --- Ust panel: iki gerilim ust uste -------------------------------------
    ax.fill_between(x, rested, charging, color=t["band"], alpha=0.10,
                    linewidth=0, zorder=1)
    ax.plot(x, charging, color=t["charging"], linewidth=2, marker="o",
            markersize=8, markeredgecolor=t["surface"], markeredgewidth=2,
            label="Şarj sırasında", zorder=3)
    ax.plot(x, rested, color=t["rested"], linewidth=2, marker="o",
            markersize=8, markeredgecolor=t["surface"], markeredgewidth=2,
            label="1 dk dinlenmiş", zorder=3)

    # Seri adları doğrudan çizgi ucunda; metin mürekkep renginde kalır.
    ax.annotate("Şarj sırasında", xy=(x[-1], charging[-1]), xytext=(9, 3),
                textcoords="offset points", color=t["text"], fontsize=11,
                fontweight="bold", va="bottom", ha="left")
    ax.annotate("1 dk dinlenmiş", xy=(x[-1], rested[-1]), xytext=(9, -3),
                textcoords="offset points", color=t["text"], fontsize=11,
                fontweight="bold", va="top", ha="left")

    ax.set_title(
        "Power-Xtra PX103049 (3,7 V / 1500 mAh Li-Po) — şarj ve dinlenmiş gerilim",
        color=t["text"], fontsize=14, fontweight="bold", loc="left", pad=14,
    )
    ax.set_ylabel("Batarya gerilimi (V)", color=t["muted"], fontsize=11)
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.set_ylim(3.20, 4.26)
    ax.set_xlim(32, 104)
    legend = ax.legend(loc="lower right", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])

    # Şarj IC'sinin sabit gerilim tavanı: üst ucun neden belirsizleştiği.
    ax.axhline(4.2, color=t["muted"], linewidth=1, linestyle=(0, (4, 4)), zorder=2)
    ax.annotate("4,20 V şarj tavanı — %100 eşiğine hiç ulaşılamadı",
                xy=(33.5, 4.2), xytext=(0, -6), textcoords="offset points",
                color=t["muted"], fontsize=9.5, va="top", ha="left")

    # --- Alt panel: aradaki fark ---------------------------------------------
    ax_delta.plot(x, delta, color=t["charging"], linewidth=2, marker="o",
                  markersize=7, markeredgecolor=t["surface"], markeredgewidth=2,
                  zorder=3)
    ax_delta.set_ylabel("Fark (mV)", color=t["muted"], fontsize=11)
    ax_delta.set_xlabel("Gerilim ölçeği eşiği (%) — gerçek doluluk değil",
                        color=t["muted"], fontsize=11)
    ax_delta.xaxis.set_major_locator(MultipleLocator(5))
    ax_delta.set_ylim(0, 200)

    # Sabit akım / sabit gerilim geçişi farkın çöküşüyle görülür.
    ax_delta.annotate("sabit akım: ~140 mV", xy=(57, 172),
                      color=t["text"], fontsize=10, ha="center", va="center")
    ax_delta.annotate("sabit gerilim: fark kapanıyor", xy=(96, 32),
                      color=t["text"], fontsize=10, ha="right", va="center")

    fig.text(0.008, 0.012,
             "13 ölçüm çifti — ESP32 + TPS22919, GPIO34 üzerinden 10k/10k bölücü. "
             "Dinlenme 60 s; ADC kalibre edilmedi.",
             color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.845, top=0.925, bottom=0.105)

    OUT.mkdir(exist_ok=True)
    name = "voltage_overlay.svg" if svg else f"voltage_overlay-{theme_name}.png"
    path = OUT / name
    fig.savefig(path, dpi=None if svg else 200, facecolor=t["surface"])
    plt.close(fig)
    return path


def main() -> None:
    rows = load_rows()
    if not rows:
        raise SystemExit("data/measurements.csv icinde tamamlanmis olcum yok.")
    written = [
        render(rows, "light"),
        render(rows, "dark"),
        render(rows, "light", svg=True),
        write_lookup(build_map(rows)),
    ]
    for path in written:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
