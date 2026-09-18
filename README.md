# Power-Xtra PX103049 — şarj / dinlenmiş / yük altında gerilim haritası

Power-Xtra **PX103049** (3,7 V nominal, 1500 mAh Li-Po) hücresinde aynı gerilimin
**üç farklı durumda** ne okuduğunun ölçüm verisi:

| Durum | Ne oluyor | Okunan gerilim |
|---|---|---|
| **Şarj olurken** | hücreye akım giriyor | gerçek durumun **üstünde** |
| **Dinlenmiş** | akım yok, 1 dk beklendi | gerçek durum (referans) |
| **Yük altında deşarj olurken** | hücreden akım çıkıyor | gerçek durumun **altında** |

Amacı basit: karakteristiği bilinmeyen bir bataryada okuduğun terminal gerilimi, iç
direnç ve polarizasyon yüzünden akımın yönüne göre kayar. Bu depo o kaymayı tek bir
hücre için her iki yönde ölçülmüş sayılarla verir.

Deponun **çoğu** bu tek PX103049 hücresine ait. Sonradan eklenen ikinci bir hücrenin
(**PX803035**, 800 mAh — farklı model, farklı kapasite) verisi `-800mah` ekli
dosyalarda ayrı durur;
[kendi bölümünde](#power-xtra-px803035--ikinci-hücre-800-mah-18-eylül-2026)
anlatılıyor. İki hücrenin sayıları birleştirilmedi.

## Üç durum üst üste

![Şarjda, dinlenmiş ve yük altında gerilim](graphs/state_overlay-light.png#gh-light-mode-only)
![Şarjda, dinlenmiş ve yük altında gerilim](graphs/state_overlay-dark.png#gh-dark-mode-only)

Ortak eksen **dinlenmiş (açık devre) gerilim** — bataryanın gerçek durumu. Şarj eğrisi
referansın üstünde, yük eğrisi altında kalır; iki taralı bant sapmanın kendisidir.
İşaretçiler ölçülen çiftlerde: şarj yönünde 13, yük yönünde 15 nokta.

> **Soluk turuncu çizgi veri değil.** Bu eksende x zaten dinlenmiş gerilim olduğu için
> o çizgi tanım gereği `y = x`'tir — ölçülmüş bir eğri değil, eksenin kendisi. O yüzden
> ince/soluk çizilir ve legend'de seri olarak yer almaz. Ölçüm bilgisi mavi ve yeşil
> eğrilerde: onların bu çizgiden dikey uzaklığı sapmanın kendisi.

> **Eksen neden terminal gerilimi değil:** her iki koşuda da anahtarlama zaten ölçülen
> terminal geriliminde tetikleniyor. Terminal gerilimine göre çizilirse `charging_mv` ile
> `loaded_mv` eşik çizgisinin kendisine oturur ve iki eğri yapay olarak çakışır —
> grafik hiçbir şey göstermez. Dinlenmiş gerilim, iki koşunun karşılaştırılabildiği
> tek ortak durum değişkenidir.

Kıyasın özeti: **aynı dinlenmiş gerilimde, şarjda okunan ile yük altında okunan
arasında ~180–220 mV fark var.** Akımın yönünü bilmeden terminal gerilimine bakarsan
belirsizliğin bu kadar.

| Dinlenmiş (OCV) | Şarjda okunur | Yük altında okunur | Pencere |
|---:|---:|---:|---:|
| 3300 mV | 3450,2 | 3228,0 | **222,2 mV** |
| 3500 mV | 3642,3 | 3439,4 | **202,9 mV** |
| 3700 mV | 3838,1 | 3639,4 | **198,7 mV** |
| 3850 mV | 3974,0 | 3797,2 | **176,8 mV** |

Ara değerler iki koşunun ölçüm noktaları arasında doğrusal interpolasyonla bulundu;
örtüşen dinlenmiş aralık 3260,8–3883,0 mV.

Sapma simetrik **değil**: şarj yönünde +51…+166 mV, yük yönünde yalnızca −46…−80 mV.
Sebebi akım farkı — şarj ~0,5C (≈790 mA) ile yapıldı, yük ise sabit bir dummy load ve
çok daha küçük akım çekiyor. Sapmanın büyüklüğü akımla ölçeklenir, yönüyle değil.

## Şarj yönü ayrıntısı

![Şarj ve dinlenmiş gerilim](graphs/voltage_overlay-light.png#gh-light-mode-only)
![Şarj ve dinlenmiş gerilim](graphs/voltage_overlay-dark.png#gh-dark-mode-only)

Üst panel iki gerilimi üst üste gösterir; aradaki taralı bant farkın kendisidir.
Alt panel bu farkı ayrıca çizer: sabit akım (CC) boyunca ~140 mV'ta sabit kalıyor,
şarj sabit gerilim (CV) aşamasına geçip akım azaldıkça 51 mV'a kadar kapanıyor.

## Deşarj yönü ayrıntısı

![Yük altında ve toparlanmış gerilim](graphs/discharge_overlay-light.png#gh-light-mode-only)
![Yük altında ve toparlanmış gerilim](graphs/discharge_overlay-dark.png#gh-dark-mode-only)

Yukarıdakinin yük yönündeki eşi: aynı düzen, aynı eksen, ters yön. Bu kez
toparlanmış değer yük altındakinin **üstünde** kalıyor. Alt panelde fark şarj
yönünün tersine davranıyor — boşaldıkça **büyüyor** (−46 → −80 mV), çünkü iç
direnç alt uca doğru artıyor (aşağıda 2,23 kat olarak ölçüldü).

Kesikli çizgi firmware'in boş kabulü (3,00 V); koşu yük altında 2994,6 mV'ta bitti.
Şarj grafiğindeki 4,20 V tavanının karşılığı.

> **İki yön neden ayrı grafik:** eşik ekseninde anahtarlama zaten ölçülen terminal
> geriliminde tetikleniyor, dolayısıyla ortak eşiklerde `charging_mv` ile `loaded_mv`
> 3–20 mV içinde çakışıyor. Üst üste konsa iki eğri birbirini örter ve hiçbir şey
> göstermez. Üçünü birlikte görmek için yukarıdaki
> [üç durum grafiği](#üç-durum-üst-üste) var — onun ekseni dinlenmiş gerilim.

## Ölçüm düzeneği

| Parça | Rol |
|---|---|
| ESP32-WROOM-32D DevKit | Ölçüm ve anahtar kontrolü |
| TPS22919 yük anahtarı | Hattı açıp kapatır (GPIO4, HIGH = açık) |
| 10 kΩ + 10 kΩ gerilim bölücü | Batarya gerilimini ikiye böler, orta nokta ADC girişine |
| Power-Xtra PX103049 | Ölçülen hücre, 3,7 V / 1500 mAh Li-Po (hücre etiketi) |

Aynı anahtar iki yönde de kullanıldı: **şarj koşularında** şarj hattını, **deşarj
koşusunda** bir sabit dummy load'u bağlayıp kesiyor. Ölçüm mantığı birebir aynı,
değişen tek şey anahtarın ucundaki yük.

Ölçüm akışı: her saniye 32 ADC örneğinin ortalaması alınır. Terminal gerilimi bir
sonraki %5 eşiğini en az 5 saniye aşınca (şarjda yukarı, yükte aşağı) o an
`charging_mv` / `loaded_mv` olarak kaydedilir ve anahtar kapatılır. Anahtar 60 saniye
kapalı kalır; süre sonunda okunan değer `rested_mv` / `recovered_mv` olur, çift
tamamlanır ve anahtar yeniden açılır. Dinlenme boyunca 5, 10, 15, 20, 30, 40 ve 50.
saniyelerde de ara ölçüm alınır (`relax_mv`) — gerilimin oturup oturmadığı bu
sütundan görülür.

Ölçümü yapan firmware ayrı bir depodadır: `tps22919_switch_test`.

Veri cihazdan `DUMP` komutuyla, seri porttan (COM4, 115200 8N1) olduğu gibi alındı.
Port DTR/RTS asserted edilmeden açılıyor — aksi halde ESP32 resetlenir ve firmware
koşuyu reset sonrası sürdürmediği için o koşu ölür.

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
| [`data/measurements-run2.csv`](data/measurements-run2.csv) | İkinci koşunun ölçüm çiftleri (devam ediyor) |
| [`data/raw_dump-run2.log`](data/raw_dump-run2.log) | İkinci koşunun ham seri port çıktısı |
| [`data/measurements-run2b.csv`](data/measurements-run2b.csv) | Devam segmenti, eşik %70–85 |
| [`data/raw_dump-run2b.log`](data/raw_dump-run2b.log) | Devam segmentinin ham çıktısı |
| [`data/predicted-run2.csv`](data/predicted-run2.csv) | **Tahmin** (%90, %95) — ölçüm değil |
| [`data/measurements-discharge.csv`](data/measurements-discharge.csv) | Deşarj koşusunun 15 ölçüm çifti (yük yönü) |
| [`data/raw_dump-discharge.log`](data/raw_dump-discharge.log) | Deşarj koşusunun ham seri port çıktısı |
| [`data/lookup-discharge.csv`](data/lookup-discharge.csv) | 10 mV adımlı arama tablosu — yük altındaki gerilimden dinlenmiş karşılığı |
| [`scripts/plot_voltage.py`](scripts/plot_voltage.py) | Grafikleri ve arama tablolarını üretir — bu hücrenin çıktıları için `px103049` branch'i ([nasıl](#kodu-çalıştırmak)) |

Deşarj koşusunun CSV kolonları şarj koşusundan farklı adlandırılır: `load_elapsed_ms`,
`total_load_ms`, `loaded_mv`, `recovered_mv`. Karşılıkları sırasıyla
`charge_elapsed_ms`, `total_charge_ms`, `charging_mv`, `rested_mv`.

İki arama tablosu da yalnızca **ölçülen aralığı** doldurur, dışına **ekstrapolasyon
yapılmaz**; ara değerler parça-parça doğrusaldır:

| Tablo | Girdi aralığı | Ne verir |
|---|---|---|
| [`lookup.csv`](data/lookup.csv) | 3430–4140 mV (şarjda okunan) | dinlenmiş karşılığı |
| [`lookup-discharge.csv`](data/lookup-discharge.csv) | 3000–3830 mV (yük altında okunan) | dinlenmiş karşılığı |

Hangi tabloyu kullanacağını **akımın yönü** belirler. Şarj ederken `lookup.csv`, yük
çekerken `lookup-discharge.csv`. Yönü bilmiyorsan tek bir sayı veremezsin — yukarıdaki
~180–220 mV'lik pencerenin tamamı olasıdır.

## İkinci ölçüm — 16 Eylül 2026 (devam ediyor)

Aynı hücrede ikinci bir koşu. Düzenek aynı; tek fark ADC girişinin GPIO34 yerine
**GPIO32**'de olması. İlk denemede gerilim bölücüde lehim köprüsü vardı, ADC sabit
142 mV okuyordu; köprü giderilince değer yerine oturdu.

Koşu 3366,8 mV'tan başladı, yani ilk eşik %40. Altı çift alındıktan sonra kart
resetlendi; firmware koşuyu reset sonrası sürdürmediği için ölçüm burada kesildi.
%70 ve üstü eşikler sonraki koşuda toplanıp buraya eklenecek.

| # | Eşik % | Şarjda (mV) | Dinlenmiş (mV) | Fark (mV) | O ana kadar şarj |
|---:|---:|---:|---:|---:|---:|
| 1 | 40 | 3519,1 | 3367,3 | 151,8 | 6 s |
| 2 | 45 | 3556,2 | 3416,7 | 139,6 | 58 s |
| 3 | 50 | 3608,0 | 3460,8 | 147,2 | 2 dk 02 s |
| 4 | 55 | 3673,0 | 3519,4 | 153,6 | 3 dk 44 s |
| 5 | 60 | 3722,7 | 3571,9 | 150,8 | 8 dk 33 s |
| 6 | 65 | 3780,3 | 3632,8 | 147,6 | 15 dk 43 s |

Başlangıç (şarj hiç açılmadan, dinlenmiş): **3366,8 mV**.

### İki koşu birbirini tutuyor mu

Ortak eşiklerde iki bağımsız koşunun şarj gerilimleri birkaç mV içinde örtüşüyor:

| Eşik % | Şarjda run 1 | Şarjda run 2 | Fark | Dinlenmiş run 1 | Dinlenmiş run 2 | Fark |
|---:|---:|---:|---:|---:|---:|---:|
| 45 | 3558,6 | 3556,2 | −2,4 | 3415,9 | 3416,7 | +0,8 |
| 50 | 3606,9 | 3608,0 | +1,1 | 3467,7 | 3460,8 | −6,9 |
| 55 | 3663,9 | 3673,0 | +9,1 | 3519,7 | 3519,4 | −0,3 |
| 60 | 3721,8 | 3722,7 | +0,9 | 3579,5 | 3571,9 | −7,6 |
| 65 | 3784,1 | 3780,3 | −3,8 | 3645,6 | 3632,8 | −12,8 |

Şarj gerilimleri ±9 mV, dinlenmiş gerilimler ±13 mV içinde. Fark (`delta_mv`) run 2'de
ortalama ~8 mV daha yüksek; iki koşu arasında hücre yaşlanması, sıcaklık ve şarj akımı
farkı için beklenen büyüklükte. Haritanın tekrarlanabilir olduğunun doğrudan kanıtı.

### Devam segmenti — eşik %70–85 (ölçülmüş)

USB bağlantısı koptuğu için ikinci ölçüm parça parça toplandı; firmware koşuyu reset
sonrası sürdürmediğinden her kopma o anki koşuyu bitiriyor. Bu segment 3754,3 mV
baseline ile başladı ve üst ucu kapattı.

| # | Eşik % | Şarjda (mV) | Dinlenmiş (mV) | Fark (mV) |
|---:|---:|---:|---:|---:|
| 1 | 70 | 3891,5 | 3752,1 | 139,4 |
| 2 | 75 | 3903,2 | 3756,5 | 146,8 |
| 3 | 80 | 3961,8 | 3824,2 | 137,6 |
| 4 | 85 | 4020,7 | 3890,1 | 130,6 |

İki segment birlikte %40–85 aralığını kesintisiz kapsıyor.

### Tahmin — eşik %90 ve %95 (ÖLÇÜM DEĞİL)

> **Uyarı:** Aşağıdaki iki satır ölçülmedi, hesaplandı. Ölçüm dosyalarına
> karıştırılmadı; ayrı olarak [`data/predicted-run2.csv`](data/predicted-run2.csv)
> içinde, her satırda `source=predicted` sütunuyla duruyor. Gerçek değerler
> ölçüldüğünde bu bölüm onlarla değiştirilecek.

Yöntem: iki koşunun **ortak 10 eşiğinde** `delta_mv` farkı karşılaştırıldı. Run 2,
run 1'e göre ortalama **+9,2 mV** daha yüksek fark veriyor (standart sapma 7,3 mV).
Tahmin, run 1'in aynı eşikteki ölçümüne bu sapmanın eklenmesiyle üretildi.

| Eşik % | Şarjda (mV) | Tahmini dinlenmiş (mV) | Tahmini fark (mV) | Belirsizlik |
|---:|---:|---:|---:|---:|
| 90 | 4081,5 | ~3990,6 | ~90,9 | ±7,3 |
| 95 | 4140,1 | ~4080,1 | ~60,1 | ±7,3 |

Belirsizlik sapmanın standart sapmasıdır; ölçüm hatası değildir. Sapma eşikle birlikte
büyüyor gibi görünüyor (%70'te +1,3 iken %85'te +17,8), yani üst uçta gerçek değerler
tahminin bir miktar altında kalabilir.

**%100 için tahmin üretilmedi.** Run 1 oraya hiç ulaşamadı, şarj 4140 mV'ta takılıp
`CHARGE_STAGE_TIMEOUT` ile bitti — dayanak noktası yok.

## Yük altında deşarj — 15 çift (ölçülmüş)

Aynı hücrede, aynı düzenekle, bu kez **yük yönünde** tam bir koşu. Anahtarın ucundaki
şarj hattı yerine sabit bir dummy load var; mantık aynı, eşikler aşağı doğru
tarandı. Koşu `state=DONE` ile temiz bitti — eşik %70'ten %0'a kadar 15 çiftin
tamamı alındı. Veri cihazdan 17 Eylül 2026'da `DUMP` ile çekildi.

Başlangıç (yük hiç bağlanmadan, dinlenmiş): **3887,2 mV**.
Toplam yük altında geçen süre: **2 sa 17 dk**, koşunun tamamı 2 sa 33 dk.

`delta_mv` bu koşuda **negatif** — yük altındaki gerilim dinlenmişin altında.

| # | Eşik % | Yük altında (mV) | Dinlenmiş (mV) | Fark (mV) | O ana kadar yük |
|---:|---:|---:|---:|---:|---:|
| 1 | 70 | 3837,2 | 3883,0 | −45,8 | 10 s |
| 2 | 65 | 3778,5 | 3834,6 | −56,1 | 25 dk 20 s |
| 3 | 60 | 3719,1 | 3774,0 | −54,9 | 46 dk 24 s |
| 4 | 55 | 3659,6 | 3719,5 | −59,9 | 59 dk 01 s |
| 5 | 50 | 3599,9 | 3661,7 | −61,8 | 1 sa 11 dk |
| 6 | 45 | 3538,9 | 3595,5 | −56,6 | 1 sa 26 dk |
| 7 | 40 | 3478,4 | 3531,3 | −52,9 | 1 sa 43 dk |
| 8 | 35 | 3419,1 | 3483,7 | −64,6 | 1 sa 57 dk |
| 9 | 30 | 3359,1 | 3421,7 | −62,6 | 2 sa 03 dk |
| 10 | 25 | 3298,6 | 3363,4 | −64,8 | 2 sa 07 dk |
| 11 | 20 | 3235,6 | 3308,4 | −72,8 | 2 sa 10 dk |
| 12 | 15 | 3177,9 | 3244,9 | −67,0 | 2 sa 12 dk |
| 13 | 10 | 3114,8 | 3187,6 | −72,8 | 2 sa 14 dk |
| 14 | 5 | 3055,2 | 3131,9 | −76,7 | 2 sa 16 dk |
| 15 | 0 | 2994,6 | 3074,2 | −79,6 | 2 sa 17 dk |

### Deşarj verisi tutarlı mı

- **Sapma boşaldıkça büyüyor.** Üst uçta −45,8 mV, alt uçta −79,6 mV. Yük sabit
  dirençse akım gerilimle birlikte **azalır**, yani sapmanın büyümesi yalnızca iç
  direncin artmasıyla açıklanabilir. Sabit direnç varsayımıyla akım
  `I ∝ V_yük` olduğundan `R_iç ∝ |sapma| / V_yük`: bu oran %70'te 11,92 iken %0'da
  26,57 — **iç direnç alt uca doğru 2,23 kat artıyor.** Li-Po'da beklenen davranış ve
  yükün direnç değerini bilmeyi gerektirmeyen bir kontrol.
- **İlk satır fizik testini geçiyor.** Yalnızca 10 saniye yük sonrası dinlenmiş
  gerilim 3883,0 mV — başlangıçtaki 3887,2 mV'un sadece 4,2 mV altında. Neredeyse hiç
  enerji çıkmadığı için doğru sonuç. (Şarj koşusundaki aynı testin aynası.)
- **İç tutarlılık temiz.** Dinlenmiş gerilim her satırda monoton azalıyor, her satırda
  `loaded < recovered`, `threshold_pct` ölçülen gerilimle birebir uyuşuyor, dinlenme
  süresi her satırda 61000 ms ve 30 gerilim değerinin tamamı ADC'nin 0,0625 mV
  (= 2/32) ızgarasına oturuyor.
- **Bu koşunun yük akımı sonradan belirlendi.** Üçüncü kartta dummy load
  multimetreyle 12,2 Ω olarak ölçüldü ve **aynı eşikte** (%70) yeni bir çift alındı.
  Aynı hücre, aynı eşik, dolayısıyla aynı iç direnç — sapma oranı doğrudan akım
  oranıdır ve iç direnç sadeleşir:

  ```
  sapma_eski / sapma_yeni = 45,75 / 100,50 = 0,455
  I_yeni = 3839,12 mV / 12,2 Ω           = 315 mA
  I_eski = 315 mA × 0,455                = 143 mA   (≈0,10C)
  R_load(eski) = 3837,25 mV / 143 mA     ≈ 26,8 Ω
  ```

  Bu çıkarım yalnızca 12,2 Ω'a dayanır; bir OCV→SoC eğrisi veya kapasite varsayımı
  kullanmaz. 143 mA, 1500 mAh üzerinden ≈0,10C eder.

  Şarj akımıyla kıyas burada tutmuyor: kapasiteden türetilen ~790 mA'in beşte biri
  kadar bir yük akımı, sapmalarda da beşte bir beklerdi. Oysa sapmalar şarjda 140 mV,
  yükte 46–80 mV — yalnızca 2–3 kat. Tutarsızlığın kaynağı büyük olasılıkla ~790 mA'in
  kendisi; o sayı ölçüm değil, etiket kapasitesinden türetilmiş
  ([sınır 8](#sınırlar--bunları-bilmeden-kullanma)).

### Deşarj koşusunun kendi sınırları

1. **Bu koşu sırasında yükün direnci kaydedilmedi.** Yukarıdaki 143 mA ve 26,8 Ω,
   sonradan ölçülen 12,2 Ω ile aynı eşikte alınan bir çiftten çıkarıldı; yalnızca
   o dirence dayanır, kapasite varsayımı içermez. Direncin *oranı* (2,23×) bundan
   da bağımsızdır. Dummy load artık firmware'e yazılı, yani yeni koşularda akım
   doğrudan `loaded_mv / 12,2` ile biliniyor.
2. **Dört çift 60 saniyede oturmamıştı.** 50. ile 60. saniye arasındaki değişim
   eşik %55'te 5,88 mV, %20'de 5,13 mV, %15'te 3,07 mV ve %0'da 2,38 mV — 2 mV
   eşiğinin üstünde. Bu satırlardaki **dinlenmiş değerler bir miktar düşük**;
   gerçek açık devre gerilimi biraz daha yukarıda.
3. **Toparlanma şarjın aynası değil.** Yük kesildikten sonra gerilim *yukarı*
   toparlanıyor, şarj kesildikten sonra *aşağı* oturuyor. `relax_mv` sütunlarının
   yönü bu yüzden iki koşuda terstir; karşılaştırırken karıştırma.
4. **Eşik %0, hücre boş demek değil.** %0 yalnızca gerilim indeksinin tabanı
   (3000 mV) anlamına gelir ve o an **yük altında** okunmuştur; dinlenmiş karşılığı
   3074,2 mV'tur. Hücre kesme gerilimine kadar boşaltılmadı.

## Veri gerçekten tutarlı mı

Sayıların fiziksel olarak anlamlı olup olmadığını birkaç bağımsız yoldan kontrol ettim:

- **Fark profili beklendiği gibi.** CC aşamasında 6.–9. satırlarda 138–144 mV ile
  sabit; CV'ye geçişte 113 → 82 → 51 mV'a düşüyor. Akım azaldıkça IR düşüşünün
  azalması tam olarak olması gereken şey.
- **İma edilen şarj akımı CC bölgesinde sabit.** Ardışık `rested_mv` değerlerini genel
  bir Li-Po OCV→SoC eğrisinden geçirip **1500 mAh** üzerinden hesaplayınca 6.–10.
  satırlarda 695 / 959 / 725 / 732 / 838 mA çıkıyor — ortalama ~790 mA (≈0,5C).
  Sonrasında 420 → 226 → 97 mA ile düzgün bir CV kuyruğu. Beş bağımsız adımdan
  aynı akımın çıkması verinin gerçekliğinin en güçlü işareti.

  > Bu akımlar kapasiteden **türetilmiştir**, o yüzden C-oranı kapasiteyle birlikte
  > ölçeklenmez: 800 mAh varsayımı ~420 mA verir ve o da ≈0,5C'dir. Kapasite
  > değiştiğinde değişen şey **mutlak akım**, C-oranı değil.
- **İç direnç ölçüldü.** Sonraki kartta dummy load bir multimetreyle 12,2 Ω olarak
  okundu, yani akım artık varsayım değil. Yük altında 3943,81 mV okunurken sapma
  75,75 mV ölçüldü:

  ```
  I    = 3943,81 mV / 12,2 Ω = 323 mA   (≈0,22C)
  R_iç = 75,75 mV / 323 mA   = 234 mΩ   (dinlenmiş ~4,02 V, yani üst uçta)
  ```

  Bu sayı **kapasiteden bağımsızdır** — hücrenin 1500 mAh mi başka bir değer mi
  olduğu onu değiştirmez, ve bu boyutta bir pouch hücre + TPS22919 (~42 mΩ) +
  kablolama için beklenen aralıkta.

  **İkinci yol bununla uyuşmuyor.** Şarj koşusunun CC bölgesinden dolaylı olarak
  çıkan değer 140 mV / 790 mA ≈ **177 mΩ**, yani ölçülenin 0,76 katı. Oysa iç direnç
  boşaldıkça arttığına göre (aşağıda 2,23 kat) orta SoC'de 234 mΩ'un **üstünde**
  beklenirdi — fark ters yönde. Güvenilir olan ölçülen 234 mΩ; 177 mΩ, kapasiteden
  türetilen ~790 mA'e dayanıyor ve o zincirin en zayıf halkası etiket kapasitesi
  ([sınır 8](#sınırlar--bunları-bilmeden-kullanma)).
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
7. **Yük altındaki davranış artık ölçüldü** — ama tek bir yük akımında. Aynı anahtara
   dummy load bağlanarak 15 çift alındı (yukarıdaki
   [deşarj bölümü](#yük-altında-deşarj--15-çift-ölçülmüş)). Sapmanın büyüklüğü akımla
   ölçeklenir, dolayısıyla **farklı bir yükte farklı sayılar** çıkar; bu koşu
   ~0,10C'lik bir yükü temsil eder. Bu koşu sırasında yükün direnci kaydedilmediği
   için mutlak akım değeri çıkarımdır; sonradan ölçülen 12,2 Ω ile aynı eşikte
   alınan bir çift üzerinden belirlendi.
8. **Kapasite etiketten, doğrulanmadı — ve bir tutarsızlık bırakıyor.** PX103049 için
   1500 mAh alındı; ayrı bir deşarj testiyle ölçülmedi. C-oranı ifadelerinin ve
   OCV→SoC üzerinden türetilen şarj akımlarının tamamı buna dayanıyor. **Ölçülen
   gerilimlerin hiçbiri kapasiteye bağlı değil** — etkilenen tek şey türetilen akımlar.

   Tutarsızlık şu: 1500 mAh, CC bölgesinde ~790 mA'lik bir şarj akımı ima ediyor;
   o akımla 140 mV'luk sapmayı açıklamak 177 mΩ iç direnç gerektiriyor. Oysa üst uçta
   **doğrudan ölçülen** iç direnç 234 mΩ ve boşaldıkça artıyor, yani orta SoC'de daha
   da yüksek olmalı. İki sayı ters yönde duruyor. Aynı tutarsızlık yük akımı
   kıyasında da görünüyor (yukarıda). Kapasiteyi ~800–900 mAh almak ikisini de
   uzlaştırırdı, ama bu depo **etiketteki değeri** yazar; çözümü tek bir ölçüm verir:
   hücreyi bilinen bir yükle tam boşaltıp kapasiteyi saymak. O yapılana kadar bu
   deponun **kapasiteden türetilen bütün akımları şüphelidir**; ölçülen gerilimler,
   sapmalar ve 234 mΩ ise değildir.

## Power-Xtra PX803035 — ikinci hücre, 800 mAh (18 Eylül 2026)

Yukarıdaki bütün ölçümler tek bir **PX103049** hücresine ait. Bu bölüm başka bir
hücrenin verisi: **PX803035**, 800 mAh — hem modeli hem kapasitesi farklı. Dosyaları
`-800mah` ekiyle ayrı duruyor, yukarıdaki tablolarla ve grafiklerle
**birleştirilmedi**.

> **İki hücreyi karıştırma.** Aynı eşikteki sayılar doğrudan kıyaslanamaz: hücre
> farklı, yük akımı farklı (143 mA yerine 245–316 mA) ve şarj akımı da farklı.
> Aşağıdaki karşılaştırmalar bu yüzden "iki hücre arasındaki fark" değil, "iki
> koşu arasındaki fark" olarak okunmalı.

Düzenek aynı (ESP32 + TPS22919 + 10 kΩ/10 kΩ bölücü), firmware ise yeni. Değişenler:

| | PX103049 (yukarısı) | PX803035 (bu bölüm) |
|---|---|---|
| Koşu yapısı | üç ayrı koşu (şarj, şarj, deşarj) | **tek koşu, iki faz**: önce deşarj, sonra şarj |
| Yük direnci | koşu sırasında kaydedilmedi, sonradan ölçüldü | firmware'de yazılı, `CONFIG` satırında: **12,20 Ω** |
| Yük akımı | çıkarım (≈143 mA) | **doğrudan hesaplanıyor**: `loaded_mv / 12,2` |
| Üst uç | 4140 mV'ta takıldı, `CHARGE_STAGE_TIMEOUT` | **eşik %100 alındı**, 4200,6 mV |
| Bitiş | biri `FAULT`, biri `DONE` | `state=DONE`, 31 çiftin tamamı |
| `STATUS` alanları | `switch_pin` | `phase`, `load_pin`, `charge_pin` |

Veri cihazdan 18 Eylül 2026'da `DUMP` ile, aynı şekilde (COM4, 115200 8N1,
DTR/RTS asserted edilmeden) çekildi: [`data/raw_dump-800mah.log`](data/raw_dump-800mah.log).

### Üç durum üst üste

![PX803035 — şarjda, dinlenmiş ve yük altında gerilim](graphs/state_overlay-800mah-light.png#gh-light-mode-only)
![PX803035 — şarjda, dinlenmiş ve yük altında gerilim](graphs/state_overlay-800mah-dark.png#gh-dark-mode-only)

Deponun başındaki [üç durum grafiğinin](#üç-durum-üst-üste) bu hücredeki karşılığı,
aynı eksende ve aynı okumayla: ortak eksen **dinlenmiş (açık devre) gerilim**, mavi
eğri şarj yönü, yeşil eğri yük yönü, aradaki soluk turuncu çizgi eksenin kendisi
(`y = x`, ölçüm değil). İşaretçiler ölçülen çiftlerde: şarj yönünde 15, yük yönünde
16 nokta.

Bu hücrede iki koşu tek bir dumpta olduğu için üç durum aynı hücrenin aynı gününden
geliyor — PX103049'da şarj ve deşarj ayrı koşulardı.

### Aynı dinlenmiş gerilimde üç durum

Grafiğin sayı hali. İki fazın örtüştüğü dinlenmiş aralık **3180,1–3925,4 mV**; ara
değerler ölçüm noktaları arasında doğrusal interpolasyonla bulundu.

| Dinlenmiş (OCV) | Şarjda okunur | Yük altında okunur | Pencere |
|---:|---:|---:|---:|
| 3200 mV | 3394,8 | 3106,6 | **288,2** |
| 3250 mV | 3443,0 | 3159,5 | **283,5** |
| 3300 mV | 3506,0 | 3208,9 | **297,1** |
| 3350 mV | 3547,8 | 3256,8 | **291,1** |
| 3400 mV | 3609,5 | 3305,5 | **304,0** |
| 3450 mV | 3671,0 | 3358,5 | **312,5** |
| 3500 mV | 3723,3 | 3407,2 | **316,0** |
| 3550 mV | 3776,9 | 3456,0 | **320,9** |
| 3600 mV | 3842,8 | 3503,2 | **339,6** |
| 3650 mV | 3895,3 | 3549,1 | **346,2** |
| 3700 mV | 3938,4 | 3594,5 | **343,9** |
| 3750 mV | 3979,9 | 3650,4 | **329,6** |
| 3800 mV | 4016,2 | 3704,1 | **312,1** |
| 3850 mV | 4067,5 | 3752,1 | **315,5** |
| 3900 mV | 4109,1 | 3807,8 | **301,2** |

Pencere **283–346 mV**. PX103049'un 177–222 mV'luk penceresinden geniş, ama bu hücrenin
daha kötü olduğu anlamına gelmez: **her iki yönde de akım daha yüksek.** Pencerenin
genişliği akımla ölçeklenir, yönüyle değil.

Ölçülen 31 çiftin kendisi — eşikler, ham gerilimler, süreler ve `relax_mv` ara
noktaları — CSV'lerde:
[`measurements-discharge-800mah.csv`](data/measurements-discharge-800mah.csv) (16 çift,
yük yönü) ve [`measurements-charge-800mah.csv`](data/measurements-charge-800mah.csv)
(15 çift, şarj yönü).

### Koşunun iki fazı

| | Faz 1 — yük altında deşarj | Faz 2 — şarj |
|---|---|---|
| Çift | 16 (eşik %75 → %0) | 15 (eşik %30 → %100) |
| Başlangıç (dinlenmiş) | **3932,69 mV** | **3131,69 mV** |
| Bitiş (dinlenmiş) | 3083,9 mV | 4109,4 mV |
| Akım altında geçen süre | 1 sa 09 dk | 53 dk 49 s |
| Fazın tamamı | 1 sa 26 dk | 1 sa 09 dk |
| Sapma aralığı | −69,2 … −105,8 mV | +91,2 … +250,1 mV |

İki faz arasında hücre 3083,9 mV'tan 3131,69 mV'a toparlandı (47,8 mV); şarj fazı bu
değerden başlıyor.

**Eşik %100 ilk kez alındı.** PX103049 koşusu 4140 mV'ta takılıp zaman aşımıyla
bitmişti; bu koşu 4200,6 mV'ta %100'ü geçti ve dinlenmiş karşılığı 4109,4 mV çıktı.
Şarj yönündeki sapma profili beklendiği gibi: %30–90 arasında 192,6–250,1 mV'ta
gezinip CV aşamasında 158,8 → 91,2 mV'a kapanıyor.

Her iki fazın ilk satırı da fizik testini geçiyor. Yalnızca 6 saniye yükten sonra
toparlanmış gerilim 3925,4 mV — başlangıçtaki 3932,7 mV'un 7,3 mV altında; neredeyse
hiç enerji çıkmamış.

### İç direnç: artık çıkarım değil, ölçüm

Yük direnci koşu boyunca biliniyor, dolayısıyla her satırda akım da biliniyor.
Efektif iç direnç doğrudan çıkıyor:

```
I     = loaded_mv / 12,2 Ω
R_eff = |delta_mv| / I
```

| Eşik % | Toparlanmış (mV) | Akım (mA) | R_eff (mΩ) |
|---:|---:|---:|---:|
| 75 | 3925,4 | 316 | 219 |
| 70 | 3921,2 | 314 | 268 |
| 65 | 3878,2 | 310 | 323 |
| 55 | 3754,7 | 300 | 330 |
| 45 | 3638,4 | 290 | 344 |
| 35 | 3511,3 | 280 | 332 |
| 25 | 3388,0 | 270 | 353 |
| 15 | 3261,1 | 260 | 346 |
| 5 | 3140,1 | 250 | 368 |
| 0 | 3083,9 | 245 | 413 |

Boşaldıkça artıyor: 3878 mV'ta 323 mΩ, 3084 mV'ta 413 mΩ — **1,28 kat**. PX103049
koşusunda aynı eğilim sapma oranından dolaylı olarak 2,23 kat çıkmıştı; bu koşuda
oran doğrudan ölçülüyor ve daha ılımlı.

> **Bu ohmik direnç değil.** `delta_mv` 60 saniyelik dinlenme sonrasına göre
> hesaplanıyor, yani IR düşüşü ile difüzyon polarizasyonu birlikte içinde. "60 s'lik
> efektif DC direnci" demek doğru olur. İlk iki satırın (219 ve 268 mΩ) düşük
> çıkmasının sebebi de bu: yük o satırlarda yalnızca 6 ve 38 saniyedir bağlıydı,
> polarizasyon henüz oturmamıştı.

### Deşarjda çekilen yük

Akım her satırda bilindiği için deşarj fazı aynı zamanda bir kulon sayımıdır. Ardışık
eşikler arasında akımın ortalaması alınıp yük altında geçen süreyle çarpıldı:

| Aralık (dinlenmiş) | Çekilen |
|---|---:|
| 3932,7 → 3878,2 mV | 54,5 mAh |
| 3878,2 → 3703,9 mV | 161,7 mAh |
| 3703,9 → 3388,0 mV | 107,2 mAh |
| 3388,0 → 3083,9 mV | 21,3 mAh |
| **3932,7 → 3083,9 mV** | **345 mAh** |

Ortalama akım 296 mA. Bu sayı yalnızca 12,2 Ω'a dayanır — kapasite varsayımı ya da
OCV→SoC eğrisi içermez.

> **345 mAh etiket değerinin altında, ama bu bir kapasite ölçümü değil.** Koşu tam bir
> deşarj testi değildi: 3932,7 mV açık devre geriliminden başladı (hücre dolu değildi)
> ve 3083,9 mV'ta kesildi (kesme gerilimine kadar boşaltılmadı). Bu pencere tipik bir
> Li-Po'nun kullanılabilir kapasitesinin kabaca %70'ine denk gelir; o kabulle tam
> kapasite ~490 mAh'a çıkar, yani etiketteki 800 mAh'ın epey altında. Kabul bir tahmin
> olduğu için **hücrenin gerçekten 800 mAh olmadığı sonucu çıkarılamaz** — bunu ancak
> tam bir deşarj testi söyler.

### Bu koşunun kendi sınırları

1. **Şarj akımı hâlâ bilinmiyor ve iki tahmin çelişiyor.** Şarj hattında ölçülmüş bir
   direnç yok. Deşarjdan çıkan `R_eff` ile hesaplanınca ~530–740 mA çıkıyor; oysa
   fazın kulon dengesi (53 dk 49 s'de deşarjın aldığından fazlasını geri koyması
   gerekir) bunun iki katına yakın bir akım gerektiriyor. İki yöntem uzlaşmıyor —
   ya efektif direnç yöne göre belirgin biçimde farklı, ya da bu tahminlerden biri
   geçersiz. **Bu koşu şarj akımını belirlemiyor**; şarj hattına da bilinen bir
   direnç konmadan çözülmez.
2. **Çiftlerin çoğu 60 saniyede oturmamış.** 50. ile 60. saniye arasındaki değişim
   2 mV'ı deşarjda 16 satırın 10'unda, şarjda 15 satırın 12'sinde aşıyor (en büyüğü
   şarjda %75 eşiğinde 7,44 mV). Akım yüksek olduğu için polarizasyon da büyük;
   PX103049 koşularından daha fazla satır etkilenmiş. Dolayısıyla **deşarjda
   toparlanmış değerler bir miktar düşük, şarjda dinlenmiş değerler bir miktar
   yüksek** — gerçek pencere yukarıdaki tablodan biraz dar.
3. **ADC kalibre edilmedi.** Kazanç 1,000000, ofset 0,00; mutlak değerlerde ±20–30 mV
   sistematik kayma olabilir. Buna karşılık 279 gerilim değerinin tamamı ADC'nin
   1/16 mV ızgarasına oturuyor, `rest_duration_ms` her satırda 61000 ve 31 çiftin
   hepsi `complete=1`.
4. **Kapasite doğrulanmadı.** 800 mAh bilgisi hücreden geliyor, ayrı bir deşarj
   testiyle ölçülmedi.
5. **Eşik %0 boş demek değil.** Yalnızca gerilim indeksinin tabanı (3000 mV) ve o an
   yük altında okunmuştur; dinlenmiş karşılığı 3083,9 mV.
6. **Tek hücre, tek koşu, tek akım.** Oda sıcaklığında, tek bir yük direnciyle.

### Dosyalar

| Dosya | İçerik |
|---|---|
| [`data/raw_dump-800mah.log`](data/raw_dump-800mah.log) | Cihazdan alınan ham seri port çıktısı, hiç düzenlenmedi |
| [`data/measurements-discharge-800mah.csv`](data/measurements-discharge-800mah.csv) | Faz 1 — yük yönünde 16 ölçüm çifti |
| [`data/measurements-charge-800mah.csv`](data/measurements-charge-800mah.csv) | Faz 2 — şarj yönünde 15 ölçüm çifti |
| [`data/lookup-discharge-800mah.csv`](data/lookup-discharge-800mah.csv) | 10 mV adımlı arama tablosu — yük altındaki gerilimden dinlenmiş karşılığı |
| [`data/lookup-charge-800mah.csv`](data/lookup-charge-800mah.csv) | 10 mV adımlı arama tablosu — şarjdaki gerilimden dinlenmiş karşılığı |
| `graphs/state_overlay-800mah-light.png` / `-dark.png` / `.svg` | Yukarıdaki üç durum grafiği |

CSV'ler ham dump'tan faz faz ayrılmış, sütunları hiç değiştirilmemiş kopyalardır.
Faz 1 firmware'in yük yönündeki adlarını kullanır (`load_elapsed_ms`, `total_load_ms`,
`loaded_mv`, `recovered_mv`), faz 2 şarj yönündekileri (`charge_elapsed_ms`,
`total_charge_ms`, `charging_mv`, `rested_mv`).

Arama tabloları yukarıdakilerle aynı yöntemle üretildi — yalnızca **ölçülen aralığı**
doldururlar, dışına ekstrapolasyon yapılmaz, ara değerler parça-parça doğrusaldır:

| Tablo | Girdi aralığı | Ne verir |
|---|---|---|
| [`lookup-charge-800mah.csv`](data/lookup-charge-800mah.csv) | 3380–4200 mV (şarjda okunan) | dinlenmiş karşılığı |
| [`lookup-discharge-800mah.csv`](data/lookup-discharge-800mah.csv) | 2990–3850 mV (yük altında okunan) | dinlenmiş karşılığı |

**Bu tablolar PX803035'e aittir.** PX103049 için [`lookup.csv`](data/lookup.csv) ve
[`lookup-discharge.csv`](data/lookup-discharge.csv) kullanılır; ikisi birbirinin
yerine geçmez.

## Kodu çalıştırmak

Depoda tek bir script var: [`scripts/plot_voltage.py`](scripts/plot_voltage.py).
Ölçüm CSV'lerini okur, grafikleri ve arama tablolarını yazar. Cihaza, seri porta
veya internete ihtiyacı yok — girdisi `data/` altındaki dosyalar.

### Kurulum

Python 3.10 veya üstü gerekiyor (kod `list[dict]` gibi yeni tip yazımını kullanıyor).
Tek bağımlılık matplotlib.

```bash
python -m venv .venv
.venv/Scripts/activate            # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
```

`uv` kullanıyorsan aynı şey:

```bash
uv venv
uv pip install -r requirements.txt
```

### Çalıştırmak

```bash
python scripts/plot_voltage.py
```

Argüman almaz. Hangi bataryayı işleyeceği script'in başındaki `BATTERY` blokundan
gelir. Ne yaptığını yazdırır — aşağıdaki çıktı `main` branch'inden, yani PX803035
ayarıyla; `px103049` branch'inde aynı komut o hücrenin dosyalarını listeler:

```
Batarya: Power-Xtra PX803035 (3,7 V / 800 mAh Li-Po)
Girdi:   data/measurements-charge-800mah.csv (15 cift), data/measurements-discharge-800mah.csv (16 cift)
Yazilan:
  graphs/state_overlay-800mah-light.png
  graphs/state_overlay-800mah-dark.png
  graphs/state_overlay-800mah.svg
  data/lookup-charge-800mah.csv
  data/lookup-discharge-800mah.csv
```

Listelenen dosyalar **üzerine yazılır**, başkasına dokunulmaz. Çıktı deterministiktir:
veri değişmediyse PNG'ler bayt bayt aynı çıkar. (SVG'ler hariç — matplotlib içlerine
üretim tarihi ve rastgele `clip-path` id'leri koyuyor, o yüzden her koşuda içerikçe
aynı ama baytça farklı olurlar. SVG diff'i görürsen paniğe kapılma.)

Hata alırsan: `... icinde tamamlanmis cift yok` demek, CSV'de `complete=1` olan satır
bulunamadı demektir — dosya yolu yanlış ya da dump yarım kalmış.

### Bu depodaki iki batarya

Depoda iki ayrı hücrenin verisi var ve script **aynı anda yalnızca birini** işler:

| Branch | `BATTERY` ayarı | Ürettikleri |
|---|---|---|
| `main` | **PX803035** (yeni hücre) | `state_overlay-800mah-*`, `lookup-*-800mah.csv` |
| `px103049` | **PX103049** (ilk hücre) | `voltage_overlay-*`, `discharge_overlay-*`, `state_overlay-*`, `lookup.csv`, `lookup-discharge.csv` |

İki branch'te kod **aynı**; tek fark `BATTERY` bloku. Yani PX103049'un grafiklerini
yeniden üretmek istiyorsan:

```bash
git checkout px103049
python scripts/plot_voltage.py
```

Her iki branch de her iki hücrenin **verisini** taşır; ayrılan şey yalnızca script'in
o an neyi işlediği. Bu yüzden `main` üzerinde çalışırken `graphs/voltage_overlay-*.png`
gibi PX103049 dosyaları yerinde durur ama yeniden üretilmez — onları `px103049`
branch'i üretir.

### Başka bir batarya için

Yeni bir hücre eklemek script'in başındaki tek bloğu doldurmaktan ibaret:

```python
BATTERY = dict(
    model="PX803035",
    nominal="3,7 V / 800 mAh Li-Po",

    empty_mv=3000.0,        # firmware'deki BatteryConfig.h ile AYNI olmali
    full_mv=4200.0,

    load_ohms=12.20,        # dummy load'un olculen direnci; bilinmiyorsa None

    charge_csv="measurements-charge-800mah.csv",   # data/ altinda
    load_csv="measurements-discharge-800mah.csv",

    charge_lookup="lookup-charge-800mah.csv",      # data/ altina yazilir
    load_lookup="lookup-discharge-800mah.csv",

    graphs=("state",),
    state_stem="state_overlay-800mah",
    ...
)
```

Sırasıyla:

1. **Dump'ı al.** Cihazdan `DUMP` komutuyla, seri porttan (COM4, 115200 8N1). Portu
   **DTR/RTS asserted etmeden** aç — aksi halde ESP32 resetlenir ve firmware koşuyu
   reset sonrası sürdürmediği için o koşu ölür. Çıktıyı olduğu gibi
   `data/raw_dump-<hücre>.log` olarak kaydet, düzenleme.
2. **Fazları CSV'ye ayır.** Log'daki `# PHASE,...` satırlarından sonra gelen
   `row,...` başlığı ve satırları olduğu gibi kopyala; sütunları değiştirme. Yük
   yönü `loaded_mv`/`recovered_mv`, şarj yönü `charging_mv`/`rested_mv` kullanır —
   script ikisini de bu adlarla bekliyor.
3. **`BATTERY` bloğunu doldur.** `empty_mv`/`full_mv` firmware'in `CONFIG` satırından,
   `load_ohms` yine `CONFIG` satırındaki `load_ohms` alanından gelir.
4. **Eksen sınırlarını ayarla.** `state_xlim` / `state_ylim` / `state_delta_ylim`
   elle veriliyor; otomatik hesaplanmıyor ki kaydedilmiş grafikler yeniden
   üretildiğinde birebir aynı çıksın. Veri aralığını görmek için bir kez çalıştırıp
   grafiğe bakmak yeterli.
5. **Çalıştır.**

`graphs` alanı hangi grafiklerin çizileceğini söyler. `"state"` (üç durum üst üste)
her batarya için çalışır. `"charge"` ve `"load"` ayrıntı grafiklerinin içindeki
açıklama metinleri PX103049'un sayılarına göre yazılmış (`"sabit akım: ~140 mV"`
gibi), o yüzden başka bir hücrede açmadan önce `render()` ve `render_discharge()`
içindeki `annotate()` çağrılarını güncellemek gerekir.

### Renkler

Her iki tema da aynı doğrulanmış kategorik paletin ilk üç yuvasını kullanır (mavi /
turuncu / aqua); üçü birlikte hem açık hem koyu modda all-pairs kontrast eşiklerini
geçer. Aqua açık yüzeyde 3:1'in altında kaldığı için seriler grafikte doğrudan
etiketlenir, ayrıca sayıları README'deki tablolarda durur.
