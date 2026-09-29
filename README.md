# `inr18650mj1` — LG INR18650 MJ1 (3,635 V / 3400 mAh Li-ion)

Bu dal **yalnızca bu hücreye** aittir. Hücre **henüz ölçülmedi**: dalda şimdilik
yalnızca bu hücreye ayarlanmış script var, `data/` ve `graphs/` ilk koşudan sonra
dolacak. Önceki hücrelerin dosyaları kendi dallarında (`px103049`, `px803035`).

**Ölçümün anlatıldığı rapor `main` dalındadır.**

## Hücre

| | Değer | Kaynak |
|---|---|---|
| Model | LG INR18650 MJ1, 18650 Li-ion (NMC) | sargı etiketi |
| Kapasite | 3400 mAh minimum / 3500 mAh tipik | etiket `3.40Ah` / datasheet |
| Nominal gerilim | 3,635 V | datasheet |
| Şarj | 4,20 V ± 0,05 V CC-CV | datasheet |
| Deşarj alt sınırı | 2,50 V | datasheet |
| Koruma | hücre üstünde koruma PCB'si var | fotoğraf |

## Firmware ayarı (`tps22919_switch_test/include/BatteryConfig.h`)

Düzenek aynı: ESP32 + iki TPS22919 (GPIO4 yük, GPIO17 şarj) + 10 kΩ/10 kΩ bölücü
(GPIO32) + 12,2 Ω dummy load. PX803035'e göre değişenler:

| Sabit | PX803035 | MJ1 | Neden |
|---|---|---|---|
| `EMPTY_MV` | 3000 | **2800** | Li-ion 2,5 V'a kadar iner; güvenlik tabanları ölçeğin altında kalmak zorunda |
| `DISCHARGE_CUTOFF_MV` | 2500 | **2600** | taban sırası: inhibit < cutoff < validity |
| `LOAD_INHIBIT_MV` | 2400 | **2500** | datasheet alt sınırının altına hiç yük bağlanmaz |
| `MIN_VALID_MV` / `MAX_VALID_MV` | 2700 / 4250 | aynı | 4250 = şarj toleransının üst ucu |
| `MAX_CHARGE_STAGE_MS` | 2 saat | **6 saat** | düz platoda tek 70 mV'luk basamak 2–3 saat sürebilir |
| `MAX_RUN_MS` | 24 saat | **48 saat** | ≈12 saat deşarj + şarj (şarj cihazına bağlı) |

Gerilim ölçeği 2,80–4,20 V, adım %5 = 70 mV. PX803035'in ayarı
`BatteryConfig.h.px803035` dosyasında duruyor.

12,2 Ω yük bu hücrede 0,23–0,34 A (≈0,1C) çeker, tam deşarj 11–12 saat sürer. Yük
direnci değiştiyse yeniden ölçüp hem firmware'e hem `BATTERY["load_ohms"]`'a yaz.

## Çalıştırmak

```bash
python -m venv .venv
.venv/Scripts/activate         # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/plot_voltage.py
```

Script şu dosyaları bekler. Yoksa ne eksik olduğunu söyleyip çıkar:

- `data/measurements-discharge-mj1.csv`: faz 1, yük yönündeki çiftler
- `data/measurements-charge-mj1.csv`: faz 2, şarj yönündeki çiftler

Ham seri çıktı `data/raw_dump-mj1.log` olarak saklanmalı. Çıktılar `graphs/*-mj1*`
ve `data/lookup-*-mj1.csv`.

`BATTERY` bloğundaki eksen sınırları ve açıklama metinleri datasheet'e göre
**tahmini başlangıç değerleridir**. İlk veri gelince grafiklere bakıp düzeltilmeli.

## Depodaki dallar

| Dal | Ne taşır |
|---|---|
| `main` | Rapor: ölçülen bataryaların verisi, tabloları, grafikleri ve anlatımı |
| `px103049` | PX103049 (1500 mAh Li-Po) |
| `px803035` | PX803035 (800 mAh Li-Po) |
| **`inr18650mj1`** | **LG INR18650 MJ1 (3400 mAh Li-ion) — burası, ölçüm bekliyor** |
| `archive/sarj`, `archive/ikinci-olcum` | eski ölçüm dalları, pasif |
