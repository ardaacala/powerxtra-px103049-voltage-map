"""Sarj / dinlenmis / yuk altinda gerilim haritasi grafikleri.

Hangi batarya islenecegi dosyanin basindaki BATTERY blogundan gelir; script'te
batarya-ozel baska bir yer yoktur. Su an yapilandirilmis olan: PX103049.
Diger hucrenin (PX803035) ayari `px803035` branch'inde.

Girdiler (data/ altinda, BATTERY'den):
  BATTERY["charge_csv"]  -> sarj yonundeki olcum ciftleri
  BATTERY["load_csv"]    -> yuk yonundeki olcum ciftleri

Ciktilar:
  graphs/<state_stem>-light.png / -dark.png / .svg  -> uc durum ust uste
  graphs/<charge_stem>-*  /  <load_stem>-*          -> yalnizca graphs= acikken
  data/<charge_lookup>, data/<load_lookup>          -> 10 mV adimli arama tablolari

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
OUT = ROOT / "graphs"

# ===========================================================================
# OLCULEN BATARYA
#
# Bu blok disinda script'te batarya-ozel hicbir sey yok. Baska bir hucreye
# gecmek icin yalnizca burasi degisir -- girdi CSV'leri, cikti adlari, gerilim
# olcegi ve uc durum grafiginin eksenleri. Onceki hucrenin (PX103049) hazir
# ayari `px803035` branch'inde ayni yerde duruyor.
#
# Nasil calistirilacagi ve blogun nasil doldurulacagi README'de:
# "Kodu calistirmak" ve "Baska bir batarya icin".
# ===========================================================================
BATTERY = dict(
    model="PX103049",
    nominal="3,7 V / 1500 mAh Li-Po",
    capacity_mah=1500,          # hucre etiketinden; ayri bir desarj testiyle
                                # dogrulanmadi (README sinir 8).

    # Gerilim olcegi -- firmware'deki BatteryConfig.h ile AYNI olmali.
    # voltage_pct bu ikisinden hesaplanir; dogrusal bir indeks, doluluk degil.
    empty_mv=3000.0,
    full_mv=4200.0,

    # Bu kosularda dummy load'un direnci kaydedilmedi. Sonradan olculen 12,2
    # ohm uzerinden ~26,8 ohm / ~143 mA olarak CIKARILDI, yani olcum degil --
    # o yuzden burada None.
    load_ohms=None,

    # Girdiler: data/ altindaki olcum CSV'leri.
    charge_csv="measurements.csv",
    load_csv="measurements-discharge.csv",

    # Ciktilar: data/ altindaki arama tablolari.
    charge_lookup="lookup.csv",
    load_lookup="lookup-discharge.csv",

    # Bu hucrenin uc grafigi de uretilir. "charge" ve "load" ayrinti
    # grafiklerinin icindeki aciklama metinleri bu hucrenin sayilarina gore
    # yazilmistir -- baska bir bataryaya gecerken render()/render_discharge()
    # icindeki annotate() cagrilarini da guncellemek gerekir.
    graphs=("charge", "load", "state"),
    charge_stem="voltage_overlay",
    load_stem="discharge_overlay",
    state_stem="state_overlay",

    # Uc durum grafiginin ekseni ve metinleri. Sinirlar elle veriliyor ki
    # kaydedilmis grafikler yeniden uretildiginde birebir ayni ciksin.
    state_label="Şarj olurken (0,5C)",
    state_footnote=("Şarj: 13 çift, ~0,5C (koşu 1). Yük: 15 çift, sabit dummy load. "
                    "Her iki yönde de 60 s dinlenme; ADC kalibre edilmedi."),
    state_xlim=(3.03, 4.13),
    state_ylim=(2.95, 4.20),
    state_delta_ylim=(-130, 210),
    state_note_x=3.42,
)
DATA = ROOT / "data" / BATTERY["charge_csv"]
DATA_DISCHARGE = ROOT / "data" / BATTERY["load_csv"]
EMPTY_MV = BATTERY["empty_mv"]
FULL_MV = BATTERY["full_mv"]

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


def load_rows(path: Path = DATA) -> list[dict]:
    """Yalnizca tamamlanmis (complete=1) olcum ciftlerini dondurur."""
    rows = []
    with path.open(encoding="utf-8") as handle:
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


def load_discharge_rows(path: Path = DATA_DISCHARGE) -> list[dict]:
    """Desarj kosusunun tamamlanmis ciftleri, dinlenmis gerilime gore artan.

    Kolon adlari sarj kosusundan farkli: firmware yuk yonunde olcerken
    `loaded_mv` (yuk bagliyken) ve `recovered_mv` (60 s sonra) yaziyor.
    delta_mv bu kosuda negatif -- yuk altindaki gerilim dinlenmisin altinda.
    """
    rows = []
    with path.open(encoding="utf-8") as handle:
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
        f"Power-Xtra {BATTERY['model']} ({BATTERY['nominal']}) — şarj ve dinlenmiş gerilim",
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
    stem = BATTERY["charge_stem"]
    name = f"{stem}.svg" if svg else f"{stem}-{theme_name}.png"
    path = OUT / name
    fig.savefig(path, dpi=None if svg else 200, facecolor=t["surface"])
    plt.close(fig)
    return path


def render_discharge(rows: list[dict], theme_name: str, svg: bool = False) -> Path:
    """render()'in yuk yonundeki esi: ayni duzen, ayni eksen, ters yon.

    Sarj grafigiyle ayni eksende (esik %) ayri cizilir, ustune bindirilmez:
    esik zaten olculen terminal geriliminde tetiklendigi icin `charging_mv`
    ile `loaded_mv` ortak esiklerde 3-20 mV icinde cakisiyor. Ust uste
    konsa iki egri birbirini ortup hicbir sey gostermezdi; ayri cizilince
    her yonun kendi sapmasi okunabiliyor.
    """
    t = THEMES[theme_name]
    rows = sorted(rows, key=lambda r: r["threshold_pct"])
    x = [r["threshold_pct"] for r in rows]
    loaded = [r["loaded_mv"] / 1000 for r in rows]
    recovered = [r["rested_mv"] / 1000 for r in rows]
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
    # Bu yonde toparlanmis deger yuk altindakinin USTUNDE kalir.
    ax.fill_between(x, loaded, recovered, color=t["load"], alpha=0.10,
                    linewidth=0, zorder=1)
    ax.plot(x, recovered, color=t["rested"], linewidth=2, marker="o",
            markersize=8, markeredgecolor=t["surface"], markeredgewidth=2,
            label="1 dk toparlanmış", zorder=3)
    ax.plot(x, loaded, color=t["load"], linewidth=2, marker="o",
            markersize=8, markeredgecolor=t["surface"], markeredgewidth=2,
            label="Yük altında", zorder=3)

    ax.annotate("1 dk toparlanmış", xy=(x[-1], recovered[-1]), xytext=(9, 3),
                textcoords="offset points", color=t["text"], fontsize=11,
                fontweight="bold", va="bottom", ha="left")
    ax.annotate("Yük altında", xy=(x[-1], loaded[-1]), xytext=(9, -3),
                textcoords="offset points", color=t["text"], fontsize=11,
                fontweight="bold", va="top", ha="left")

    ax.set_title(
        f"Power-Xtra {BATTERY['model']} ({BATTERY['nominal']}) — yük altında ve "
        "toparlanmış gerilim",
        color=t["text"], fontsize=13.5, fontweight="bold", loc="left", pad=14,
    )
    ax.set_ylabel("Batarya gerilimi (V)", color=t["muted"], fontsize=11)
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.set_ylim(2.94, 3.96)
    ax.set_xlim(-4, 76)
    legend = ax.legend(loc="upper left", frameon=False, fontsize=10.5)
    for text in legend.get_texts():
        text.set_color(t["text"])

    # Firmware'in bos kabulu: sarj grafigindeki 4,20 V tavaninin karsiligi.
    ax.axhline(3.0, color=t["muted"], linewidth=1, linestyle=(0, (4, 4)), zorder=2)
    ax.annotate("3,00 V — firmware'in boş kabulü; koşu yük altında 2,99 V'ta bitti",
                xy=(-3, 3.0), xytext=(0, 6), textcoords="offset points",
                color=t["muted"], fontsize=9.5, va="bottom", ha="left")

    # --- Alt panel: aradaki fark ---------------------------------------------
    ax_delta.plot(x, delta, color=t["load"], linewidth=2, marker="o",
                  markersize=7, markeredgecolor=t["surface"], markeredgewidth=2,
                  zorder=3)
    ax_delta.set_ylabel("Fark (mV)", color=t["muted"], fontsize=11)
    ax_delta.set_xlabel("Gerilim ölçeği eşiği (%) — gerçek doluluk değil",
                        color=t["muted"], fontsize=11)
    ax_delta.xaxis.set_major_locator(MultipleLocator(5))
    ax_delta.set_ylim(-100, 0)

    # Sarj yonunun tersi: sapma bosaldikca BUYUYOR, cunku ic direnc artiyor.
    ax_delta.annotate("boşaldıkça büyüyor: −46 → −80 mV", xy=(38, -88),
                      color=t["text"], fontsize=10, ha="center", va="center")

    fig.text(0.008, 0.012,
             "15 ölçüm çifti — aynı düzenek, anahtarın ucunda sabit dummy load. "
             "Dinlenme 60 s; ADC kalibre edilmedi.",
             color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.845, top=0.925, bottom=0.105)

    OUT.mkdir(exist_ok=True)
    stem = BATTERY["load_stem"]
    name = f"{stem}.svg" if svg else f"{stem}-{theme_name}.png"
    path = OUT / name
    fig.savefig(path, dpi=None if svg else 200, facecolor=t["surface"])
    plt.close(fig)
    return path


def render_states(
    charge: list[dict], discharge: list[dict], theme_name: str, svg: bool = False,
    *, stem: str, title: str, charge_label: str, footnote: str,
    xlim: tuple[float, float], ylim: tuple[float, float],
    delta_ylim: tuple[float, float], note_x: float,
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
            label=charge_label, zorder=4)
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
    # Referans ayri tutulur: soluk ve kalin degil, cunku olcum degil.
    ax.annotate("dinlenmiş = eksen\n(veri değil)", xy=(ref_x[-1], ref_x[-1]),
                xytext=(9, -9), textcoords="offset points", color=t["muted"],
                fontsize=9.5, va="top", ha="left")

    ax.set_title(title, color=t["text"], fontsize=14, fontweight="bold",
                 loc="left", pad=14)
    ax.set_ylabel("Terminal gerilimi (V)", color=t["muted"], fontsize=11)
    ax.yaxis.set_major_locator(MultipleLocator(0.1))
    ax.set_ylim(*ylim)
    ax.set_xlim(*xlim)
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
    ax_delta.set_ylim(*delta_ylim)

    # Aciklamalar egrilerin bos tarafinda: sarj serisinin ustu, yukun alti.
    ch_d = [r["delta_mv"] for r in charge]
    ld_d = [r["delta_mv"] for r in discharge]
    ax_delta.annotate(f"şarj yönü: +{min(ch_d):.0f} … +{max(ch_d):.0f} mV",
                      xy=(note_x, delta_ylim[1] - 20), color=t["text"], fontsize=10,
                      ha="left", va="center")
    ax_delta.annotate(f"yük yönü: −{abs(max(ld_d)):.0f} … −{abs(min(ld_d)):.0f} mV",
                      xy=(note_x, delta_ylim[0] + 20), color=t["text"], fontsize=10,
                      ha="left", va="center")

    fig.text(0.008, 0.012, footnote, color=t["muted"], fontsize=9)
    fig.subplots_adjust(left=0.085, right=0.845, top=0.925, bottom=0.105)

    OUT.mkdir(exist_ok=True)
    name = f"{stem}.svg" if svg else f"{stem}-{theme_name}.png"
    path = OUT / name
    fig.savefig(path, dpi=None if svg else 200, facecolor=t["surface"])
    plt.close(fig)
    return path


def main() -> None:
    """Yapilandirilmis bataryanin grafiklerini ve arama tablolarini uretir."""
    charge = load_rows()
    if not charge:
        raise SystemExit(f"data/{BATTERY['charge_csv']} icinde tamamlanmis cift yok.")
    load = load_discharge_rows()
    if not load:
        raise SystemExit(f"data/{BATTERY['load_csv']} icinde tamamlanmis cift yok.")

    state_opts = dict(
        stem=BATTERY["state_stem"],
        title=(f"Power-Xtra {BATTERY['model']} — aynı hücre, üç durum: "
               "şarjda, dinlenmiş, yük altında"),
        charge_label=BATTERY["state_label"],
        footnote=BATTERY["state_footnote"],
        xlim=BATTERY["state_xlim"],
        ylim=BATTERY["state_ylim"],
        delta_ylim=BATTERY["state_delta_ylim"],
        note_x=BATTERY["state_note_x"],
    )

    written: list[Path] = []
    if "charge" in BATTERY["graphs"]:
        written += [render(charge, "light"), render(charge, "dark"),
                    render(charge, "light", svg=True)]
    if "load" in BATTERY["graphs"]:
        written += [render_discharge(load, "light"), render_discharge(load, "dark"),
                    render_discharge(load, "light", svg=True)]
    if "state" in BATTERY["graphs"]:
        written += [render_states(charge, load, "light", **state_opts),
                    render_states(charge, load, "dark", **state_opts),
                    render_states(charge, load, "light", svg=True, **state_opts)]
    written += [
        write_lookup(build_map(charge), name=BATTERY["charge_lookup"]),
        write_lookup(build_map(load, "loaded_mv"),
                     name=BATTERY["load_lookup"], first_col="loaded_mv"),
    ]

    print(f"Batarya: Power-Xtra {BATTERY['model']} ({BATTERY['nominal']})")
    print(f"Girdi:   data/{BATTERY['charge_csv']} ({len(charge)} cift), "
          f"data/{BATTERY['load_csv']} ({len(load)} cift)")
    print("Yazilan:")
    for path in written:
        print(f"  {path.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
