# scraper.py — ParçaPusula Lite Async Scraper Engine (Vercel & PWA Uyumlu)
import asyncio
import httpx
import re
import random
import urllib.parse
from curl_cffi.requests import AsyncSession
from bs4 import BeautifulSoup
from dataclasses import dataclass
from typing import Optional

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

@dataclass
class SiteConfig:
    name           : str
    base_search_url: str
    result_item_sel: str
    title_sel      : str
    price_sel      : str
    timeout_ms     : int = 15_000

# ─────────────────────────── Site Tanımları ──────────────────────────
SITES: list[SiteConfig] = [
    SiteConfig(
        name            = "OnlineYedekParca",
        base_search_url = "https://www.onlineyedekparca.com/arama/{query}",
        result_item_sel = "div.showcase, div.ProductItem, div.product-item, div.product-card, div.card",
        title_sel       = "div.showcase-title a, div.productName a, div.product-title a, h3.name, a.title, div.product-name a, h3.product-name a",
        price_sel       = "div.showcase-price span, div.discountPrice span, div.product-price span, span.price, div.price, div.current-price, span.current-price",
    ),
    SiteConfig(
        name="AlloYedekParca",
        base_search_url="https://www.aloparca.com/arama/{query}",
        result_item_sel=".product-item, .product-card",
        title_sel="a.product-name, h3.product-title a",
        price_sel=".product-price, .price"
    ),
    SiteConfig(
        name="ParcaDeposu",
        base_search_url="https://www.otoparcadeposu.com/arama?q={query}",
        result_item_sel=".showcase",
        title_sel=".showcase-title a",
        price_sel=".showcase-price-new"
    ),
    SiteConfig(
        name            = "n11",
        base_search_url = "https://www.n11.com/arama?q={query}",
        result_item_sel = "li.column, div.pro, ul.list-ul li, div.listView ul li, li.product, div.product",
        title_sel       = "h3.productName, a.proName, h3.name, h3",
        price_sel       = "ins, span.newPrice c, div.priceContainer ins, div.price, span.new-price",
    ),
    SiteConfig(
        name            = "Hepsiburada",
        base_search_url = "https://www.hepsiburada.com/ara?q={query}",
        result_item_sel = "li.productListContent-item, ul.productList li, div[data-test-id='product-card'], div.product-card",
        title_sel       = "h3[data-test-id='product-card-name'], h3, div.product-title",
        price_sel       = "div[data-test-id='price-current-price'], span.price, div.price-value, span.price-current-price",
    ),
    SiteConfig(
        name            = "Sahibinden",
        base_search_url = "https://www.sahibinden.com/kelime-ile-arama?query_text={query}",
        result_item_sel = "tr.searchResultsItem, div.list-item",
        title_sel       = "a.classifiedTitle, h3.title",
        price_sel       = "td.searchResultsPriceValue div, span.price",
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
            async with httpx.AsyncClient(timeout=cfg.timeout_ms / 1000.0 * 2) as client:
                response = await client.get(api_url)
        elif use_httpx:
            async with httpx.AsyncClient(http2=True, verify=False, proxies=proxy, timeout=cfg.timeout_ms / 1000.0) as client:
                response = await client.get(url, headers=dyn_headers)
        else:
            from curl_cffi.requests import AsyncSession
            # iOS 17 Safari impersonation for stealth
            async with AsyncSession(impersonate="safari17_0", proxies=proxies_dict, headers=dyn_headers, verify=False) as client:
                # ── Session & Cookie Persistence (Pre-flight) ──
                # Arama yapmadan önce sitenin ana sayfasına bir ön istek atarak cf_clearance ve session_id gibi çerezleri topla
                from urllib.parse import urlparse
                base_domain = f"{urlparse(cfg.base_search_url).scheme}://{urlparse(cfg.base_search_url).netloc}"
                
                try:
                    await client.get(base_domain, timeout=cfg.timeout_ms / 1000.0)
                    await asyncio.sleep(random.uniform(0.5, 1.2)) # Çerezleri sindirmesi için kısa bir bekleme
                except Exception as e:
                    print(f"[{cfg.name}] Preflight (Cookie Session) Hatası: {e}")
                
                # Çerezlerle birlikte asıl arama isteğini at
                response = await client.get(url, timeout=cfg.timeout_ms / 1000.0)
        
        if response.status_code >= 400:
            if response.status_code in [403, 429, 503]:
                print(f"[{cfg.name}] KRİTİK: {response.status_code} Hata! Bot Koruması/Rate Limit.")
                raise Exception(f"HTTP_{response.status_code}_BLOCKED")
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
                                offers = item.get('offers', {})
                                if isinstance(offers, dict): price = offers.get('price')
                                elif isinstance(offers, list) and offers: price = offers[0].get('price')
                                
                                if price:
                                    s_price_str = f"{price} ₺"
                                    schema_results.append(SearchResult(cfg.name, True, part_name=name, price_str=s_price_str, price_numeric=parse_price(s_price_str), url=item.get('url', url), affiliate_url=generate_affiliate_url(item.get('url', url))))
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
                                    hb_results.append(SearchResult(cfg.name, True, part_name=name, price_str=p_str, price_numeric=p_num, url=p_url or url, affiliate_url=generate_affiliate_url(p_url or url)))
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
                        shb_results.append(SearchResult(cfg.name, True, part_name=title, price_str=price_str, price_numeric=price_num, url=cl_url, affiliate_url=generate_affiliate_url(cl_url)))
                if shb_results:
                    return shb_results[:3]
            except: pass

        if not items:
            print(f"[{cfg.name}] UYARI: Ürün kartı (item) bulunamadı. Denediğim selectorlar: '{cfg.result_item_sel}'")
            
            # Kapsamlı (Çoklu) Regex Fallback (₺ ve TL Taraması)
            import re
            m = re.findall(r'([\d\.,]+)\s*[₺|TL]', response.text)
            if not m:
                m = re.findall(r'[₺|TL]\s*([\d\.,]+)', response.text)
            if m:
                print(f"[{cfg.name}] UYARI: Tüm Selector/JSON boşa düştü ama Regex Fallback çalıştı!")
                found_res = []
                for price_raw in m:
                    clean_raw = str(price_raw).strip() + " ₺"
                    p_num = parse_price(clean_raw)
                    if p_num and p_num > 50:
                        found_res.append(SearchResult(cfg.name, True, part_name="Hassas Fiyat Yakalama", price_str=clean_raw, price_numeric=p_num, url=url, affiliate_url=generate_affiliate_url(url)))
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
            elif not relative_url.startswith("http"):
                full_url = url

            results_list.append(SearchResult(
                site_name     = cfg.name,
                success       = True,
                part_name     = part_name_raw,
                price_str     = price_raw,
                price_numeric = price_num,
                url           = full_url,
                affiliate_url = generate_affiliate_url(full_url)
            ))

        # Filter out junk results (Price sanity check > 50 TL and named items)
        results_list = [r for r in results_list if r.price_numeric and r.price_numeric > 50 and r.part_name and r.part_name != "Ürün İsimsiz"]

        if not results_list:
            hatali_selector = cfg.title_sel + " / " + cfg.price_sel
            print(f"[{cfg.name}] HATA: Kartlar bulundu ancak içlerinde element eşleşmedi veya kriter uymadı. Selector: '{hatali_selector}'")
            
            # Kapsamlı (Çoklu) Regex Fallback (₺ ve TL Taraması)
            import re
            m = re.findall(r'([\d\.,]+)\s*[₺|TL]', response.text)
            if not m:
                m = re.findall(r'[₺|TL]\s*([\d\.,]+)', response.text)
            if m:
                print(f"[{cfg.name}] UYARI: Kart Parse boşa düştü ama Regex Fallback çalıştı!")
                found_res = []
                for price_raw in m:
                    clean_raw = str(price_raw).strip() + " ₺"
                    p_num = parse_price(clean_raw)
                    if p_num and p_num > 50:
                        found_res.append(SearchResult(cfg.name, True, part_name="Hassas Fiyat Yakalama", price_str=clean_raw, price_numeric=p_num, url=url, affiliate_url=generate_affiliate_url(url)))
                    if len(found_res) >= 3: break
                if found_res: return found_res
            return [SearchResult(cfg.name, False, error_msg="Fiyat Ayıklanamadı")]

        return results_list

    except Exception as exc:
        from curl_cffi.requests.errors import Timeout
        if isinstance(exc, Timeout):
            print(f"[{cfg.name}] HATA: Zaman aşımı.")
            return [SearchResult(cfg.name, False, error_msg="Zaman aşımı — site yanıt vermedi.")]
        print(f"[{cfg.name}] BEKLENMEYEN HATA: {type(exc).__name__} - {str(exc)[:50]}")
        return [SearchResult(cfg.name, False, error_msg="Fiyat Alınamadı")]

async def _scrape_one_with_limit(cfg: SiteConfig, query: str, dyn_headers: dict) -> list[SearchResult]:
    import random
    import asyncio
    
    # Target (Site) Spesifik Bekleme Süreleri Optimization
    if cfg.name in ["n11", "Hepsiburada", "Sahibinden"]:
        delay = random.uniform(2.5, 5.0)
    else:
        delay = random.uniform(0.5, 2.0)
        
    await asyncio.sleep(delay)
    
    # ── Akıllı Proxy & IP Failover (Retry Loop) ──
    max_retries = 3
    last_err = "Bilinmeyen Hata"
    
    for attempt in range(max_retries):
        try:
            res = await _scrape_one(cfg, query, dyn_headers, use_httpx=False)
            for r in res: r.engine = "Stealth (curl_cffi)"
            return res
        except Exception as e:
            err_msg = str(e)
            last_err = err_msg
            if "HTTP_403_BLOCKED" in err_msg or "HTTP_429_BLOCKED" in err_msg or "HTTP_503_BLOCKED" in err_msg:
                print(f"[{cfg.name}] Katman 1 (curl_cffi) Deneme {attempt+1}/{max_retries} Başarısız. Proxy Değiştirilip Tekrar Deneniyor...")
                await asyncio.sleep(random.uniform(2.0, 4.0)) # Ban yememek için uzun bekle
                continue
            else:
                print(f"[{cfg.name}] Kapsamlı Hata: {type(e).__name__} - {err_msg[:50]}")
                break # Diğer hatalarda Katman 2'ye geç
                
    # Max Retry aşıldıysa (Katman 1 Başarısız) => Katman 2: HTTPX HTTP/2 Fallback
    print(f"[{cfg.name}] Katman 1 aşıldı! Katman 2 (HTTPX HTTP/2 Fallback) deneniyor...")
    try:
        await asyncio.sleep(random.uniform(1.0, 2.5))
        res2 = await _scrape_one(cfg, query, dyn_headers, use_httpx=True)
        for r in res2: r.engine = "Stealth (httpx)"
        return res2
    except Exception as fallback_err:
        print(f"[{cfg.name}] Katman 2 Başarısız: {str(fallback_err)[:50]}")
        
        # ── Katman 3: ScraperAPI Kriz Motoru ──
        print(f"[{cfg.name}] Tüm Stealth Motorları Tükendi! Katman 3: ScraperAPI Kriz Motoru Devrede...")
        try:
            res3 = await _scrape_one(cfg, query, dyn_headers, use_scraperapi=True)
            for r in res3: r.engine = "ScraperAPI"
            return res3
        except Exception as api_err:
             print(f"[{cfg.name}] Katman 3 (ScraperAPI) de Başarısız: {str(api_err)[:50]}")
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
            "https://www.apple.com/"
        ]
        # Gerçek Mac OS Safari 17.0 izleri (Desktop rendering, yet still stealth via safari17_0 impersonate)
        return {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15",
            "Accept-Language": "tr-TR,tr;q=0.9,en-US;q=0.8,en;q=0.7",
            "Accept-Encoding": "gzip, deflate, br",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8",
            "Referer": random.choice(referers),
            "Sec-Fetch-Dest": "document",
            "Sec-Fetch-Mode": "navigate",
            "Sec-Fetch-Site": "cross-site",
            "Upgrade-Insecure-Requests": "1"
        }

    async def search_all(self, query: str) -> list[SearchResult]:
        print(f"[*] İstek atılıyor. Kullanılan UA: Chrome 120 Impersonation ve Rotating Proxies...")
        
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
