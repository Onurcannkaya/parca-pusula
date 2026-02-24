from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from scraper import ScraperEngine

app = FastAPI(title="ParçaPusula API", description="Serverless Scraper API")

# Allow requests from the Flet frontend
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
        
        # ── Başarılı aramaları JSON formatında yerel olarak logla (Caching için temel) ──
        import json, os
        from datetime import datetime
        try:
            log_file = "search_logs.json"
            logs = []
            if os.path.exists(log_file):
                with open(log_file, "r", encoding="utf-8") as f:
                    try:
                        logs = json.load(f)
                    except:
                        pass
            
            logs.append({
                "timestamp": datetime.now().isoformat(),
                "query": q,
                "found_count": sum(1 for r in results if r.success)
            })
            
            with open(log_file, "w", encoding="utf-8") as f:
                json.dump(logs[-100:], f, ensure_ascii=False, indent=2)  # Son 100 aramayı tutar
        except Exception as log_err:
            print("Loglama Hatası:", log_err)
            
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
    return {"status": "ok", "app": "ParcaPusula Lite PWA Engine"}
