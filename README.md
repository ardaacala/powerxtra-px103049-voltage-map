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
Sebebi akım farkı — şarj ~0,5C (≈750 mA) ile yapıldı, yük ise sabit bir dummy load ve
çok daha küçük akım çekiyor. Sapmanın büyüklüğü akımla ölçeklenir, yönüyle değil.

## Şarj yönü ayrıntısı

![Şarj ve dinlenmiş gerilim](graphs/voltage_overlay-light.png#gh-light-mode-only)
![Şarj ve dinlenmiş gerilim](graphs/voltage_overlay-dark.png#gh-dark-mode-only)

Üst panel iki gerilimi üst üste gösterir; aradaki taralı bant farkın kendisidir.
Alt panel bu farkı ayrıca çizer: sabit akım (CC) boyunca ~140 mV'ta sabit kalıyor,
şarj sabit gerilim (CV) aşamasına geçip akım azaldıkça 51 mV'a kadar kapanıyor.

## Ölçüm düzeneği

| Parça | Rol |
|---|---|
| ESP32-WROOM-32D DevKit | Ölçüm ve anahtar kontrolü |
| TPS22919 yük anahtarı | Hattı açıp kapatır (GPIO4, HIGH = açık) |
| 10 kΩ + 10 kΩ gerilim bölücü | Batarya gerilimini ikiye böler, orta nokta ADC girişine |
| Power-Xtra PX103049 | Ölçülen hücre, 3,7 V / 1500 mAh Li-Po |

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
| [`scripts/plot_voltage.py`](scripts/plot_voltage.py) | Grafikleri ve arama tablolarını üretir |

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
- **İki yön birbiriyle uyumlu.** Şarj koşusundan çıkan iç direnç ~187 mΩ. Bu değer üst
  uçta da geçerliyse yukarıdaki orandan dummy load ≈ 15,7 Ω ve yük akımı ≈ 244 mA
  (≈0,16C) çıkar. Şarj akımının (~750 mA) kabaca üçte biri — sapmaların da kabaca
  üçte bir olmasıyla (140 mV'a karşı 46–80 mV) tutarlı. *Bu bir çıkarım; yükün direnci
  ölçülüp kaydedilmedi.*

### Deşarj koşusunun kendi sınırları

1. **Yükün direnci kaydedilmedi.** Dolayısıyla yük akımı ve iç direnç **mutlak**
   olarak verilemez; yukarıdaki 244 mA ve 15,7 Ω yalnızca şarj koşusunun iç direncine
   dayanan bir çıkarımdır. Direncin *oranı* (2,23×) bu varsayımdan bağımsızdır.
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
7. **Yük altındaki davranış artık ölçüldü** — ama tek bir yük akımında. Aynı anahtara
   dummy load bağlanarak 15 çift alındı (yukarıdaki
   [deşarj bölümü](#yük-altında-deşarj--15-çift-ölçülmüş)). Sapmanın büyüklüğü akımla
   ölçeklenir, dolayısıyla **farklı bir yükte farklı sayılar** çıkar; bu koşu
   ~0,16C'lik bir yükü temsil eder. Yükün direnci kaydedilmediği için mutlak akım
   değeri de çıkarımdır.

## Grafikleri yeniden üretmek

```bash
python -m venv .venv
.venv/Scripts/activate      # Linux/macOS: source .venv/bin/activate
pip install -r requirements.txt
python scripts/plot_voltage.py
```

Şu dosyalar yeniden yazılır:

```
graphs/voltage_overlay-light.png    graphs/state_overlay-light.png
graphs/voltage_overlay-dark.png     graphs/state_overlay-dark.png
graphs/voltage_overlay.svg          graphs/state_overlay.svg
data/lookup.csv                     data/lookup-discharge.csv
```

Grafikler `data/measurements.csv` (şarj) ve `data/measurements-discharge.csv` (yük)
dosyalarından üretilir; her iki tema da aynı doğrulanmış kategorik paletin ilk üç
yuvasını kullanır.
