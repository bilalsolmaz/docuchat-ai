from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime


class DocumentInfo(BaseModel):
    id: str
    name: str
    size: int
    chunks: int
    created_at: str


class ChatRequest(BaseModel):
    question: str
    document_ids: Optional[List[str]] = None  # None = tüm dokümanlar


class Source(BaseModel):
    document_name: str
    document_id: str
    chunk_text: str
    relevance_score: float


class ChatResponse(BaseModel):
    answer: str
    sources: List[Source]
    question: str


class DeleteResponse(BaseModel):
    message: str
    document_id: str


class SummaryRequest(BaseModel):
    document_ids: Optional[List[str]] = None
