# `px803035` — Power-Xtra PX803035 (3,7 V / 800 mAh Li-Po)

Bu dal **yalnızca bu hücreye** aittir: kendi ölçüm verisi, kendi grafikleri ve
`BATTERY` bloğu bu hücreye ayarlanmış script. Diğer hücrenin (PX103049, 1500 mAh)
dosyaları burada **yok** — onlar `px103049` dalında.

**Ölçümün anlatıldığı rapor `main` dalındadır.** Tablolar, tutarlılık kontrolleri ve
sınırlar orada; bu dal kodu ve girdisini taşır.

## Bu daldakiler

| Dosya | İçerik |
|---|---|
| `data/raw_dump-800mah.log` | Cihazdan alınan ham seri port çıktısı, hiç düzenlenmedi |
| `data/measurements-discharge-800mah.csv` | Faz 1 — yük yönünde 16 ölçüm çifti |
| `data/measurements-charge-800mah.csv` | Faz 2 — şarj yönünde 15 ölçüm çifti |
| `data/lookup-discharge-800mah.csv` | Yük altındaki gerilimden dinlenmiş karşılığı (10 mV adım) |
| `data/lookup-charge-800mah.csv` | Şarjdaki gerilimden dinlenmiş karşılığı (10 mV adım) |
| `graphs/state_overlay-800mah-*` | Üç durum üst üste |
| `graphs/voltage_overlay-800mah-*` | Şarj yönü ayrıntısı |
| `graphs/discharge_overlay-800mah-*` | Deşarj yönü ayrıntısı |
| `scripts/plot_voltage.py` | Grafikleri ve arama tablolarını üretir |

## Çalıştırmak

```bash
python -m venv .venv
.venv/Scripts/activate         # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/plot_voltage.py
```

Argüman almaz; hangi bataryayı işleyeceği `scripts/plot_voltage.py` başındaki
`BATTERY` blokundan gelir ve bu dalda o blok PX803035'e ayarlıdır:

```
Batarya: Power-Xtra PX803035 (3,7 V / 800 mAh Li-Po)
Girdi:   data/measurements-charge-800mah.csv (15 cift), data/measurements-discharge-800mah.csv (16 cift)
Yazilan:
  graphs/voltage_overlay-800mah-light.png
  ...
  data/lookup-discharge-800mah.csv
```

Listelenen dosyalar üzerine yazılır. Çıktı deterministiktir — veri değişmediyse
PNG'ler bayt bayt aynı çıkar. SVG'ler hariç: matplotlib içlerine üretim tarihi ve
rastgele `clip-path` id'leri koyduğu için içerikçe aynı, baytça farklı olurlar.

Bu hücrenin özellikleri (`load_ohms=12,20` ölçüm, `capacity_mah=800` etiketten),
`BATTERY` bloğunun nasıl doldurulacağı ve yeni bir batarya nasıl eklenir — hepsi
`main` dalındaki raporun "Kodu çalıştırmak" bölümünde.

## Depodaki dallar

| Dal | Ne taşır |
|---|---|
| `main` | Rapor: iki bataryanın da verisi, tabloları, grafikleri ve anlatımı |
| `px103049` | PX103049 (1500 mAh) — kendi verisi, grafikleri, `BATTERY` ayarı |
| **`px803035`** | **PX803035 (800 mAh) — burası** |
| `archive/sarj`, `archive/ikinci-olcum` | eski ölçüm dalları, pasif |
