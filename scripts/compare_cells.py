"""Uc hucrenin sapmalarini ust uste koyan karsilastirma grafikleri.

Her hucrenin olcum CSV'leri kendi branch'inden birebir kopyalanip
data/<hucre>/ altina kondu; bu script yalnizca onlari okur.

Girdiler (her hucre icin):
  data/<hucre>/measurements-charge.csv     -> sarj yonundeki ciftler
  data/<hucre>/measurements-discharge.csv  -> yuk yonundeki ciftler

Ciktilar:
  graphs/fark_karsilastirma-light.png / -dark.png / .svg
      ust: sarjdaki gerilim - dinlenmis, alt: yuk altindaki - toparlanmis (mV)
  graphs/direnc_karsilastirma-light.png / -dark.png / .svg
      yuk yonundeki sapma / yuk akimi = gorunur direnc (mOhm)

Yatay eksen her grafikte dinlenmis (acik devre) gerilimdir: hucrelerin
yuzde olcekleri farkli (3,0-4,2 V ve 2,8-4,2 V), gerilim ise ortak.

Kullanim:  python scripts/compare_cells.py
"""

from __future__ import annotations

import csv
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
OUT = ROOT / "graphs"

# SVG'ler de yeniden uretildiginde birebir ayni ciksin: tarih yok, sabit id'ler.
plt.rcParams["svg.hashsalt"] = "karsilastirma"

# ===========================================================================
# HUCRELER
#
# Sira sabittir ve renk yuvasini belirler: ilk olculen hucre 1. yuva. Bir
# hucre eklenirse sona eklenir, oncekilerin rengi degismez.
#
# load_ohms: yuk yonundeki akim I = loaded_mv / load_ohms. PX103049'un
# kosusunda direnc kaydedilmedi; 26,8 ohm sonradan CIKARILDI (px103049
# branch'inin README'si), bu yuzden o hucre direnc grafiginde kesik cizgiyle
# ve "akim cikarim" notuyla ayrilir.
# ===========================================================================
CELLS = [
    dict(key="px103049", name="PX103049", desc="1500 mAh Li-Po",
         load_ohms=26.8, load_inferred=True),
    dict(key="px803035", name="PX803035", desc="800 mAh Li-Po",
         load_ohms=12.2, load_inferred=False),
    dict(key="inr18650mj1", name="MJ1", desc="3400 mAh Li-ion",
         load_ohms=12.2, load_inferred=False),
]

# Renkler: dogrulanmis kategorik paletin 1./2./3. yuvasi (mavi / turuncu /
# aqua), hucre basina birer kimlik. Bu uclu her iki modda all-pairs esiklerini
# gecer (CVD dE 9.2 light, 9.4 dark; normal gorus 24.0 / 20.9). Aqua light
# yuzeyde 3:1 kontrastin altinda kaldigi icin seriler dogrudan etiketlenir ve
# README'de ayni sayilarin tablosu var.
THEMES = {
    "light": dict(surface="#fcfcfb", text="#0b0b0b", muted="#52514e", grid="#e3e2dd",
                  zero="#8a8984", series=("#2a78d6", "#eb6834", "#1baf7a")),
    "dark": dict(surface="#1a1a19", text="#ffffff", muted="#c3c2b7", grid="#34332f",
                 zero="#8a8984", series=("#3987e5", "#d95926", "#199e70")),
}

XLIM = (2.85, 4.20)
FOOTNOTE_CURRENTS = (
    "Akımlar farklı: şarj akımı hiçbir koşuda ölçülmedi. Yük: PX103049 ≈0,11–0,14 A "
    "(26,8 Ω, sonradan çıkarıldı), PX803035 ve MJ1 12,2 Ω (0,23–0,32 A)."
)
FOOTNOTE_COMMON = "Her çift 60 s dinlenmeden sonra; ADC kalibre edilmedi."


def load(cell: dict, direction: str) -> list[dict]:
    """Bir hucrenin bir yondeki tamamlanmis ciftleri, dinlenmis gerilime gore artan."""
    measured, settled = (("charging_mv", "rested_mv") if direction == "charge"
                         else ("loaded_mv", "recovered_mv"))
    path = DATA / cell["key"] / f"measurements-{direction}.csv"
    rows = []
    with path.open(encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if raw["complete"] != "1" or not raw[settled]:
                continue
            rows.append({
                "measured_mv": float(raw[measured]),
                "rested_mv": float(raw[settled]),
                "delta_mv": float(raw["delta_mv"]),
            })
    rows.sort(key=lambda r: r["rested_mv"])
    return rows


def style(fig, axes, t) -> None:
    fig.patch.set_facecolor(t["surface"])
    for axis in axes:
        axis.set_facecolor(t["surface"])
        axis.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
        axis.set_axisbelow(True)
        for side in ("top", "right"):
            axis.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            axis.spines[side].set_color(t["grid"])
        axis.tick_params(colors=t["muted"], labelsize=10)


def plot_series(ax, x, y, color, t, label, dashed=False) -> None:
    # Kesik seri (cikarim) ici bos noktalarla da ayrilir: kenar seri renginde.
    ax.plot(x, y, color=color, linewidth=2, linestyle=(0, (5, 3)) if dashed else "-",
            marker="o", markersize=8, markeredgewidth=2,
            markeredgecolor=color if dashed else t["surface"],
            markerfacecolor=t["surface"] if dashed else color, label=label, zorder=3)


def label_column(ax, ends, t, min_gap_pt: float = 16) -> None:
    """Seri adlarini cizimin sagindaki tek bir sutuna koyar, ince bir cizgiyle
    her serinin son noktasina baglar; ust uste binenleri dikeyde iter.

    Uclar yakin dustugunde (iki hucre ~3,9-4,0 V'ta bitiyor) adlar cizgilerin
    ustune binmesin diye uca degil sutuna yazilir. Konumlar eksen kesri
    cinsinden, boylece PNG (200 dpi) ve SVG ayni yerlesimi alir.

    ends: (metin, x, y) -- veri koordinatinda. Limitler bu cagridan ONCE
    ayarlanmis olmali.
    """
    to_axes = ax.transAxes.inverted()
    # Aralik puntoyla verilir, eksen kesrine burada cevrilir: kisa panelde de
    # iki ad arasinda ayni bosluk kalsin.
    height_pt = ax.get_window_extent().height * 72 / ax.figure.dpi
    min_gap = min_gap_pt / height_pt
    placed = sorted(
        ([to_axes.transform(ax.transData.transform((x, y)))[1], text, x, y]
         for text, x, y in ends),
        key=lambda p: p[0])
    for i in range(1, len(placed)):
        placed[i][0] = max(placed[i][0], placed[i - 1][0] + min_gap)
    for y_axes, text, x, y in placed:
        ax.annotate(text, xy=(x, y), xytext=(1.015, y_axes), textcoords="axes fraction",
                    color=t["text"], fontsize=10.5, fontweight="bold",
                    va="center", ha="left", annotation_clip=False,
                    arrowprops=dict(arrowstyle="-", color=t["muted"], linewidth=0.8,
                                    alpha=0.7, shrinkA=3, shrinkB=6))


def save(fig, stem: str, theme_name: str, svg: bool) -> Path:
    OUT.mkdir(exist_ok=True)
    path = OUT / (f"{stem}.svg" if svg else f"{stem}-{theme_name}.png")
    fig.savefig(path, dpi=None if svg else 200, facecolor=fig.get_facecolor(),
                metadata={"Date": None} if svg else None)
    plt.close(fig)
    return path


def render_deltas(data: dict, theme_name: str, svg: bool = False) -> Path:
    t = THEMES[theme_name]
    fig, (ax_ch, ax_ld) = plt.subplots(
        2, 1, figsize=(10, 7.4), sharex=True,
        gridspec_kw=dict(height_ratios=[1.25, 1], hspace=0.16),
    )
    style(fig, (ax_ch, ax_ld), t)

    for i, cell in enumerate(CELLS):
        color = t["series"][i]
        label = f"{cell['name']} ({cell['desc']})"
        for ax, direction in ((ax_ch, "charge"), (ax_ld, "discharge")):
            rows = data[cell["key"]][direction]
            plot_series(ax, [r["rested_mv"] / 1000 for r in rows],
                        [r["delta_mv"] for r in rows], color, t,
                        label if ax is ax_ch else None)

    ax_ld.axhline(0, color=t["zero"], linewidth=1, alpha=0.6, zorder=2)
    ax_ch.set_ylim(0, 270)
    ax_ld.set_ylim(-120, 0)
    ax_ch.yaxis.set_major_locator(MultipleLocator(50))
    ax_ld.yaxis.set_major_locator(MultipleLocator(20))
    ax_ld.xaxis.set_major_locator(MultipleLocator(0.1))
    ax_ld.set_xlim(*XLIM)

    ax_ch.set_ylabel("Şarjda − dinlenmiş (mV)", color=t["muted"], fontsize=11)
    ax_ld.set_ylabel("Yük altında − toparlanmış (mV)", color=t["muted"], fontsize=11)
    ax_ld.set_xlabel("Dinlenmiş (açık devre) gerilim (V) — hücrenin gerçek durumu",
                     color=t["muted"], fontsize=11)
    ax_ch.set_title("Üç hücre — şarjda ve yük altında, dinlenmiş gerilimden sapma",
                    color=t["text"], fontsize=14, fontweight="bold", loc="left", pad=14)
    legend = ax_ch.legend(loc="upper left", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])

    fig.text(0.008, 0.040, FOOTNOTE_CURRENTS, color=t["muted"], fontsize=9)
    fig.text(0.008, 0.012, FOOTNOTE_COMMON, color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.855, top=0.925, bottom=0.13)

    for ax, direction in ((ax_ch, "charge"), (ax_ld, "discharge")):
        label_column(ax, [(cell["name"],
                           data[cell["key"]][direction][-1]["rested_mv"] / 1000,
                           data[cell["key"]][direction][-1]["delta_mv"])
                          for cell in CELLS], t)
    return save(fig, "fark_karsilastirma", theme_name, svg)


def resistance_rows(cell: dict, rows: list[dict]) -> list[tuple[float, float]]:
    """(dinlenmis V, gorunur direnc mOhm): |sapma| / (loaded_mv / load_ohms)."""
    return [(r["rested_mv"] / 1000,
             abs(r["delta_mv"]) / (r["measured_mv"] / cell["load_ohms"]) * 1000)
            for r in rows]


def render_resistance(data: dict, theme_name: str, svg: bool = False) -> Path:
    t = THEMES[theme_name]
    fig, ax = plt.subplots(figsize=(10, 6.2))
    style(fig, (ax,), t)

    ends = []
    for i, cell in enumerate(CELLS):
        points = resistance_rows(cell, data[cell["key"]]["discharge"])
        suffix = " — akım çıkarım" if cell["load_inferred"] else ""
        plot_series(ax, [p[0] for p in points], [p[1] for p in points], t["series"][i], t,
                    f"{cell['name']} ({cell['desc']}){suffix}", dashed=cell["load_inferred"])
        ends.append((cell["name"] + ("*" if cell["load_inferred"] else ""), *points[-1]))

    ax.set_xlim(*XLIM)
    ax.set_ylim(0, 800)
    ax.xaxis.set_major_locator(MultipleLocator(0.1))
    ax.yaxis.set_major_locator(MultipleLocator(100))
    ax.set_ylabel("Görünür direnç (mΩ)", color=t["muted"], fontsize=11)
    ax.set_xlabel("Dinlenmiş (açık devre) gerilim (V)", color=t["muted"], fontsize=11)
    ax.set_title("Üç hücre — yük yönünde görünür direnç: 60 s toparlanma ÷ yük akımı",
                 color=t["text"], fontsize=14, fontweight="bold", loc="left", pad=14)
    legend = ax.legend(loc="upper right", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])

    fig.text(0.008, 0.070,
             "Hücre + koruma devresi + kablo + anahtar birlikte; saf iç direnç değil. "
             "I = yük altındaki gerilim / yük direnci.",
             color=t["muted"], fontsize=9)
    fig.text(0.008, 0.042,
             "* PX103049'un yük direnci kaydedilmedi; 26,8 Ω sonradan çıkarıldı, bu "
             "yüzden eğrisi kesik ve ölçeği belirsiz.",
             color=t["muted"], fontsize=9)
    fig.text(0.008, 0.014, FOOTNOTE_COMMON, color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.855, top=0.91, bottom=0.19)
    label_column(ax, ends, t)
    return save(fig, "direnc_karsilastirma", theme_name, svg)


def main() -> None:
    data = {cell["key"]: {d: load(cell, d) for d in ("charge", "discharge")}
            for cell in CELLS}
    for cell in CELLS:
        for direction, rows in data[cell["key"]].items():
            if not rows:
                raise SystemExit(f"data/{cell['key']}/measurements-{direction}.csv "
                                 "icinde tamamlanmis cift yok.")

    written = []
    for render in (render_deltas, render_resistance):
        written += [render(data, "light"), render(data, "dark"),
                    render(data, "light", svg=True)]

    print("Hucreler: " + ", ".join(
        f"{c['name']} ({len(data[c['key']]['charge'])} sarj + "
        f"{len(data[c['key']]['discharge'])} yuk cifti)" for c in CELLS))
    print("Yazilan:")
    for path in written:
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
