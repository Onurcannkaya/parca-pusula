<div align="center">
  <img src="https://via.placeholder.com/150/1E1E1E/FFB300?text=ParcaPusula" alt="Parça Pusula Logo" width="120" />
  <h1>Parça Pusula ⚙️</h1>
  <p><strong>Türkiye'nin En Agresif ve Hızlı Yedek Parça Tarama Motoru.</strong></p>
  
  [![Vercel Deployment](https://img.shields.io/badge/Deployed_on-Vercel-black?logo=vercel)](https://vercel.com/)
  [![FastAPI](https://img.shields.io/badge/Backend-FastAPI-009688?logo=fastapi)](https://fastapi.tiangolo.com/)
  [![License](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)
</div>

---

## ⚡ Nedir Bu Parça Pusula?

**ParçaPusula**, arabanızın bozulan o can sıkıcı parçasını internetteki onlarca farklı yedek parça sitesinde (N11, Hepsiburada, Sahibinden, ParçaDeposu vb.) **aynı anda** saniyeler içinde arayan ve en ucuz fiyatı bulup önünüze getiren gelişmiş bir veri madenciliği (web scraping) motorudur.

Standart bot korumalarına (WAF, Cloudflare) takılmaz; çünkü Chrome tarayıcılarının kimliklerini **birebir taklit eden** gizlilik (stealth) katmanlarına sahiptir.

## 🚀 Ana Özellikler

- **🛡️ 3 Katmanlı Anti-Bot Zırhı:**
  Siteler bot olduğunuzu anladığında sistem anında `curl_cffi` üzerinden tam teşekküllü bir Google Chrome (v120) gibi davranır. TLS Fingerprinting, dinamik başlıklar (headers) ve rastgele gecikmeler (jitter) ile savunmaları aşar.
- **⚡ Eşzamanlı (Concurrent) Tarama:**
  Tüm yedek parça siteleri sırayla değil, `asyncio.gather()` sayesinde **aynı anda** taranır. En hızlı siteyle aynı sürede hepsi taranmış olur; Serverless sistemlerde saniye başı tasarruf eder.
- **🎯 Fallback Regex (Görünmez Veri Avcısı):**
  Satıcılar kodları gizlese bile, sistem o sayfanın içindeki fiyat etiketlerini (₺ / TL) ve çevresindeki resimleri (`data-src`, `srcset`) yapay zeka keskinliğiyle tarayarak bulur.
- **💎 Dark Industrial Elegance UI:**
  Cam efektli, karanlık mod destekli ve harika animasyonlara sahip "Premium" Frontend vitrini.
- **✨ Akıllı Fallback Placeholder:**
  Satıcı ürüne fotoğraf eklememiş mi? Sorun değil! Tasarımcı tarafından özel üretilmiş `#1E1E1E` karanlık-sarı "Görsel Yok" şablonumuz devreye girer.

## 🛠️ Kurulum ve Çalıştırma

Local (yerel) ortamınızda bu şaheseri test etmek çok kolay:

1. **Repoyu Klonlayın:**
   ```bash
   git clone https://github.com/Onurcannkaya/parca-pusula.git
   cd parca-pusula
   ```

2. **Gereksinimleri Yükleyin:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Geliştirici Sunucusunu Başlatın:**
   ```bash
   python -m uvicorn api.index:app --port 8888 --reload
   ```

4. Tarayıcınızda [http://localhost:8888](http://localhost:8888) adresine gidin ve avlanmaya başlayın!

## 🧩 Mimari

- **Frontend:** Vanilla JavaScript, HTML5, CSS3, Google Fonts (Orbitron & Inter).
- **Backend:** Python 3.9+, FastAPI, `asyncio`
- **Scraping Core:** `curl_cffi` (TLS Bypass), `httpx` (HTTP/2 Fallback), `BeautifulSoup4` (DOM Ayrıştırma), İleri Düzey `re` (Regex).
- **Hosting:** Vercel (Serverless Edge Functions) için %100 uyumludur. Gelişmiş hafıza sızıntısı ve 10s Time-out korumaları inşa edilmiştir.

## 👨‍💻 Geliştirici

Bu proje, kodlara ruh katan geliştirici **Onurcan KAYA** tarafından bir Başyapıt (Masterpiece) olarak tasarlanmıştır.

---
_"Hata bulduğunuzda veya site blokemi aşmanız gerektiğinde kodların arasındaki sanat eserlerine göz atın."_
