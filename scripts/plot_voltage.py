"""Power-Xtra PX103049 sarj / dinlenmis / yuk altinda gerilim haritasi grafikleri.

Girdiler:
  data/measurements.csv            -> sarj kosusu (13 cift, sarj yonu)
  data/measurements-discharge.csv  -> desarj kosusu (15 cift, yuk yonu)

Ayrica (varsa) predict_map.py ve window_curve.py ciktilarini kullanir:
  data/lookup-combined.csv   -> tam aralik grafigi
  data/window-curve.csv      -> kapasite pencresi grafigi

Ciktilar:
  graphs/voltage_overlay-light.png / -dark.png / .svg -> sarj + dinlenmis
  graphs/state_overlay-light.png / -dark.png / .svg   -> uc durum ust uste
  graphs/full_range-light.png / -dark.png / .svg      -> gerilim indeksi, %0-100
  graphs/window_curve-light.png / -dark.png / .svg    -> kapasite ekseni
  data/lookup.csv                                     -> sarjdaki gerilim -> dinlenmis
  data/lookup-discharge.csv                           -> yuk altindaki gerilim -> dinlenmis

Kullanim:  python scripts/plot_voltage.py
"""

from __future__ import annotations

import csv
import math
from pathlib import Path

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.lines import Line2D
from matplotlib.ticker import MultipleLocator

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data" / "measurements.csv"
DATA_DISCHARGE = ROOT / "data" / "measurements-discharge.csv"
OUT = ROOT / "graphs"

# Bu deneyin gerilim olcegi (firmware'deki BatteryConfig.h ile ayni).
EMPTY_MV = 3000.0
FULL_MV = 4200.0

# Renkler: dogrulanmis kategorik paletin 1./2./3. yuvasi (mavi / turuncu / aqua).
# Ucu birlikte her iki modda all-pairs esiklerini gecer (CVD dE 9.2 light,
# 9.4 dark; normal gorus 24.0 / 20.9). Aqua light yuzeyde 3:1 kontrastin
# altinda kaldigi icin seriler dogrudan etiketlenir + README'de tablo var.
THEMES = {
    "light": dict(
        surface="#fcfcfb", text="#0b0b0b", muted="#52514e",
        grid="#e3e2dd", charging="#2a78d6", rested="#eb6834", band="#2a78d6",
        load="#1baf7a",
    ),
    "dark": dict(
        surface="#1a1a19", text="#ffffff", muted="#c3c2b7",
        grid="#34332f", charging="#3987e5", rested="#d95926", band="#3987e5",
        load="#199e70",
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


def load_discharge_rows() -> list[dict]:
    """Desarj kosusunun tamamlanmis ciftleri, dinlenmis gerilime gore artan.

    Kolon adlari sarj kosusundan farkli: firmware yuk yonunde olcerken
    `loaded_mv` (yuk bagliyken) ve `recovered_mv` (60 s sonra) yaziyor.
    delta_mv bu kosuda negatif -- yuk altindaki gerilim dinlenmisin altinda.
    """
    rows = []
    with DATA_DISCHARGE.open(encoding="utf-8") as handle:
        for raw in csv.DictReader(handle):
            if raw["complete"] != "1" or not raw["recovered_mv"]:
                continue
            rows.append({
                "threshold_pct": int(raw["threshold_pct"]),
                "loaded_mv": float(raw["loaded_mv"]),
                "rested_mv": float(raw["recovered_mv"]),
                "delta_mv": float(raw["delta_mv"]),
                "total_load_h": int(raw["total_load_ms"]) / 3_600_000,
            })
    rows.sort(key=lambda r: r["rested_mv"])
    return rows


def voltage_pct(mv: float) -> float:
    """Dogrusal gerilim indeksi -- gercek doluluk degil."""
    return max(0.0, min(100.0, 100.0 * (mv - EMPTY_MV) / (FULL_MV - EMPTY_MV)))


def build_map(rows: list[dict], measured_key: str = "charging_mv") -> list[tuple[float, float]]:
    """Olculen gerilim artan siradaki noktalar; plato/gurultu noktalari atilir."""
    points: list[tuple[float, float]] = []
    for row in rows:
        if points and row[measured_key] <= points[-1][0]:
            continue  # sabit gerilim platosu: harita tek degerli kalmali
        points.append((row[measured_key], row["rested_mv"]))
    return points


def write_lookup(
    points: list[tuple[float, float]],
    step_mv: int = 10,
    name: str = "lookup.csv",
    first_col: str = "charging_mv",
) -> Path:
    """Olculen araligi parca-parca dogrusal doldurur; disina tasmaz."""
    path = ROOT / "data" / name
    low = math.ceil(points[0][0] / step_mv) * step_mv
    high = math.floor(points[-1][0] / step_mv) * step_mv
    with path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.writer(handle)
        writer.writerow([first_col, "est_rested_mv", "voltage_pct"])
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


def render_states(
    charge: list[dict], discharge: list[dict], theme_name: str, svg: bool = False
) -> Path:
    """Uc durumu ortak bir eksende ust uste koyar.

    Ortak eksen dinlenmis (acik devre) gerilimdir -- bataryanin gercek durumu.
    Terminal gerilimi esik olarak kullanilamaz: her kosuda anahtarlama zaten o
    gerilimde tetiklendigi icin `charging_mv` ile `loaded_mv` esik cizgisinin
    kendisine oturur ve iki egri yapay olarak cakisir. Dinlenmis gerilime
    gore cizilince sarj egrisi referansin uzerinde, yuk egrisi altinda kalir.
    """
    t = THEMES[theme_name]

    ch_x = [r["rested_mv"] / 1000 for r in charge]
    ch_y = [r["charging_mv"] / 1000 for r in charge]
    ld_x = [r["rested_mv"] / 1000 for r in discharge]
    ld_y = [r["loaded_mv"] / 1000 for r in discharge]

    # Referans kosegen: iki kosunun dinlenmis gerilimlerinin birlesimi.
    ref_x = sorted(ch_x + ld_x)

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

    # --- Ust panel: uc durum ------------------------------------------------
    # Taralı bantlar farkin kendisi: referansin ustu sarj, alti yuk.
    ax.fill_between(ch_x, ch_x, ch_y, color=t["charging"], alpha=0.10,
                    linewidth=0, zorder=1)
    ax.fill_between(ld_x, ld_y, ld_x, color=t["load"], alpha=0.10,
                    linewidth=0, zorder=1)

    # Referans: bu eksende x zaten dinlenmis gerilim, yani bu cizgi tanim
    # geregi y=x. Olculmus bir egri DEGIL -> ince, soluk, legend'e girmez.
    ax.plot(ref_x, ref_x, color=t["rested"], linewidth=1, alpha=0.55, zorder=2)
    ax.plot(ch_x, ch_y, color=t["charging"], linewidth=2, marker="o",
            markersize=8, markeredgecolor=t["surface"], markeredgewidth=2,
            label="Şarj olurken (0,5C)", zorder=4)
    ax.plot(ld_x, ld_y, color=t["load"], linewidth=2, marker="o",
            markersize=8, markeredgecolor=t["surface"], markeredgewidth=2,
            label="Yük altında deşarj olurken", zorder=4)

    # Olculen serilerin adlari dogrudan cizgi ucunda, murekkep renginde.
    for label, x, y, dy, va in (
        ("Şarj olurken", ch_x[-1], ch_y[-1], 3, "bottom"),
        ("Yük altında", ld_x[-1], ld_y[-1], 0, "center"),
    ):
        ax.annotate(label, xy=(x, y), xytext=(9, dy), textcoords="offset points",
                    color=t["text"], fontsize=11, fontweight="bold",
                    va=va, ha="left")
    # Referans cizgisi ayri tutulur: soluk ve kalin degil, cunku veri degil.
    ax.annotate("dinlenmiş = eksen\n(veri değil)", xy=(ref_x[-1], ref_x[-1]),
                xytext=(9, -9), textcoords="offset points", color=t["muted"],
                fontsize=9.5, va="top", ha="left")

    ax.set_title(
        "Power-Xtra PX103049 — aynı hücre, üç durum: şarjda, dinlenmiş, yük altında",
        color=t["text"], fontsize=14, fontweight="bold", loc="left", pad=14,
    )
    ax.set_ylabel("Terminal gerilimi (V)", color=t["muted"], fontsize=11)
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.set_ylim(2.95, 4.20)
    ax.set_xlim(3.03, 4.13)
    legend = ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])

    # --- Alt panel: referanstan sapma ---------------------------------------
    ax_delta.axhline(0, color=t["rested"], linewidth=1, alpha=0.55, zorder=2)
    ax_delta.plot(ch_x, [r["delta_mv"] for r in charge], color=t["charging"],
                  linewidth=2, marker="o", markersize=7,
                  markeredgecolor=t["surface"], markeredgewidth=2, zorder=4)
    ax_delta.plot(ld_x, [r["delta_mv"] for r in discharge], color=t["load"],
                  linewidth=2, marker="o", markersize=7,
                  markeredgecolor=t["surface"], markeredgewidth=2, zorder=4)
    ax_delta.set_ylabel("Dinlenmişten sapma (mV)", color=t["muted"], fontsize=11)
    ax_delta.set_xlabel(
        "Dinlenmiş (açık devre) gerilim (V) — bataryanın gerçek durumu",
        color=t["muted"], fontsize=11,
    )
    ax_delta.xaxis.set_major_locator(MultipleLocator(0.1))
    ax_delta.yaxis.set_major_locator(MultipleLocator(50))
    ax_delta.set_ylim(-130, 210)

    # Aciklamalar egrilerin bos tarafinda: sarj serisinin ustu, yukun alti.
    ch_d = [r["delta_mv"] for r in charge]
    ld_d = [r["delta_mv"] for r in discharge]
    ax_delta.annotate(f"şarj yönü: +{min(ch_d):.0f} … +{max(ch_d):.0f} mV",
                      xy=(3.42, 190), color=t["text"], fontsize=10,
                      ha="left", va="center")
    ax_delta.annotate(f"yük yönü: −{abs(max(ld_d)):.0f} … −{abs(min(ld_d)):.0f} mV",
                      xy=(3.42, -110), color=t["text"], fontsize=10,
                      ha="left", va="center")

    fig.text(0.008, 0.012,
             "Şarj: 13 çift, ~0,5C (koşu 1). Yük: 15 çift, sabit dummy load. "
             "Her iki yönde de 60 s dinlenme; ADC kalibre edilmedi.",
             color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.845, top=0.925, bottom=0.105)

    OUT.mkdir(exist_ok=True)
    name = "state_overlay.svg" if svg else f"state_overlay-{theme_name}.png"
    path = OUT / name
    fig.savefig(path, dpi=None if svg else 200, facecolor=t["surface"])
    plt.close(fig)
    return path


def load_combined() -> list[dict]:
    """predict_map.py'nin urettigi birlesik tabloyu okur (olcum + tahmin)."""
    path = ROOT / "data" / "lookup-combined.csv"
    with path.open(encoding="utf-8") as handle:
        return [{
            "pct": float(r["voltage_pct"]),
            "rested": float(r["rested_mv"]) / 1000,
            # Alt ucta hucreler bos olabilir: veri yok, tahmin uretilmiyor.
            "charging": float(r["charging_mv"]) / 1000 if r["charging_mv"] else None,
            "loaded": float(r["loaded_mv"]) / 1000 if r["loaded_mv"] else None,
            "charging_src": r["charging_src"],
            "loaded_src": r["loaded_src"],
            "observed": r["rested_observed"] == "yes",
        } for r in csv.DictReader(handle)]


def runs_by_source(rows: list[dict], value_key: str, src_key: str,
                   x_key: str = "pct"):
    """(noktalar, olculdu_mu) parcalari; sinir noktasi iki parcada da yer alir
    ki duz ve kesikli bolumler arasinda bosluk kalmasin."""
    segments: list[tuple[list[tuple[float, float]], bool]] = []
    for row in rows:
        measured = row[src_key] == "measured"
        point = (row[x_key], row[value_key])
        if segments and segments[-1][1] == measured:
            segments[-1][0].append(point)
        else:
            if segments:
                segments[-1][0].append(point)  # sinirda kopma olmasin
            segments.append(([point], measured))
    return segments


def render_full_range(rows: list[dict], charge: list[dict], discharge: list[dict],
                      theme_name: str, svg: bool = False) -> Path:
    """Uc durum, gerilim indeksi ekseninde. Olculen noktalar esas alinir.

    Duz cizgiler yalnizca OLCULEN ciftleri birlestirir (isaretciler o
    noktalarda). Kesikli kisim yalnizca son olculen noktanin OTESI, yani
    tahmin edilen devam. Olculen degerler hicbir izgaraya yeniden
    orneklenmez -- oldugu gibi cizilir.

    Dinlenmis referans cizgisi veri serisi DEGIL: bu eksende x zaten
    dinlenmis gerilimin indeksi, yani o cizgi tanim geregi duz kosegen.
    O yuzden ince/soluk cizilir ve legend'e girmez.
    """
    t = THEMES[theme_name]
    pcts = [r["pct"] for r in rows]

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

    # Hucrenin dinlenmis halde hic gozlenmedigi uclar: her iki panelde isaretli.
    unobserved = [r["pct"] for r in rows if not r["observed"]]
    if unobserved:
        low = [p for p in unobserved if p < 50]
        high = [p for p in unobserved if p >= 50]
        for axis in (ax, ax_delta):
            if low:
                axis.axvspan(min(pcts), max(low), color=t["muted"],
                             alpha=0.07, linewidth=0, zorder=0)
            if high:
                axis.axvspan(min(high), max(pcts), color=t["muted"],
                             alpha=0.07, linewidth=0, zorder=0)

    # Dinlenmis referans: veri degil, eksenin kendisi -> ince, soluk, legend yok.
    have = [r for r in rows
            if r["charging"] is not None or r["loaded"] is not None]
    ax.plot([r["pct"] for r in have], [r["rested"] for r in have],
            color=t["rested"], linewidth=1, alpha=0.55, zorder=2)

    # Olculen ciftler: hicbir izgaraya orneklenmeden, oldugu gibi.
    measured_series = (
        ("charging_mv", charge, t["charging"], "Şarj olurken (~0,5C)"),
        ("loaded_mv", discharge, t["load"], "Yük altında deşarj (~0,16C)"),
    )
    ends: dict[str, tuple[tuple[float, float], tuple[float, float]]] = {}
    for value_col, runs, color, label in measured_series:
        xs = [voltage_pct(r["rested_mv"]) for r in runs]
        ys = [r[value_col] / 1000 for r in runs]
        ax.plot(xs, ys, color=color, linewidth=2, marker="o", markersize=7,
                markeredgecolor=t["surface"], markeredgewidth=2,
                label=label, zorder=5)
        ends[value_col] = ((xs[0], ys[0]), (xs[-1], ys[-1]))

    # Tahmin yalnizca olculen araligin DISINA cizilir ve komsu olculen
    # noktaya baglanir. Olculen araligin *icinde* hicbir sey yeniden
    # hesaplanmaz -- orada cizgi dogrudan olculen ciftleri birlestirir.
    for value_col, value_key, src_key, color in (
        ("charging_mv", "charging", "charging_src", t["charging"]),
        ("loaded_mv", "loaded", "loaded_src", t["load"]),
    ):
        first, last = ends[value_col]
        predicted = [(r["pct"], r[value_key]) for r in rows
                     if r[value_key] is not None and r[src_key] != "measured"]
        below = [p for p in predicted if p[0] < first[0]]
        above = [p for p in predicted if p[0] > last[0]]
        if below:
            ax.plot([p[0] for p in below] + [first[0]],
                    [p[1] for p in below] + [first[1]],
                    color=color, linewidth=2, linestyle=(0, (5, 3)), zorder=3)
        if above:
            ax.plot([last[0]] + [p[0] for p in above],
                    [last[1]] + [p[1] for p in above],
                    color=color, linewidth=2, linestyle=(0, (5, 3)), zorder=3)

    ax.set_title(
        "Power-Xtra PX103049 — üç durum (nokta = ölçüm, kesikli = tahmin)",
        color=t["text"], fontsize=14, fontweight="bold", loc="left", pad=14,
    )
    ax.set_ylabel("Terminal gerilimi (V)", color=t["muted"], fontsize=11)
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.set_ylim(2.95, 4.26)
    ax.set_xlim(0, 100)

    legend = ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])
    ax.add_artist(legend)
    style_key = ax.legend(handles=[
        Line2D([], [], color=t["muted"], linewidth=2, marker="o", markersize=7,
               markeredgecolor=t["surface"], markeredgewidth=2,
               label="ölçülen çift"),
        Line2D([], [], color=t["muted"], linewidth=2, linestyle=(0, (5, 3)),
               label="tahmin — yalnızca ölçüm aralığı dışı"),
        Line2D([], [], color=t["rested"], linewidth=1, alpha=0.55,
               label="dinlenmiş = eksenin kendisi, veri değil"),
    ], loc="lower right", frameon=False, fontsize=10)
    for text in style_key.get_texts():
        text.set_color(t["text"])

    # Gri bant dogrudan etiketlenir; ayri bir aciklama satiri gerekmez.
    ax.annotate("veri yok", xy=(3.1, 3.62), color=t["muted"], fontsize=9.5,
                rotation=90, ha="center", va="center")

    # --- Alt panel: referanstan sapma ---------------------------------------
    # Sifir cizgisi de veri degil, referansin kendisi -> ince ve soluk.
    ax_delta.axhline(0, color=t["rested"], linewidth=1, alpha=0.55, zorder=2)
    for value_col, runs, color in (("charging_mv", charge, t["charging"]),
                                   ("loaded_mv", discharge, t["load"])):
        # Olculen sapma: dogrudan delta_mv sutunu (isareti yonden gelir).
        xs = [voltage_pct(r["rested_mv"]) for r in runs]
        ys = [r[value_col] - r["rested_mv"] for r in runs]
        ax_delta.plot(xs, ys, color=color, linewidth=2, marker="o",
                      markersize=6, markeredgecolor=t["surface"],
                      markeredgewidth=1.8, zorder=5)
        first, last = (xs[0], ys[0]), (xs[-1], ys[-1])
        key = "charging" if value_col == "charging_mv" else "loaded"
        src_key = f"{key}_src"
        predicted = [(r["pct"], (r[key] - r["rested"]) * 1000) for r in rows
                     if r[key] is not None and r[src_key] != "measured"]
        for side, anchor in ((("below"), first), (("above"), last)):
            seg = [p for p in predicted
                   if (p[0] < anchor[0] if side == "below" else p[0] > anchor[0])]
            if not seg:
                continue
            pts = seg + [anchor] if side == "below" else [anchor] + seg
            ax_delta.plot([p[0] for p in pts], [p[1] for p in pts],
                          color=color, linewidth=2, linestyle=(0, (5, 3)),
                          zorder=3)
    ax_delta.set_ylabel("Dinlenmişten sapma (mV)", color=t["muted"], fontsize=11)
    ax_delta.set_xlabel("Gerilim ölçeği — dinlenmiş gerilimin indeksi (%) "
                        "— gerçek doluluk değil",
                        color=t["muted"], fontsize=11)
    ax_delta.xaxis.set_major_locator(MultipleLocator(10))
    ax_delta.yaxis.set_major_locator(MultipleLocator(50))
    ax_delta.set_ylim(-130, 230)

    fig.text(0.008, 0.012,
             "Ölçüm: şarj 13 çift + yük 15 çift. Tahmin yöntemi ve belirsizliği "
             "README'de; hücre başına sayılar data/lookup-combined.csv'de.",
             color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.975, top=0.925, bottom=0.105)

    OUT.mkdir(exist_ok=True)
    name = "full_range.svg" if svg else f"full_range-{theme_name}.png"
    path = OUT / name
    fig.savefig(path, dpi=None if svg else 200, facecolor=t["surface"])
    plt.close(fig)
    return path


def load_window_curve() -> list[dict]:
    """window_curve.py'nin urettigi kapasite pencresi tablosunu okur."""
    path = ROOT / "data" / "window-curve.csv"
    with path.open(encoding="utf-8") as handle:
        return [{
            "window": float(r["window_pct"]),
            "rested": float(r["rested_mv"]) / 1000,
            "charging": float(r["charging_mv"]) / 1000,
            "loaded": float(r["loaded_mv"]) / 1000,
            "charging_src": r["charging_src"],
            "loaded_src": r["loaded_src"],
        } for r in csv.DictReader(handle)]


def render_window_curve(rows: list[dict], charge: list[dict],
                        discharge: list[dict], theme_name: str,
                        svg: bool = False) -> Path:
    """Uc durum, kapasite ekseninde -- batarya egrisinin kendi sekli.

    Gerilim indeksi ekseninde dinlenmis egri tanim geregi duz kosegen cikiyor
    ve plato/diz sekli kayboluyor. Kapasite ekseni (desarj kosusunun coulomb
    sayimindan) bunu ortaya cikarir.

    Eksen MUTLAK SoC DEGIL: kosu dolu hucreden baslamadi, bu pencere hucrenin
    %36-53'u. Bu yuzden 0-100 SoC gibi etiketlenmez.
    """
    t = THEMES[theme_name]
    xs = [r["window"] for r in rows]

    fig, ax = plt.subplots(figsize=(10, 6.4))
    fig.patch.set_facecolor(t["surface"])
    ax.set_facecolor(t["surface"])
    ax.grid(True, color=t["grid"], linewidth=0.8, zorder=0)
    ax.set_axisbelow(True)
    for side in ("top", "right"):
        ax.spines[side].set_visible(False)
    for side in ("left", "bottom"):
        ax.spines[side].set_color(t["grid"])
    ax.tick_params(colors=t["muted"], labelsize=10)

    for value_key, src_key, color, label in (
        ("charging", "charging_src", t["charging"], "Şarj olurken (~0,5C)"),
        ("rested", None, t["rested"], "Dinlenmiş / ortalama (açık devre)"),
        ("loaded", "loaded_src", t["load"], "Deşarj, yük altında (~0,16C)"),
    ):
        if src_key is None:
            ax.plot(xs, [r[value_key] for r in rows], color=color,
                    linewidth=2, zorder=4, label=label)
            continue
        labelled = False
        for points, measured in runs_by_source(rows, value_key, src_key, "window"):
            use_label = label if measured and not labelled else None
            labelled = labelled or measured
            ax.plot([p[0] for p in points], [p[1] for p in points],
                    color=color, linewidth=2,
                    linestyle="-" if measured else (0, (5, 3)),
                    label=use_label, zorder=5 if measured else 4)

    # Olculen ciftlerin nereye dustugunu goster: cizgi 101 noktalik izgarada
    # ciziliyor, ama gercek olcum bunlar. Arasi interpolasyon.
    inverse = sorted((r["rested"], r["window"]) for r in rows)

    def window_at(rested_v: float) -> float | None:
        for a, b in zip(inverse, inverse[1:]):
            if a[0] <= rested_v <= b[0]:
                span = b[0] - a[0]
                f = 0.0 if span == 0 else (rested_v - a[0]) / span
                return a[1] + f * (b[1] - a[1])
        return None

    for runs, value_col, color in ((charge, "charging_mv", t["charging"]),
                                   (discharge, "loaded_mv", t["load"])):
        pts = [(w, r[value_col] / 1000) for r in runs
               if (w := window_at(r["rested_mv"] / 1000)) is not None]
        if pts:
            ax.plot([p[0] for p in pts], [p[1] for p in pts], linestyle="none",
                    marker="o", markersize=6, color=color,
                    markeredgecolor=t["surface"], markeredgewidth=1.8, zorder=6)
    rest_pts = [(w, r["rested_mv"] / 1000) for r in discharge
                if (w := window_at(r["rested_mv"] / 1000)) is not None]
    ax.plot([p[0] for p in rest_pts], [p[1] for p in rest_pts], linestyle="none",
            marker="o", markersize=6, color=t["rested"],
            markeredgecolor=t["surface"], markeredgewidth=1.8, zorder=6)

    # Seri adlari dogrudan cizgi ucunda.
    for label, value_key, dy, va in (("Şarj", "charging", 4, "bottom"),
                                     ("Dinlenmiş", "rested", 0, "center"),
                                     ("Deşarj", "loaded", -13, "top")):
        ax.annotate(label, xy=(xs[-1], rows[-1][value_key]), xytext=(9, dy),
                    textcoords="offset points", color=t["text"], fontsize=11,
                    fontweight="bold", va=va, ha="left")

    ax.set_title(
        "Power-Xtra PX103049 — üç durum, deşarj koşusunun kapasite penceresinde",
        color=t["text"], fontsize=13.5, fontweight="bold", loc="left", pad=14,
    )
    ax.set_ylabel("Batarya gerilimi (V)", color=t["muted"], fontsize=11)
    ax.set_xlabel("Koşuda kalan kapasite (%) — coulomb sayımı. "
                  "MUTLAK ŞARJ DURUMU DEĞİL",
                  color=t["muted"], fontsize=11)
    ax.xaxis.set_major_locator(MultipleLocator(10))
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.set_ylim(2.94, 4.06)
    ax.set_xlim(0, 100)

    legend = ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])

    # Iki ucun da ne oldugunu grafigin kendisi soylemeli.
    ax.annotate("%0 = koşunun sonu. Yük altında 2,99 V —\n"
                "firmware'in boş kabulü (3,00 V). Bu uç tamam.",
                xy=(17, 3.30), color=t["muted"], fontsize=9.5,
                ha="left", va="top")
    ax.annotate("%100 = koşunun başı (dinlenmiş 3,89 V), DOLU DEĞİL.\n"
                "Hücre şarjda 4,09 V'a çıkmıştı; bu pencere hücrenin\n"
                "yalnızca %36–53'ü. O yüzden eksen %0–100 SoC değil.",
                xy=(98, 3.02), color=t["muted"], fontsize=9.5,
                ha="right", va="bottom")

    fig.text(0.008, 0.015,
             "Kapasite ekseni deşarj koşusunun coulomb sayımından (sabit dummy "
             "load, yük-açık süresi). Kesikli = tahmin; ayrıntı README'de.",
             color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.895, top=0.915, bottom=0.135)

    OUT.mkdir(exist_ok=True)
    name = "window_curve.svg" if svg else f"window_curve-{theme_name}.png"
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

    discharge = load_discharge_rows()
    if not discharge:
        raise SystemExit("data/measurements-discharge.csv icinde tamamlanmis olcum yok.")
    written += [
        render_states(rows, discharge, "light"),
        render_states(rows, discharge, "dark"),
        render_states(rows, discharge, "light", svg=True),
        write_lookup(build_map(discharge, "loaded_mv"),
                     name="lookup-discharge.csv", first_col="loaded_mv"),
    ]

    combined_path = ROOT / "data" / "lookup-combined.csv"
    if combined_path.exists():
        combined = load_combined()
        written += [
            render_full_range(combined, rows, discharge, "light"),
            render_full_range(combined, rows, discharge, "dark"),
            render_full_range(combined, rows, discharge, "light", svg=True),
        ]
    else:
        print("uyari: data/lookup-combined.csv yok -> once scripts/predict_map.py")

    soc_path = ROOT / "data" / "window-curve.csv"
    if soc_path.exists():
        soc_rows = load_window_curve()
        written += [
            render_window_curve(soc_rows, rows, discharge, "light"),
            render_window_curve(soc_rows, rows, discharge, "dark"),
            render_window_curve(soc_rows, rows, discharge, "light", svg=True),
        ]
    else:
        print("uyari: data/window-curve.csv yok -> once scripts/window_curve.py")

    for path in written:
        print(path.relative_to(ROOT))


if __name__ == "__main__":
    main()
