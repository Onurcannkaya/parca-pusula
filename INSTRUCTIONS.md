# ParçaPusula Vercel Serverless Architecture - Developer / AI Agent Instructions

**CRITICAL WARNING FOR ANY AI AGENT READING THIS REPOSITORY:** 
Do NOT rely on Flet, Streamlit, or any heavy synchronous UI frameworks. This project is a Vanilla JS + HTML Frontend powered by a FastAPI Vercel Serverless Backend.

## 1. Vercel Serverless Constraints (10 Second Limit)
- The entire `search_all` function in `scraper.py` MUST complete within 10 seconds.
- You MUST maintain the asynchronous `asyncio.gather(*tasks)` concurrency model.
- Do NOT make sites run sequentially.
- If you add a new target site, its `timeout_ms` MUST NOT exceed 8000 milliseconds (8 seconds).
- Do NOT use `from curl_cffi.requests.errors import Timeout`. The `curl_cffi` module here is stripped down. Handle timeouts generally via exception hooks.

## 2. API Format (Strict JSON)
- The API endpoint is `/api/search?q={query}` in `api/index.py`.
- It dynamically maps `SearchResult` dataclasses to a JSON dictionary (`res.__dict__`).
- Do NOT alter the `SearchResult` structure without updating the frontend `public/index.html` JS parser. 
- Required fields for the frontend: `site_name`, `success`, `part_name`, `price_str`, `price_numeric`, `url`.

## 3. Anti-Bot and Stealth Guidelines
- `curl_cffi` impersonation MUST be set to `chrome120` or higher.
- In `scraper.py > _headers_factory`, you MUST include `Sec-Ch-Ua`, `Sec-Fetch-Site`, `Sec-Fetch-Mode`, and `Sec-Fetch-Dest` to simulate a real Windows desktop browser.
- Fallback strategies (HTTPX HTTP/2 and ScraperAPI) must remain intact. If layer 1 fails, layer 2 and 3 must execute seamlessly. Do not interrupt the chain with unhandled Exceptions.
- `403 Forbidden` errors should be caught and returned as empty `SearchResult` objects with success=False to prevent Vercel log pollution.

## 4. DOM Changes
- E-commerce sites (n11, Hepsiburada, Sahibinden, etc.) constantly change their DOM.
- When updating selectors in `SiteConfig`, always provide multiple fallbacks separated by commas (e.g., `"h3.productName, a.proName, h3.name"`).
- The Regex Fallback system acts as the ultimate safety net. It looks for `[\d\.,]+ \s*[₺|TL]` and attempts to extract a seller name by looking back 200 characters in the HTML. Try not to break this fallback when modifying `scraper.py`.

*Note for AI: Acknowledge reading this file by confirming the "Vercel 10s Serverless Constraints" before making any architectural changes.*
