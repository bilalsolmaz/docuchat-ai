import json
from typing import List, Optional

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse

from app.config import settings
from app.models import ChatRequest, ChatResponse, Source, SummaryRequest
from app.services import metadata_store
from app.services.llm_service import (
    create_embedding,
    generate_answer,
    generate_answer_stream,
    generate_summary,
)
from app.services.vector_store import VectorStore

router = APIRouter(prefix="/chat", tags=["chat"])
vs = VectorStore(settings.chroma_persist_dir)


# ─────────────────────────────────────────────
# YARDIMCI: İlgili chunk'ları getir
# ─────────────────────────────────────────────

async def retrieve_chunks(question: str, document_ids: Optional[List[str]]):
    query_embedding = await create_embedding(question)
    chunks = vs.query(query_embedding, top_k=settings.top_k, document_ids=document_ids)
    if not chunks:
        raise HTTPException(
            status_code=404,
            detail="İlgili içerik bulunamadı. Lütfen önce doküman yükleyin.",
        )
    return chunks


def build_sources(chunks: list) -> List[Source]:
    return [
        Source(
            document_name=c["metadata"]["document_name"],
            document_id=c["metadata"]["document_id"],
            chunk_text=c["text"][:300] + "..." if len(c["text"]) > 300 else c["text"],
            relevance_score=c["score"],
        )
        for c in chunks
    ]


# ─────────────────────────────────────────────
# NORMAL SORU-CEVAP
# ─────────────────────────────────────────────

@router.post("/ask", response_model=ChatResponse)
async def ask(request: ChatRequest):
    """
    Yüklü dokümanlar üzerinden soru sorar.
    document_ids boşsa tüm dokümanlarda arar.
    """
    chunks = await retrieve_chunks(request.question, request.document_ids)
    answer = await generate_answer(request.question, chunks)
    sources = build_sources(chunks)

    return ChatResponse(
        answer=answer,
        sources=sources,
        question=request.question,
    )


# ─────────────────────────────────────────────
# STREAMING SORU-CEVAP (SSE)
# ─────────────────────────────────────────────

@router.post("/stream")
async def ask_stream(request: ChatRequest):
    """
    Streaming cevap — Server-Sent Events (SSE) formatında anlık kelime akışı.
    Frontend'de EventSource veya fetch ile okunur.
    """
    chunks = await retrieve_chunks(request.question, request.document_ids)
    sources = build_sources(chunks)

    async def event_generator():
        # Kaynakları önce gönder (frontend'de gösterim için)
        sources_payload = json.dumps(
            {"type": "sources", "data": [s.model_dump() for s in sources]},
            ensure_ascii=False,
        )
        yield f"data: {sources_payload}\n\n"

        # Cevabı kelime kelime akıt
        async for token in generate_answer_stream(request.question, chunks):
            token_payload = json.dumps(
                {"type": "token", "data": token}, ensure_ascii=False
            )
            yield f"data: {token_payload}\n\n"

        # Bitiş sinyali
        yield f"data: {json.dumps({'type': 'done'})}\n\n"

    return StreamingResponse(
        event_generator(),
        media_type="text/event-stream",
        headers={
            "Cache-Control": "no-cache",
            "X-Accel-Buffering": "no",   # Nginx proxy'de buffering'i kapat
        },
    )


# ─────────────────────────────────────────────
# ÖZETLEMEaccount
# ─────────────────────────────────────────────

@router.post("/summarize")
async def summarize(request: SummaryRequest):
    """
    Seçilen dokümanların özetini çıkarır.
    document_ids verilmezse tüm dokümanlar özetlenir.
    """
    # Özet için temsili chunk'lar al (ilk 1000 karakter gibi kısa sorgu)
    dummy_question = "Bu dokümanın ana konusu ve içeriği nedir?"
    query_embedding = await create_embedding(dummy_question)

    top_k_summary = min(10, max(1, settings.top_k * 2))
    chunks = vs.query(
        query_embedding, top_k=top_k_summary, document_ids=request.document_ids
    )

    if not chunks:
        raise HTTPException(status_code=404, detail="Özetlenecek doküman bulunamadı.")

    summary = await generate_summary(chunks)
    sources = list({c["metadata"]["document_name"] for c in chunks})

    return {
        "summary": summary,
        "source_documents": sources,
    }
