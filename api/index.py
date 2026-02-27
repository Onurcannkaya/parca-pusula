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

from fastapi.responses import FileResponse

PUBLIC_DIR = os.path.join(root_dir, "public")

@app.get("/")
async def serve_root():
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))

@app.get("/{full_path:path}")
async def serve_static(full_path: str):
    # API yollarını ezmemek için (güvenlik)
    if full_path.startswith("api/"):
        return {"status": "error", "message": "Not Found"}
        
    # Eğer boş gelirse (yani ana sayfa) veya dosya bulunamazsa index.html döndür
    if not full_path or full_path == "/":
        return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))
    
    file_path = os.path.join(PUBLIC_DIR, full_path)
    if os.path.isfile(file_path):
        return FileResponse(file_path)
    
    # 404 yerine PWA/SPA için index.html döndürüyoruz
    return FileResponse(os.path.join(PUBLIC_DIR, "index.html"))
