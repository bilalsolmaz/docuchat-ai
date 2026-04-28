from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
import os
import logging

# Logging yapılandırması
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger(__name__)

from app.routers import documents, chat

# ─────────────────────────────────────────────
# UYGULAMA
# ─────────────────────────────────────────────

app = FastAPI(
    title="DocuChat API",
    description="Dokümanlarınızla yapay zeka destekli sohbet",
    version="1.0.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
)

# CORS — Frontend'in farklı port'tan erişebilmesi için
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Prodüksiyon'da kısıtlanmalı
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Router'ları bağla
app.include_router(documents.router, prefix="/api")
app.include_router(chat.router, prefix="/api")

# Frontend static dosyalarını sun (tek container deployment için)
frontend_path = os.path.join(os.path.dirname(__file__), "../../frontend")
if os.path.exists(frontend_path):
    app.mount("/static", StaticFiles(directory=frontend_path), name="static")

    @app.get("/", include_in_schema=False)
    def serve_frontend():
        return FileResponse(os.path.join(frontend_path, "index.html"))


# ─────────────────────────────────────────────
# SAĞLIK KONTROLÜ
# ─────────────────────────────────────────────

@app.get("/api/health", tags=["health"])
def health():
    return {"status": "ok", "message": "DocuChat API çalışıyor 🚀"}


# ─────────────────────────────────────────────
# __init__.py'ler
# ─────────────────────────────────────────────
