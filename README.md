# 🔩 ParçaPusula — Anlık Yedek Parça Fiyat Karşılaştırıcı

> **Industrial Pro** temalı, Flet + Playwright ile çalışan, asenkron,
> serverless masaüstü uygulaması.

---

## ⚙️ Kurulum

```bash
# 1. Bağımlılıkları yükle
pip install -r requirements.txt

# 2. Playwright tarayıcı ikili dosyasını indir (tek seferlik)
playwright install chromium

# 3. Uygulamayı başlat
python main.py
```

---

## 🗂 Dosya Yapısı

```
parca_pusula/
├── main.py          # Flet arayüzü (UI katmanı)
├── scraper.py       # Playwright scraping motoru
├── requirements.txt
└── README.md
```

---

## 🔧 Yeni Site Ekleme

`scraper.py` içindeki `SITES` listesine yeni bir `SiteConfig` kaydı ekleyin:

```python
SiteConfig(
    name            = "YeniSite",
    base_search_url = "https://www.yenisite.com/arama?q={query}",
    result_item_sel = ".product-card:first-child",   # DevTools ile bulun
    title_sel       = ".product-title",
    price_sel       = ".price",
    timeout_ms      = 12_000,
),
```

> **{query}** yer tutucusu otomatik olarak kullanıcının girdiği arama terimiyle değiştirilir.

---

## 🏗 Mimari

```
Kullanıcı Girişi
     │
     ▼
  main.py (Flet UI)
     │  asyncio.ensure_future(do_search())
     ▼
scraper.py → ScraperEngine.search_all(query)
     │  asyncio.gather(*tasks)       ← concurrent
     ├──► Site 1: Playwright Context → _scrape_one()
     ├──► Site 2: Playwright Context → _scrape_one()
     └──► Site 3: Playwright Context → _scrape_one()
     │
     ▼
  [SearchResult, SearchResult, SearchResult]
     │
     ▼
  main.py → build_result_row() → Flet UI güncelle
```

### Hata Yönetimi
- Her site **ayrı bir Playwright browser context**'inde çalışır → birinin çökmesi diğerlerini etkilemez.
- `PWTimeout` → "Zaman aşımı" mesajı
- Diğer tüm istisnalar → "Erişilemedi: <ExceptionType>" mesajı
- Uygulama hiçbir koşulda tamamen durmaz.

---

## 🎨 Tema Renkleri

| Rol           | Hex       |
|---------------|-----------|
| Arka plan     | `#1A1A1A` |
| Kart          | `#242424` |
| Yüzey         | `#2E2E2E` |
| Turuncu aksan | `#FF6B00` |
| Beyaz metin   | `#F0F0F0` |
| En ucuz yeşil | `#00C851` |
| Hata kırmızı  | `#FF4444` |
