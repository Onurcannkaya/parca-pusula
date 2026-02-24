import sys
import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import flet_fastapi

# Root dizinini path'e ekle (main.py ve scraper.py'ye erişmek için)
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scraper import ScraperEngine
from main import main as flet_main

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
# Vercel'de root (/) isteklerini Flet'e yönlendirmek için mount ediyoruz.
app.mount("/", flet_fastapi.app(flet_main))
