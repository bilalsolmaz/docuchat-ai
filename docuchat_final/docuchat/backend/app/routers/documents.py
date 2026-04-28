import os
import uuid
import logging
import traceback
from typing import List

from fastapi import APIRouter, File, HTTPException, UploadFile
from fastapi.responses import JSONResponse

from app.config import settings
from app.models import DeleteResponse, DocumentInfo
from app.services import metadata_store
from app.services.document_processor import chunk_text, clean_text, extract_text
from app.services.llm_service import create_embeddings_batch
from app.services.vector_store import VectorStore

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/documents", tags=["documents"])

# Uygulama boyunca aynı VectorStore kullanılır
vs = VectorStore(settings.chroma_persist_dir)

ALLOWED_EXTENSIONS = {".txt", ".pdf", ".doc", ".docx"}
MAX_FILE_SIZE_MB = 20


# ─────────────────────────────────────────────
# YÜKLEME
# ─────────────────────────────────────────────

@router.post("/upload", response_model=List[DocumentInfo])
async def upload_documents(files: List[UploadFile] = File(...)):
    """
    Birden fazla dosyayı aynı anda yükler, işler ve vektör DB'ye kaydeder.
    Desteklenen formatlar: TXT, PDF, DOC, DOCX
    """
    if not files:
        raise HTTPException(status_code=400, detail="En az bir dosya yükleyin.")

    results = []

    for file in files:
        ext = os.path.splitext(file.filename)[1].lower()
        if ext not in ALLOWED_EXTENSIONS:
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' desteklenmiyor. İzin verilenler: {ALLOWED_EXTENSIONS}",
            )

        # Dosya boyutu kontrolü
        content = await file.read()
        logger.info(f"Dosya okundu: {file.filename} ({len(content)} byte)")

        if len(content) > MAX_FILE_SIZE_MB * 1024 * 1024:
            raise HTTPException(
                status_code=400,
                detail=f"'{file.filename}' çok büyük (max {MAX_FILE_SIZE_MB}MB).",
            )

        # Aynı isimde dosya varsa güncelle
        existing_id = metadata_store.document_exists_by_name(file.filename)
        doc_id = existing_id if existing_id else str(uuid.uuid4())
        logger.info(f"Doc ID: {doc_id}, mevcut mu: {bool(existing_id)}")

        # Diske kaydet
        file_path = os.path.join(settings.upload_dir, f"{doc_id}{ext}")
        with open(file_path, "wb") as f:
            f.write(content)
        logger.info(f"Dosya diske kaydedildi: {file_path}")

        # Metin çıkar ve temizle
        try:
            raw_text = extract_text(file_path, file.filename)
            logger.info(f"Metin çıkarıldı: {len(raw_text)} karakter")
        except Exception as e:
            logger.error(f"Metin çıkarma hatası: {traceback.format_exc()}")
            raise HTTPException(status_code=422, detail=f"Metin çıkarma hatası: {str(e)}")

        clean = clean_text(raw_text)
        logger.info(f"Temizlenmiş metin: {len(clean)} karakter")

        if not clean:
            raise HTTPException(
                status_code=422,
                detail=f"'{file.filename}' dosyasından metin çıkarılamadı.",
            )

        # Chunk'lara böl
        chunks = chunk_text(clean, settings.chunk_size, settings.chunk_overlap)
        logger.info(f"Chunk sayısı: {len(chunks)}")

        # Embedding oluştur (toplu - daha verimli)
        try:
            logger.info(f"Embedding oluşturuluyor ({len(chunks)} chunk)...")
            embeddings = await create_embeddings_batch(chunks)
            logger.info(f"Embedding tamamlandı: {len(embeddings)} vektör")
        except Exception as e:
            logger.error(f"Embedding hatası: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"OpenAI embedding hatası: {str(e)}")

        # Eski vektörleri temizle (güncelleme senaryosu)
        if existing_id:
            vs.delete_document(doc_id)

        # ChromaDB'ye kaydet
        try:
            vs.add_chunks(doc_id, file.filename, chunks, embeddings)
            logger.info(f"ChromaDB'ye kaydedildi")
        except Exception as e:
            logger.error(f"ChromaDB kayıt hatası: {traceback.format_exc()}")
            raise HTTPException(status_code=500, detail=f"Vektör DB hatası: {str(e)}")

        # Metadata kaydet
        metadata_store.save_document(doc_id, file.filename, len(content), len(chunks))
        logger.info(f"Metadata kaydedildi. İşlem tamamlandı: {file.filename}")

        results.append(
            DocumentInfo(
                id=doc_id,
                name=file.filename,
                size=len(content),
                chunks=len(chunks),
                created_at=metadata_store.get_document(doc_id)["created_at"],
            )
        )

    return results


# ─────────────────────────────────────────────
# LİSTELEME
# ─────────────────────────────────────────────

@router.get("/", response_model=List[DocumentInfo])
def list_documents():
    """Yüklü tüm dokümanları listeler."""
    docs = metadata_store.get_all_documents()
    return [DocumentInfo(**d) for d in docs]


# ─────────────────────────────────────────────
# SİLME
# ─────────────────────────────────────────────

@router.delete("/{document_id}", response_model=DeleteResponse)
def delete_document(document_id: str):
    """Bir dokümanı ve ilgili vektörleri siler."""
    doc = metadata_store.get_document(document_id)
    if not doc:
        raise HTTPException(status_code=404, detail="Doküman bulunamadı.")

    # ChromaDB'den sil
    vs.delete_document(document_id)

    # Fiziksel dosyayı sil
    ext = os.path.splitext(doc["name"])[1].lower()
    file_path = os.path.join(settings.upload_dir, f"{document_id}{ext}")
    if os.path.exists(file_path):
        os.remove(file_path)

    # Metadata'dan sil
    metadata_store.delete_document(document_id)

    return DeleteResponse(message=f"'{doc['name']}' başarıyla silindi.", document_id=document_id)
