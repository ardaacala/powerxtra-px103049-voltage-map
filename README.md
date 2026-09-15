# Power-Xtra PX103049 — şarj / dinlenmiş gerilim haritası

Power-Xtra **PX103049** (3,7 V nominal, 1500 mAh Li-Po) hücresinde, **şarj sürerken
okunan gerilim** ile **şarj kesildikten 1 dakika sonra okunan gerilim** arasındaki
ilişkinin ölçüm verisi.

Amacı basit: karakteristiği bilinmeyen bir bataryada şarj sırasında okuduğun gerilim,
iç direnç ve polarizasyon yüzünden gerçek durumun üstünde görünür. Bu depo, o farkı
tek bir hücre için ölçülmüş sayılarla verir — şarjda X V görüyorsan dinlenmiş karşılığı
yaklaşık Y V.

![Şarj ve dinlenmiş gerilim](graphs/voltage_overlay-light.png#gh-light-mode-only)
![Şarj ve dinlenmiş gerilim](graphs/voltage_overlay-dark.png#gh-dark-mode-only)

Üst panel iki gerilimi üst üste gösterir; aradaki taralı bant farkın kendisidir.
Alt panel bu farkı ayrıca çizer: sabit akım (CC) boyunca ~140 mV'ta sabit kalıyor,
şarj sabit gerilim (CV) aşamasına geçip akım azaldıkça 51 mV'a kadar kapanıyor.

## Ölçüm düzeneği

| Parça | Rol |
|---|---|
| ESP32-WROOM-32D DevKit | Ölçüm ve anahtar kontrolü |
| TPS22919 yük anahtarı | Şarj hattını açıp kapatır (GPIO4, HIGH = açık) |
| 10 kΩ + 10 kΩ gerilim bölücü | Batarya gerilimini ikiye böler, orta nokta GPIO34'e (ADC1_CH6) |
| Power-Xtra PX103049 | Ölçülen hücre, 3,7 V / 1500 mAh Li-Po |

Ölçüm akışı: her saniye 32 ADC örneğinin ortalaması alınır. Şarj gerilimi bir sonraki
%5 eşiğinin en az 5 saniye üzerinde kalınca o an `charging_mv` olarak kaydedilir ve
anahtar kapatılır. Anahtar 60 saniye kapalı kalır; süre sonunda okunan değer
`rested_mv` olur, çift tamamlanır ve şarj yeniden açılır. Dinlenme boyunca 5, 10, 15,
20, 30, 40 ve 50. saniyelerde de ara ölçüm alınır (`relax_mv`) — gerilimin oturup
oturmadığı bu sütundan görülür.

Ölçümü yapan firmware ayrı bir depodadır: `tps22919_switch_test`.

## Veri

| # | Eşik % | Şarjda (mV) | Dinlenmiş (mV) | Fark (mV) | O ana kadar şarj |
|---:|---:|---:|---:|---:|---:|
| 1 | 35 | 3426,4 | 3260,8 | 165,6 | 6 s |
| 2 | 40 | 3482,9 | 3353,9 | 128,9 | 1 dk 34 s |
| 3 | 45 | 3558,6 | 3415,9 | 142,6 | 2 dk 53 s |
| 4 | 50 | 3606,9 | 3467,7 | 139,2 | 4 dk 25 s |
| 5 | 55 | 3663,9 | 3519,7 | 144,2 | 7 dk 13 s |
| 6 | 60 | 3721,8 | 3579,5 | 142,2 | 16 dk 15 s |
| 7 | 65 | 3784,1 | 3645,6 | 138,6 | 23 dk 20 s |
| 8 | 70 | 3841,0 | 3702,9 | 138,1 | 33 dk 08 s |
| 9 | 75 | 3901,6 | 3762,2 | 139,4 | 42 dk 51 s |
| 10 | 80 | 3961,4 | 3834,3 | 127,1 | 52 dk 40 s |
| 11 | 85 | 4020,2 | 3907,4 | 112,8 | 1 sa 08 dk |
| 12 | 90 | 4081,5 | 3999,8 | 81,8 | 1 sa 41 dk |
| 13 | 95 | 4140,1 | 4089,2 | 50,9 | 2 sa 45 dk |

Başlangıç (şarj hiç açılmadan, dinlenmiş): **3255,2 mV**.

### Dosyalar

| Dosya | İçerik |
|---|---|
| [`data/measurements.csv`](data/measurements.csv) | 13 ölçüm çifti, `relax_mv` ara noktaları dahil |
| [`data/lookup.csv`](data/lookup.csv) | 10 mV adımlı arama tablosu — şarjdaki gerilimden dinlenmiş karşılığı |
| [`data/raw_dump.log`](data/raw_dump.log) | Cihazdan alınan ham seri port çıktısı, hiç düzenlenmedi |
| [`scripts/plot_voltage.py`](scripts/plot_voltage.py) | Grafikleri ve arama tablosunu üretir |

`lookup.csv` yalnızca ölçülen aralığı (3430–4140 mV) doldurur; dışına **ekstrapolasyon
yapılmaz**. Ara değerler parça-parça doğrusaldır.

## Veri gerçekten tutarlı mı

Sayıların fiziksel olarak anlamlı olup olmadığını birkaç bağımsız yoldan kontrol ettim:

- **Fark profili beklendiği gibi.** CC aşamasında 6.–9. satırlarda 138–144 mV ile
  sabit; CV'ye geçişte 113 → 82 → 51 mV'a düşüyor. Akım azaldıkça IR düşüşünün
  azalması tam olarak olması gereken şey.
- **İma edilen şarj akımı CC bölgesinde sabit.** Ardışık `rested_mv` değerlerini genel
  bir Li-Po OCV→SoC eğrisinden geçirip 1500 mAh üzerinden hesaplayınca 6.–10.
  satırlarda 695 / 959 / 725 / 732 / 838 mA çıkıyor — ortalama ~750 mA (≈0,5C).
  Sonrasında 420 → 226 → 97 mA ile düzgün bir CV kuyruğu. Beş bağımsız adımdan
  aynı akımın çıkması verinin gerçekliğinin en güçlü işareti.
- **İç direnç makul.** 140 mV / 750 mA ≈ 187 mΩ. Bu boyutta bir pouch hücre + TPS22919
  (~42 mΩ) + kablolama için beklenen aralıkta.
- **İlk satır fizik testini geçiyor.** Yalnızca 6 saniye şarjdan sonra dinlenmiş gerilim
  3260,8 mV — başlangıçtaki 3255,2 mV'un sadece 5,6 mV üstünde. Neredeyse hiç enerji
  girmediği için doğru sonuç.
- **İç tutarlılık temiz.** Her iki gerilim de monoton artıyor, her satırda
  `rested < charging`, `threshold_pct` ölçülen gerilimle birebir uyuşuyor, dinlenme
  süresi her satırda 61000 ms, değerler ADC'nin 0,0625 mV (= 2/32) ızgarasına oturuyor
  ve örnekleme 5 saat boyunca kaymamış.

## Sınırlar — bunları bilmeden kullanma

1. **Alt uçta 60 saniye yetmiyor.** 2.–5. satırlarda yukarıdaki akım hesabı
   2000–4600 mA veriyor; bu fiziksel değil. Sebebi düşük SoC'de dinlenmenin kısa
   kalması: `rested_mv` hâlâ yüksek okunuyor. Yani **3,35–3,52 V aralığındaki
   dinlenmiş değerler bir miktar yüksek**. 6. satırdan (3,72 V) yukarısı güvenilir.
2. **Üç çift henüz oturmamıştı.** 50. saniye ile 60. saniye arasındaki değişim
   6. satırda 2,31 mV, 7. satırda 2,44 mV, 11. satırda 2,50 mV — 2 mV eşiğinin
   üstünde. Dinlenme süresi 120–180 s olsaydı harita daha temiz olurdu.
3. **ADC kalibre edilmedi.** Kazanç 1,000000, ofset 0,00 — yani ham
   `analogReadMilliVolts` değerleri, ESP32'nin kendi eFuse kalibrasyonuna güveniliyor.
   Farklar bundan etkilenmez (sistematik hata iptal olur) ama **mutlak değerlerde
   tipik ±20–30 mV sistematik kayma olabilir.**
4. **%100 eşiğine hiç ulaşılamadı.** Şarj IC'si 4,20 V'ta sabitlerken ölçülen gerilim
   4140 mV'ta takıldı; deney son satırdan sonra 2 saat daha bekleyip
   `CHARGE_STAGE_TIMEOUT` ile bitti. Haritanın üst ucu bu yüzden 4140 mV'ta kesiliyor.
5. **Yüzde ekseni doluluk değil.** `voltage_pct`, `100 × (V − 3,000) / (4,200 − 3,000)`
   ile hesaplanan doğrusal bir **gerilim indeksidir**. Üreticinin kapasite eğrisi
   değildir; gerçek SoC ile karıştırma.
6. **Tek hücre, tek koşu.** Oda sıcaklığında, ~0,5C şarjla alınmış tek bir ölçüm
   serisidir. Sıcaklık, şarj akımı ve hücre yaşı bu eğriyi kaydırır.
7. **Yük altındaki davranış ölçülmedi.** Düzenekte bataryaya yük bağlayıp kesecek bir
   anahtar yok; yalnızca şarj açılıp kapatılıyor. Deşarj eğrisi bu veriden çıkarılamaz.

## Grafikleri yeniden üretmek

```bash
python -m venv .venv
.venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/plot_voltage.py
```

`graphs/voltage_overlay-light.png`, `-dark.png`, `voltage_overlay.svg` ve
`data/lookup.csv` yeniden yazılır.
