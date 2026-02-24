from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import flet.fastapi as flet_fastapi
import sys
import os

# Deterministic Path Resolution for Vercel
# index.py is in 'api/', so '..' is the root where scraper.py and main.py live.
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

try:
    from scraper import ScraperEngine
    from main import main as flet_main
except ImportError as e:
    print(f"[FATAL] Modül yükleme hatası: {e}")
    # Re-raise to let Vercel capture the crash logs
    raise e

app = FastAPI(title="ParçaPusula API", description="Serverless Fullstack Engine")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ScraperEngine()

@app.get("/api/search")
async def search_parts(q: str):
    if not q or len(q.strip()) < 2:
        raise HTTPException(status_code=400, detail="Arama terimi çok kısa.")
    try:
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
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "app": "ParcaPusula Fullstack Engine"}

# ── Flet App Mount ──
app.mount("/", flet_fastapi.app(flet_main))
