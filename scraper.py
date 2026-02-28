import asyncio
import httpx
import re
import random
import urllib.parse
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional

# ── Katman 1 (curl_cffi) İçin Savunma Hattı ──
try:
    from curl_cffi.requests import AsyncSession
    CURL_CFFI_AVAILABLE = True
except ImportError:
    print("[SYSTEM] UYARI: curl_cffi yüklenemedi. Katman 1 devre dışı, HTTPX/ScraperAPI fallbacks aktif.")
    CURL_CFFI_AVAILABLE = False
except Exception as e:
    print(f"[SYSTEM] UYARI: curl_cffi başlatma hatası: {e}")
    CURL_CFFI_AVAILABLE = False

# ─────────────────────────── Veri Modelleri ──────────────────────────
@dataclass
class SearchResult:
    site_name    : str
    success      : bool
    part_name    : str         = ""
    price_str    : str         = ""
    price_numeric: Optional[float] = None
    url          : str         = ""
    error_msg    : str         = ""
    affiliate_url: str         = ""
    engine       : str         = "Stealth"
    image_url    : str         = ""

@dataclass
class SiteConfig:
    name           : str
    base_search_url: str
    result_item_sel: str
    title_sel      : str
    price_sel      : str
    image_sel      : str       = ""
    timeout_ms     : int = 15_000

# ─────────────────────────── Site Tanımları ──────────────────────────
SITES: list[SiteConfig] = [
    SiteConfig(
        name            = "OnlineYedekParca",
        base_search_url = "https://www.onlineyedekparca.com/arama/{query}",
        result_item_sel = "div.showcase, div.ProductItem, div.product-item, div.product-card, div.card",
        title_sel       = "div.showcase-title a, div.productName a, div.product-title a, h3.name, a.title, div.product-name a, h3.product-name a",
        price_sel       = "div.showcase-price span, div.discountPrice span, div.product-price span, span.price, div.price, div.current-price, span.current-price",
        image_sel       = "img.product-image, img.lazy, img",
        timeout_ms      = 8000
    ),
    SiteConfig(
        name="AlloYedekParca",
        base_search_url="https://www.aloparca.com/arama/{query}",
        result_item_sel=".product-item, .product-card",
        title_sel="a.product-name, h3.product-title a",
        price_sel=".product-price, .price",
        image_sel="img.product-image, img",
        timeout_ms=8000
    ),
    SiteConfig(
        name="ParcaDeposu",
        base_search_url="https://www.otoparcadeposu.com/arama?q={query}",
        result_item_sel=".showcase",
        title_sel=".showcase-title a",
        price_sel=".showcase-price-new",
        image_sel=".showcase-image img.lazy, .showcase-image img",
        timeout_ms=8000
    ),
    SiteConfig(
        name            = "n11",
        base_search_url = "https://www.n11.com/arama?q={query}",
        result_item_sel = "li.column, div.pro, ul.list-ul li, div.listView ul li, li.catalog-item, div.product-item",
        title_sel       = "h3.productName, a.proName, h3.name, h3[class*='title'], h3",
        price_sel       = "ins, span.newPrice c, div.priceContainer ins, div.price span, span.new-price",
        image_sel       = "div.imgBox img.lazy, div.proDetail img, img",
        timeout_ms      = 8000
    ),
    SiteConfig(
        name            = "Hepsiburada",
        base_search_url = "https://www.hepsiburada.com/ara?q={query}",
        result_item_sel = "li.productListContent-item, ul.productList li, div[data-test-id='product-card'], div.product-card",
        title_sel       = "h3[data-test-id='product-card-name'], h3, div.product-title",
        price_sel       = "div[data-test-id='price-current-price'], span.price, div.price-value, span.price-current-price",
        image_sel       = "img[data-test-id='product-image'], img",
        timeout_ms      = 8000
    ),
    SiteConfig(
        name            = "Sahibinden",
        base_search_url = "https://www.sahibinden.com/kelime-ile-arama?query_text={query}",
        result_item_sel = "tr.searchResultsItem, div.list-item",
        title_sel       = "a.classifiedTitle, h3.title",
        price_sel       = "td.searchResultsPriceValue div, span.price",
        image_sel       = "td.searchResultsLargeThumbnail img, img",
        timeout_ms      = 8000
    ),
]

# ─────────────────────────── Yardımcı Fonksiyonlar ───────────────────
_PRICE_PATTERN = re.compile(r"[\d.,]+")

def parse_price(raw: str) -> Optional[float]:
    raw = raw.strip()
    m = _PRICE_PATTERN.search(raw)
    if not m:
        return None
    num_str = m.group()
    if "," in num_str and "." in num_str:
        num_str = num_str.replace(".", "").replace(",", ".")
    elif "," in num_str:
        num_str = num_str.replace(",", ".")
    try:
        return float(num_str)
    except ValueError:
        return None

def generate_affiliate_url(original_url: str) -> str:
    """Satın Alma butonu için yönlendirme (Affiliate marketing)"""
    if "?" in original_url:
        return f"{original_url}&ref=onurcan"
    return f"{original_url}?ref=onurcan"

def safe_select(element: BeautifulSoup, selectors: str) -> Optional[BeautifulSoup]:
    for sel in selectors.split(","):
        sel = sel.strip()
        found = element.select_one(sel)
        if found:
            return found
    return None

def safe_select_all(element: BeautifulSoup, selectors: str) -> list:
    for sel in selectors.split(","):
        sel = sel.strip()
        founds = element.select(sel)
        if founds:
            return list(founds)
    return []

# ─────────────────────────── Proxy Listesi ───────────────────────────
PROXIES = [
    # "http://username:password@ip:port",
    # "http://username:password@ip:port",
]

# ─────────────────────────── Scraper Motoru ──────────────────────────
async def _scrape_one(cfg: SiteConfig, query: str, dyn_headers: dict, use_httpx: bool = False, use_scraperapi: bool = False) -> list[SearchResult]:
    import random
    import httpx
    
    safe_query = urllib.parse.quote(query.strip())
    url = cfg.base_search_url.replace("{query}", safe_query)
    try:
        # Anti-Bot: Rastgele gecikme (Jitter) ekleyelim (0.2s - 1.5s arası)
        jitter = random.uniform(0.2, 1.5)
        await asyncio.sleep(jitter)
        
        # ── JSON Gizli API (Internal API) Fallback (n11 ve HB) ──
        if cfg.name in ["n11", "Hepsiburada"]:
            dyn_headers["Accept"] = "application/json, text/plain, */*"
        
        # ── Sahibinden Mobile API Simulation ──
        if cfg.name == "Sahibinden":
            url = url.replace("kelime-ile-arama?", "kelime-ile-arama?view=json&")
            dyn_headers["Accept"] = "application/json"
            dyn_headers["X-Requested-With"] = "XMLHttpRequest"
           
        if use_scraperapi:
            import os
            scraper_key = os.environ.get("SCRAPERAPI_KEY", "b33dummy123") # Örnek / Env'den gelir
            api_url = f"http://api.scraperapi.com?api_key={scraper_key}&url={urllib.parse.quote(url)}&country_code=tr"
            async with httpx.AsyncClient(timeout=8.0) as client:
                response = await client.get(api_url)
        elif use_httpx:
            async with httpx.AsyncClient(http2=True, verify=False, timeout=8.0) as client:
                response = await client.get(url, headers=dyn_headers)
        else:
            from curl_cffi.requests import AsyncSession
            # Chrome impersonation for stealth
            async with AsyncSession(impersonate="chrome120", headers=dyn_headers, verify=False) as client:
                # ── Session & Cookie Persistence (Pre-flight) ──
                # Arama yapmadan önce sitenin ana sayfasına bir ön istek atarak cf_clearance ve session_id gibi çerezleri topla
                from urllib.parse import urlparse
                base_domain = f"{urlparse(cfg.base_search_url).scheme}://{urlparse(cfg.base_search_url).netloc}"
                
                try:
                    await client.get(base_domain, timeout=8)
                    await asyncio.sleep(0.5) # Çerezleri sindirmesi için kısa bir bekleme (Vercel zamanıyla uyumlu)
                except Exception as e:
                    pass
                
                # Çerezlerle birlikte asıl arama isteğini at
                response = await client.get(url, timeout=8)
        
        if response.status_code >= 400:
            if response.status_code in [403, 429, 503]:
                # 403/Forbidden gibi hataları sessizce yakala, terminali boğma
                return [SearchResult(cfg.name, False, error_msg="Erişim Engellendi (Koruma)")]
            return [SearchResult(cfg.name, False, error_msg="Site Koruma Altında")]

        soup = BeautifulSoup(response.text, "html.parser")
        
        items = safe_select_all(soup, cfg.result_item_sel)
        
        # ── JSON LD+JSON Schema Extract (Çoklu ürün listesi için N11/HB Taraması) ──
        schema_results = []
        import json
        for script in soup.find_all('script', type='application/ld+json'):
            if script.string:
                try:
                    data = json.loads(script.string)
                    # N11 itemListElement array
                    if isinstance(data, dict) and data.get('@type') == 'ItemList' and 'itemListElement' in data:
                        for idx, el in enumerate(data['itemListElement']):
                            if isinstance(el, dict) and 'url' in el:
                                item = el.get('item', {}) if 'item' in el else el
                                name = item.get('name', 'Ürün İsimsiz')
                                price = None
                                image_url = ""
                                offers = item.get('offers', {})
                                if isinstance(offers, dict): price = offers.get('price')
                                elif isinstance(offers, list) and offers: price = offers[0].get('price')
                                
                                img_data = item.get('image', '')
                                if isinstance(img_data, str): image_url = img_data
                                elif isinstance(img_data, list) and img_data:
                                    image_url = img_data[0] if isinstance(img_data[0], str) else img_data[0].get('url', '')
                                elif isinstance(img_data, dict): image_url = img_data.get('url', '')

                                if price:
                                    s_price_str = f"{price} ₺"
                                    schema_results.append(SearchResult(cfg.name, True, part_name=name, price_str=s_price_str, price_numeric=parse_price(s_price_str), url=item.get('url', url), affiliate_url=generate_affiliate_url(item.get('url', url)), image_url=image_url))
                            if len(schema_results) >= 3: break
                except Exception: pass
        if schema_results:
            # Price Sanity Check (> 50 TL)
            valid_results = [r for r in schema_results if r.part_name and r.part_name != "Ürün İsimsiz" and r.price_numeric and r.price_numeric > 50]
            if valid_results:
                return valid_results
            else:
                print(f"[{cfg.name}] UYARI: Hiçbir schema ürünü 50 TL barajını geçemedi veya isimsiz.")

        # ── Hepsiburada __NEXT_DATA__ Extract ──
        if cfg.name == "Hepsiburada":
            next_data_m = re.search(r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>', response.text, re.DOTALL)
            if next_data_m:
                try:
                    next_data = json.loads(next_data_m.group(1))
                    # Try to find product list in various possible NEXT_DATA paths
                    products_src = next_data.get('props', {}).get('pageProps', {}).get('productModel', {}).get('productList', []) or \
                                   next_data.get('props', {}).get('pageProps', {}).get('listing', {}).get('data', {}).get('products', [])
                    
                    hb_results = []
                    for p in products_src[:5]:
                        name = p.get('name') or p.get('title')
                        price_data = p.get('price', {})
                        price_val = price_data.get('value') if isinstance(price_data, dict) else (p.get('currentPrice') or price_data)
                        
                        if name and price_val:
                            try:
                                p_num = float(str(price_val).replace(',', '.'))
                                if p_num > 50:
                                    p_str = f"{p_num} ₺"
                                    p_url = p.get('url', '')
                                    if p_url and not p_url.startswith('http'):
                                        p_url = "https://www.hepsiburada.com" + p_url
                                    
                                    img_url = ""
                                    img_list = p.get('imageUrls') or p.get('images', [])
                                    if img_list and isinstance(img_list, list):
                                        img_url = img_list[0].get('url', '') if isinstance(img_list[0], dict) else img_list[0]
                                    elif p.get('image'): 
                                        img_url = str(p.get('image'))

                                    hb_results.append(SearchResult(cfg.name, True, part_name=name, price_str=p_str, price_numeric=p_num, url=p_url or url, affiliate_url=generate_affiliate_url(p_url or url), image_url=img_url))
                            except: continue
                    if hb_results:
                        return hb_results[:3]
                except Exception as e:
                    print(f"[{cfg.name}] NEXT_DATA Parse Hatası: {e}")

        # ── Sahibinden Mobile JSON Parse ──
        if cfg.name == "Sahibinden" and 'application/json' in response.headers.get('content-type', ''):
            try:
                data = response.json()
                classifieds = data.get('classifieds', [])
                shb_results = []
                for cl in classifieds[:5]:
                    title = cl.get('title')
                    price_str = cl.get('price') # Örn: "1.200 TL"
                    price_num = parse_price(price_str)
                    if title and price_num and price_num > 50:
                        cl_url = f"https://www.sahibinden.com{cl.get('url')}"
                        img_url = cl.get('thumbnailUrl', '') or cl.get('thumbnailUrl1', '')
                        shb_results.append(SearchResult(cfg.name, True, part_name=title, price_str=price_str, price_numeric=price_num, url=cl_url, affiliate_url=generate_affiliate_url(cl_url), image_url=img_url))
                if shb_results:
                    return shb_results[:3]
            except: pass

        if not items:
            print(f"[{cfg.name}] UYARI: Ürün kartı (item) bulunamadı. Denediğim selectorlar: '{cfg.result_item_sel}'")
            
            # Kapsamlı (Çoklu) Regex Fallback (₺ ve TL Taraması + Satıcı Tahmini)
            import re
            m = re.finditer(r'\b([1-9][\d\.,]*)\s*(?:₺|TL|tl)\b', response.text, re.IGNORECASE)
            matches = list(m)
            if not matches:
                m = re.finditer(r'\b(?:₺|TL|tl)\s*([1-9][\d\.,]*)\b', response.text, re.IGNORECASE)
                matches = list(m)
            
            if matches:
                print(f"[{cfg.name}] UYARI: Tüm Selector/JSON boşa düştü ama Regex Fallback çalıştı!")
                found_res = []
                for match in matches:
                    price_raw = match.group(1)
                    clean_raw = str(price_raw).strip() + " ₺"
                    p_num = parse_price(clean_raw)
                    if p_num and p_num > 50:
                        # Satıcı tahmini (Fiyatın geçtiği yerden geriye doğru 200 karakterde satıcı/dükkan adı ara)
                        start_idx = max(0, match.start() - 200)
                        context = response.text[start_idx:match.start()]
                        seller_name = ""
                        # Basit bir satıcı class/title varsayımı
                        seller_match = re.search(r'(?:seller|store|magaza)[^>]*>([^<]+)<', context, re.IGNORECASE)
                        if seller_match:
                            seller_name = f" ({seller_match.group(1).strip()})"
                        
                        part_title = f"Hassas Fiyat Yakalama{seller_name}"
                        found_res.append(SearchResult(cfg.name, True, part_name=part_title, price_str=clean_raw, price_numeric=p_num, url=url, affiliate_url=generate_affiliate_url(url)))
                    if len(found_res) >= 3: break
                if found_res: return found_res
            return [SearchResult(cfg.name, False, error_msg="Fiyat Ayıklanamadı")]

        results_list = []
        for item in items[:3]: # En fazla 3 ürün gösterelim
            title_el = safe_select(item, cfg.title_sel)
            price_el = safe_select(item, cfg.price_sel)

            if not title_el or not price_el:
                continue

            part_name_raw = title_el.get_text(strip=True)
            price_raw = price_el.get_text(strip=True)
            price_num = parse_price(price_raw)
            
            # URL'yi çıkar (HREF)
            relative_url = title_el.get("href", "") if title_el.name == "a" else ""
            if not relative_url and title_el.parent and title_el.parent.name == "a":
                relative_url = title_el.parent.get("href", "")
                
            full_url = relative_url
            if relative_url.startswith("/"):
                from urllib.parse import urlparse
                parsed_base = urlparse(cfg.base_search_url)
                full_url = f"{parsed_base.scheme}://{parsed_base.netloc}{relative_url}"
                full_url = url

            image_url = ""
            if cfg.image_sel:
                img_el = safe_select(item, cfg.image_sel)
                if img_el:
                    image_url = img_el.get('data-original') or img_el.get('data-src') or img_el.get('src') or ""
                    if image_url and image_url.startswith('//'):
                        image_url = "https:" + image_url

            results_list.append(SearchResult(
                site_name     = cfg.name,
                success       = True,
                part_name     = part_name_raw,
                price_str     = price_raw,
                price_numeric = price_num,
                url           = full_url,
                affiliate_url = generate_affiliate_url(full_url),
                image_url     = image_url
            ))

        # Filter out junk results (Price sanity check > 50 TL and named items)
        results_list = [r for r in results_list if r.price_numeric and r.price_numeric > 50 and r.part_name and r.part_name != "Ürün İsimsiz"]

        if not results_list:
            hatali_selector = cfg.title_sel + " / " + cfg.price_sel
            print(f"[{cfg.name}] HATA: Kartlar bulundu ancak içlerinde element eşleşmedi veya kriter uymadı. Selector: '{hatali_selector}'")
            
            # Kapsamlı (Çoklu) Regex Fallback (₺ ve TL Taraması + Satıcı Tahmini)
            import re
            m = re.finditer(r'\b([1-9][\d\.,]*)\s*(?:₺|TL|tl)\b', response.text, re.IGNORECASE)
            matches = list(m)
            if not matches:
                m = re.finditer(r'\b(?:₺|TL|tl)\s*([1-9][\d\.,]*)\b', response.text, re.IGNORECASE)
                matches = list(m)
            
            if matches:
                print(f"[{cfg.name}] UYARI: Kart Parse boşa düştü ama Regex Fallback çalıştı!")
                found_res = []
                for match in matches:
                    price_raw = match.group(1)
                    clean_raw = str(price_raw).strip() + " ₺"
                    p_num = parse_price(clean_raw)
                    if p_num and p_num > 50:
                        # Satıcı tahmini (Fiyatın geçtiği yerden geriye doğru 200 karakterde satıcı/dükkan adı ara)
                        start_idx = max(0, match.start() - 200)
                        context = response.text[start_idx:match.start()]
                        seller_name = ""
                        # Basit bir satıcı class/title varsayımı
                        seller_match = re.search(r'(?:seller|store|magaza)[^>]*>([^<]+)<', context, re.IGNORECASE)
                        if seller_match:
                            seller_name = f" ({seller_match.group(1).strip()})"
                        
                        part_title = f"Hassas Fiyat Yakalama{seller_name}"
                        found_res.append(SearchResult(cfg.name, True, part_name=part_title, price_str=clean_raw, price_numeric=p_num, url=url, affiliate_url=generate_affiliate_url(url)))
                    if len(found_res) >= 3: break
                if found_res: return found_res
            return [SearchResult(cfg.name, False, error_msg="Fiyat Ayıklanamadı")]

        return results_list

    except asyncio.TimeoutError:
        return [SearchResult(cfg.name, False, error_msg="Zaman aşımı (Vercel 10s Tavanı)")]
    except Exception as exc:
        err_msg = str(exc)
        if "timeout" in err_msg.lower():
            return [SearchResult(cfg.name, False, error_msg="Zaman aşımı (Vercel 10s Tavanı)")]
        return [SearchResult(cfg.name, False, error_msg="Fiyat Alınamadı veya Engellendi")]

async def _scrape_one_with_limit(cfg: SiteConfig, query: str, dyn_headers: dict) -> list[SearchResult]:
    import random
    import asyncio
    
    # Target (Site) Spesifik Bekleme Süreleri Optimization (Kısaltıldı)
    delay = random.uniform(0.2, 0.5)
    await asyncio.sleep(delay)
    
    # Sadece 1 kez Katman 1'i dene, Vercel'de çok fazla denemeye vaktimiz yok!
    if CURL_CFFI_AVAILABLE:
        try:
            res = await _scrape_one(cfg, query, dyn_headers, use_httpx=False)
            for r in res: r.engine = "Stealth (curl_cffi)"
            return res
        except Exception as e:
            pass # Katman 2'ye atla

    # Hızlı Katman 2 (HTTPX HTTP/2 Fallback)
    try:
        res2 = await _scrape_one(cfg, query, dyn_headers, use_httpx=True)
        for r in res2: r.engine = "Stealth (httpx)"
        return res2
    except Exception as fallback_err:
        pass
        
    # Sona kalan Katman 3 (ScraperAPI Kriz Motoru)
    try:
        res3 = await _scrape_one(cfg, query, dyn_headers, use_scraperapi=True)
        for r in res3: r.engine = "ScraperAPI"
        return res3
    except Exception as api_err:
        return [SearchResult(cfg.name, False, error_msg="Sürekli Engel (Bot Koruması)", engine="Failed")]

class ScraperEngine:
    def __init__(self):
        pass
        
    def _headers_factory(self):
        import random
        referers = [
            "https://www.google.com.tr/",
            "https://yandex.com.tr/",
            "https://www.bing.com/",
            "https://duckduckgo.com/",
            "https://www.yahoo.com/"
        ]
        # Güncel Chrome Windows masaüstü kimliği (User-Agent ve Sec-* başlıkları eklendi)
        return {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
            "Referer": random.choice(referers),
            "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
            "Sec-Ch-Ua-Mobile": "?0",
            "Sec-Ch-Ua-Platform": '"Windows"',
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Sec-Fetch-User": "?1",
            "Upgrade-Insecure-Requests": "1"
        }

    async def search_all(self, query: str) -> list[SearchResult]:
        # Motor siteleri sırayla DEĞİL, asyncio.gather() ile aynı anda (concurrent) aratıyor
        print(f"[*] Eşzamanlı (Concurrent) Arama Başladı: {query} ...")
        
        dyn_headers = self._headers_factory()
        
        tasks = [_scrape_one_with_limit(cfg, query, dyn_headers) for cfg in SITES]
        results_of_lists = await asyncio.gather(*tasks, return_exceptions=False)
        
        final_results = []
        for rl in results_of_lists:
             if isinstance(rl, list):
                  final_results.extend(rl)
             else:
                  final_results.append(rl)
                  
        return final_results
            
    async def close(self):
        pass
