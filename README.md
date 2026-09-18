# `px103049` — Power-Xtra PX103049 (3,7 V / 1500 mAh Li-Po)

Bu dal **yalnızca bu hücreye** aittir: kendi ölçüm verisi, kendi grafikleri ve
`BATTERY` bloğu bu hücreye ayarlanmış script. Diğer hücrenin (PX803035, 800 mAh)
dosyaları burada **yok** — onlar `px803035` dalında.

**Ölçümün anlatıldığı rapor `main` dalındadır.** Tablolar, tutarlılık kontrolleri ve
sınırlar orada; bu dal kodu ve girdisini taşır.

## Bu daldakiler

| Dosya | İçerik |
|---|---|
| `data/raw_dump.log` | İlk koşunun ham seri port çıktısı, hiç düzenlenmedi |
| `data/measurements.csv` | İlk koşunun 13 ölçüm çifti (şarj yönü) |
| `data/raw_dump-run2.log`, `data/measurements-run2.csv` | İkinci koşu |
| `data/raw_dump-run2b.log`, `data/measurements-run2b.csv` | İkinci koşunun devam segmenti |
| `data/predicted-run2.csv` | **Tahmin** (%90, %95) — ölçüm değil |
| `data/raw_dump-discharge.log`, `data/measurements-discharge.csv` | Deşarj koşusu, 15 çift |
| `data/lookup.csv` | Şarjdaki gerilimden dinlenmiş karşılığı (10 mV adım) |
| `data/lookup-discharge.csv` | Yük altındaki gerilimden dinlenmiş karşılığı (10 mV adım) |
| `graphs/state_overlay-*` | Üç durum üst üste |
| `graphs/voltage_overlay-*` | Şarj yönü ayrıntısı |
| `graphs/discharge_overlay-*` | Deşarj yönü ayrıntısı |
| `scripts/plot_voltage.py` | Grafikleri ve arama tablolarını üretir |

## Çalıştırmak

```bash
python -m venv .venv
.venv/Scripts/activate         # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/plot_voltage.py
```

Argüman almaz; hangi bataryayı işleyeceği `scripts/plot_voltage.py` başındaki
`BATTERY` blokundan gelir ve bu dalda o blok PX103049'a ayarlıdır:

```
Batarya: Power-Xtra PX103049 (3,7 V / 1500 mAh Li-Po)
Girdi:   data/measurements.csv (13 cift), data/measurements-discharge.csv (15 cift)
Yazilan:
  graphs/voltage_overlay-light.png
  ...
  data/lookup-discharge.csv
```

Listelenen dosyalar üzerine yazılır. Çıktı deterministiktir — veri değişmediyse
PNG'ler bayt bayt aynı çıkar. SVG'ler hariç: matplotlib içlerine üretim tarihi ve
rastgele `clip-path` id'leri koyduğu için içerikçe aynı, baytça farklı olurlar.

Bu hücrede `load_ohms=None` — deşarj koşusu sırasında dummy load'un direnci
kaydedilmedi, ~26,8 Ω / ~143 mA sonradan çıkarıldı. `capacity_mah=1500` etiketten
geliyor ve ayrı bir deşarj testiyle doğrulanmadı; `main`'deki raporun 8. sınırı bunun
bıraktığı tutarsızlığı anlatıyor.

## Depodaki dallar

| Dal | Ne taşır |
|---|---|
| `main` | Rapor: iki bataryanın da verisi, tabloları, grafikleri ve anlatımı |
| **`px103049`** | **PX103049 (1500 mAh) — burası** |
| `px803035` | PX803035 (800 mAh) — kendi verisi, grafikleri, `BATTERY` ayarı |
| `archive/sarj`, `archive/ikinci-olcum` | eski ölçüm dalları, pasif |
