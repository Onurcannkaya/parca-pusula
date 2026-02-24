import sys
import os

# Root dizinini path'e ekle (main.py ve scraper.py'ye erişmek için)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
import flet as ft
import flet.fastapi as flet_fastapi

# FastAPI uygulamasını başlat
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
    return {"status": "ok", "app": "ParcaPusula Engine"}

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

# ── Flet Arayüz Entegrasyonu (Mapping Engineer Özel) ──
from main import main as flet_main

# EN KRİTİK ADIM: Flet'i FastAPI'nin kök dizinine (/) monte et
# Bu satır, Vercel'deki 404/Not Found hatasını çözen anahtar işlemdir.
app.mount("/", flet_fastapi.app(flet_main))
