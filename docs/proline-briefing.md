# TANIK — Proline görüşmesi için brifing

Ayberk'in Proline'daki biyometri irtibatıyla konuşmaya hazır olması için hazırlanmış özet. İki iş görür: (1) sistemin **dürüst mevcut durumu** — neyin çalıştığı, neyin çalışmadığı; (2) **Türkçe proje brifingi** + **zor sorulara dürüst cevaplar**, detaylı soru geldiğinde buradan cevap verilebilsin diye.

> **Son doğrulama: 2026-07-29.** Canlı sistem durumu redeploy'larla değişir; rakamlar (örn. cold-start süresi) o günkü ölçüme aittir.

---

## 0. Dürüst sistem durumu — "100/100 çalışıyor mu?"

Hayır, o standartta değil. Gerçekler (iyimserlik değil):

- **Health endpoint HTTP 200 döndü ama 42.6 saniye sürdü** — Render uyuyordu, cold-start yaptı. İlk ziyaretçinin gördüğü tam olarak bu 42 sn'lik bekleme.
- **İstemci (Vercel): ayakta, hızlı.** Motorlar: `open-iris/1.11.1`, `sourceafis/3.18.1`, `calibration_status: "placeholder"`.
- **Enroll→verify mutlu yolu uçtan uca hiç doğrulanmadı** — bitmemiş `#33` DoD yürüyüşü. Son denemede iki gerçek hata bulunup düzeltildi ama tam akış o günden beri teyit edilmedi.
- **Kalıcı olmayan veritabanı** — Render free tier her redeploy'da SQLite dosyasını siler. İrtibat enrolle eder, arada redeploy olursa `subject_id`'si uçar.
- **Görsel ışık webcam, NIR değil; kalibrasyon placeholder** — henüz doğruluk rakamı yok.

**İrtibat kendi kendine online bakabilir mi?** URL'ler herkese açık, teknik olarak evet. Ama **soğuk canlı link göndermem** — ilk tıklamada 42 sn donma "bozuk" gibi görünür, prova edilmemiş akış tam da etkilemek istediğin kişinin önünde patlayabilir.

**Bir biyometri mühendisi için daha iyi self-servis materyal: GitHub reposu** (`github.com/Ayberkone/tanik`). Dokümanlar — özellikle `docs/architecture.md` — zaten bir gezinti gibi yazılmış, cold-start yapmaz, çökmez. Bu kitle için repo + dokümanlar UI'dan daha etkileyici. Sonra canlı siteyi göstermek istersen, önce `#33` yürüyüşünü kendin yap ve hemen öncesinde Render'ı ısıt (`/api/v1/health`'e vur).

---

## 1. Proje brifingi (Türkçe)

### Ne bu, neden var
TANIK, bir kullanıcının **irisini ve parmak izini** alıp ikisini **tek bir kimlik kararında birleştiren** (füzyon), açık kaynak, çok-modlu bir biyometrik doğrulama kiosk'u. Havaalanı e-geçiş kapıları, devlet kimlik gişeleri, yüksek güvenlikli tesis girişleri sınıfından. **Amaç yeni araştırma değil**; bir biyometri mühendisinin bir öğleden sonra okuyup "ciddi iş" diyebileceği, dürüst ve iyi belgelenmiş bir **referans sistem**.

### Neden iris + parmak izi (yüz değil)
- **İris:** DNA dışı en yüksek doğruluk; doku detayı kimlik düzeyinde entropi (Daugman 1993'ten beri iyi çalışılmış). Biyometri mühendislerinin en çok saygı duyduğu modalite — **birincil**.
- **Parmak izi:** devasa saha geçmişi, oturmuş ISO standartları (19794-2), bol test verisi. Bağımsız ikinci kanıt — **ikincil**.
- **Yüz: bilerek kapsam dışı.** En yüksek yanlış-kabul oranı, en geniş sunum-saldırısı yüzeyi (basılı foto, ekran replay, deepfake), AB + Türkiye'de düzenleyici baskı. Eklemek "ciddi biyometri" pitch'ini sulandırırdı.

### Mimari — iki servis, tek sözleşme
- **İstemci (Next.js, tarayıcı):** webcam yakalama, katı **capture state machine** (Zustand), modalite bazlı formlar, sonuç panelleri. ML çalıştırmaz.
- **Çıkarım servisi (FastAPI, Python 3.10):** upload doğrulama, iris pipeline, parmak izi pipeline, SQLite (yalnız şablon), füzyon + birleşik verify. UI render etmez.
- Aralarındaki **tek bağ: JSON HTTP API** (`docs/api-contract.md` tek doğruluk kaynağı). Gerçek üretim dağıtımıyla aynı ayrım: kiosk donanımı istemciyi, sağlamlaştırılmış çıkarım kümesi eşleştiricileri çalıştırır.

### İris pipeline (Worldcoin `open-iris`)
1. Yüklenen görüntüyü OpenCV ile gri tonlamalı diziye **çöz**.
2. İris ve göz bebeği sınırlarını **segmente et** (ONNX modeli).
3. Polar (dikdörtgen) "iris şeridine" **normalize et**.
4. Daugman tarzı **Gabor filtreleriyle** ~2.048 bitlik ikili **iris koduna** çevir (+ güvenilmez bitlerin maskesi).
5. İki kod arasında **maskeli kesirli Hamming uzaklığı** hesapla — farklı bit oranı.

Hamming `0.0` → birebir aynı; iki rastgele kod istatistiksel olarak `~0.5`'e yakınsar. **Eşik: `0.37`** (düşük = daha iyi).

### Parmak izi pipeline (SourceAFIS 3.18.1)
Java kütüphanesi; Python'dan **JPype** ile **süreç içinde tek JVM** üzerinden çağrılıyor.
1. **Minutiae** tespit et (çatlak uçları, çatallanmalar) ve yönleri.
2. SourceAFIS'in yerel **CBOR** formatında şablon üret.
3. İki şablonu hizalayıp minutiae uyumunu **skorla** — açık uçlu skor (güçlü eşleşmeler yüzlerce). **Eşik: `40.0`** (SourceAFIS'in FMR=%0.01 belgelenmiş eşiği; yüksek = daha iyi).

### Neden ikisi de threadpool'da
FastAPI async. İris (CPU-yoğun) ve parmak izi (JVM/JNI çağrısı) event loop'u bloklardı. İkisi de işi `run_in_threadpool`'a devrediyor. **"Async" sihirli non-blocking demek değil — CPU işini elle bir thread'e vermen gerekir.**

### Depolama — dürüstlük duruşunun kalbi
- **Ham görüntüler diske asla yazılmaz.** İstek kapsamında bellekte durur, yanıt gidince çöpe alınır. Yalnız **çıkarılan şablonlar** saklanır. Diske yazan hiçbir kod yolu repoda yok — "yokluk"la garanti.
- **Bir özne = bir modalite.** İris + parmak enrolle eden kişi iki ayrı satır (iki `subject_id`) üretir. Çapraz-modalite bağlama Phase 4 işi.
- SQLite (dev) → Postgres (üretim) taşınabilirliği için `metadata_json` düz string kolonu.

### Füzyon (Phase 3'ün en ilginç parçası)
**Problem:** iris Hamming uzaklığı verir (düşük=iyi, `[0,1]`); parmak izi benzerlik skoru verir (yüksek=iyi, açık uçlu). Ortak ölçek lazım.
**Çözüm:** ikisini de `[0,1]`'e, **her modalitenin kendi eşiğine sabitlenmiş** parçalı-doğrusal eğriyle taşı. Güvendiğimiz tek yerel sayı eşik olduğu için çapa o: **yerel eşik → normalize 0.5**. Böylece birleşik karar eşiği `0.5`'in net anlamı olur: *"iki modalite de kendi çalışma noktasında."* Füzyon **ağırlıklı toplam**; ağırlıklar istekte gelen modalitelere göre yeniden normalize edilir (tek modaliteli çağrı temiz çalışır).
**Dürüstlük şerhi:** bugünkü ağırlıklar/tavanlar **placeholder** — ayarlanmadı. Yanıt `calibration_status: "placeholder"` taşır; ölçülü FAR/FRR vaat eden bir alt-sistem placeholder'a göre işlem yapmayı reddedebilsin diye. Gerçek kalibrasyon veri setiyle (`#43`) gelecek.

### Dürüstlük disiplini (asıl kredibilite argümanı)
- **Uydurma FAR/FRR yok.** Ölçülmemiş sayı hiçbir yerde geçmez. "TBD" kabul; "1'de 1.000.000" değil.
- **Liveness'ta abartı yok.** Phase 4 temel bir PAD ekleyecek; "askeri sınıf" değil, temel savunma diye belgelenecek. Gerçek iris-PAD, bu sistemde olmayan NIR donanım özellikleri ister.
- **Doğru gizlilik dili.** Şablonlar KVKK/GDPR kapsamında kişisel veridir. "Zero-knowledge" yanlış çünkü şablonlar *saklanıyor* — görüntü-değil-şablon dili kullanılıyor.
- **Düzgün atıf.** open-iris, SourceAFIS, skor normalizasyonu, füzyon — hepsi kaynak gösterilerek.

### Bugün güçlü / zayıf (dürüst tehdit modeli)
**Güçlü:** yalnız şablon (ham görüntü kalıcı değil); MIME magic-byte doğrulama (header'a güvenmez); Pydantic-katı istek modelleri; sıfır telemetri/analytics.
**Zayıf (ve açıkça kabul ediliyor):** henüz **liveness yok** — enrolle edilmiş bir irisin **basılı fotoğrafı şu an eşleşir**; replay direnci yok; şablonlar dinlenirken şifreli değil (SQLite'ta düz); kimlik doğrulama yok; **1:N kimlik tespiti yok**, sadece 1:1 verify.

### Ne bitti / ne bitmedi
- **Phase 0** (iris spike notebook) ✅ · **Phase 1** (iris backend + istemci) ✅ implementasyon + ✅ deploy, ⏳ DoD yürüyüşü (`#33`) · **Phase 2** (parmak izi) ✅ CI yeşil · **Phase 3** (füzyon/eşik/dürüst metrik) ⏳ — `#41` çıktı, `#42`+`#43` **veri setine bağlı** · **Phase 4** (liveness+admin) ve **Phase 5** (cila+release) ⏳.
- **Faz-kapısı disiplini:** fazlar bir sonraki başlamadan biter. Tarihsel en büyük hata scope-creep; yeni fikirler `BACKLOG.md`'ye gider, aktif faza sızmaz.

---

## 2. Zor sorular gelirse — dürüst cevaplar

| Soru | Cevabın |
|---|---|
| **"Doğruluğu ne? FAR/FRR?"** | "Henüz ölçmedim — dürüstlük gereği uydurmuyorum. Tam da bu yüzden araştırma kalitesinde bir veri seti arıyorum; ölçünce `docs/performance.md`'ye script yazacak, elle girmeyeceğim." |
| **"Liveness var mı? Fotoğrafla kandırılır mı?"** | "v1'de yok, açıkça belgeli. Basılı bir iris fotoğrafı şu an eşleşir. Phase 4 temel bir PAD ekliyor; gerçek iris-PAD NIR donanım özellikleri ister, o referans sistemin kapsamı dışında." |
| **"Neden webcam? Gerçek iris NIR ister."** | "Doğru. Bu referans sistem, dağıtım değil. Görsel ışık zayıf ama pipeline aynı; gerçek dağıtımda `BiometricEngine` arayüzü sayesinde sertifikalı NIR kameraya geçiş tek dosyalık değişiklik." |
| **"Şablondan görüntü geri getirilir mi?"** | "Bu repodaki kodla open-iris şablonundan görüntü yeniden oluşturmak pratik değil. Ama 'matematiksel olarak geri döndürülemez' *demiyorum* — o araştırmaya açık bir konu; savunabildiğim iddia bu." |
| **"İki modaliteyi nasıl birleştiriyorsun?"** | "Skor seviyesinde füzyon. İkisini de her modalitenin eşiğine sabitleyip `[0,1]`'e normalize ediyorum, sonra ağırlıklı toplam. Ağırlıklar şu an placeholder — yanıt bunu `calibration_status` ile açıkça söylüyor." |
| **"Üretime ne kadar uzak?"** | "Referans, dağıtım değil. Eksikler net: sertifikalı donanım, donanım liveness, şifreli şablon deposu (AES-256 + HSM), yatay ölçek, denetim logu. Mimari bu yükseltmelere kasıtlı olarak dostane." |
| **"Neden yüz yok?"** | "En yüksek yanlış-kabul, en geniş sunum-saldırısı yüzeyi, en ağır düzenleyici baskı. Ciddi biyometri pitch'ini sulandırırdı — bilinçli kapsam kararı." |
| **"Şablonlar şifreli mi?"** | "v1'de hayır — SQLite'ta düz. Üretimde AES-256 + HSM-destekli anahtar; bu productionizasyon işi, v1 iddiası değil." |

> Her dürüst cevap veri seti ricasına bağlanıyor — tasarım bu: kabul edeceğin eksikler, ondan istediğin şeyin *gerekçesi*. Domain'e hâkim göründüğün nokta burası, delik saklıyor gibi değil.
