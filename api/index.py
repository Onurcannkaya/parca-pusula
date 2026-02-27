import sys
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

# Root dizinini path'e ekle (scraper.py'ye erişmek için)
current_dir = os.path.dirname(os.path.abspath(__file__))
root_dir = os.path.dirname(current_dir)
if root_dir not in sys.path:
    sys.path.insert(0, root_dir)

from scraper import ScraperEngine

app = FastAPI(title="ParçaPusula API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

engine = ScraperEngine()

@app.get("/api/search")
async def search_api(q: str):
    """HTML ön yüzünden gelen aramaları karşılar, motoru çalıştırır ve sonuçları geri yollar."""
    try:
        results_raw = await engine.search_all(q)
        results_json = [res.__dict__ for res in results_raw]
        return {"status": "success", "data": results_json}
    except Exception as e:
        return {"status": "error", "message": str(e)}
