import sys
import os

# Deterministic Path Resolution
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="ParçaPusula Fullstack")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "engine": "FastAPI Serverless"}

@app.get("/api/search")
async def search_parts(q: str):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Arama terimi çok kısa.")
    try:
        from scraper import ScraperEngine
        engine = ScraperEngine()
        results = await engine.search_all(q.strip())
        return {
            "query": q,
            "results": [
                {
                    "site": r.site_name,
                    "success": r.success,
                    "part_name": r.part_name,
                    "price_str": r.price_str,
                    "price_numeric": r.price_numeric,
                    "url": r.url,
                    "affiliate_url": r.affiliate_url,
                    "engine": getattr(r, "engine", "Stealth"),
                    "status": r.error_msg if not r.success else "OK"
                }
                for r in results
            ]
        }
    except Exception as e:
        return {"error": str(e), "success": False}

# ── Flet App Mount ──
try:
    import flet.fastapi as flet_fastapi
    from main import main as flet_main
    app.mount("/", flet_fastapi.app(flet_main))
except Exception as e:
    print(f"Flet Mount Error: {e}")
