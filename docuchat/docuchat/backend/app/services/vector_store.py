from typing import List, Optional, Dict, Any
import chromadb
from chromadb.config import Settings as ChromaSettings


class VectorStore:
    """ChromaDB ile vektör depolama ve arama işlemleri."""

    def __init__(self, persist_dir: str):
        self.client = chromadb.PersistentClient(path=persist_dir)
        # Cosine similarity kullan (metin benzerliği için daha iyi)
        self.collection = self.client.get_or_create_collection(
            name="documents",
            metadata={"hnsw:space": "cosine"},
        )

    # ──────────────────────────────────────────
    # EKLEME
    # ──────────────────────────────────────────

    def add_chunks(
        self,
        document_id: str,
        document_name: str,
        chunks: List[str],
        embeddings: List[List[float]],
    ) -> None:
        """Parçaları ve vektörlerini ChromaDB'ye ekler."""
        ids = [f"{document_id}_{i}" for i in range(len(chunks))]
        metadatas = [
            {
                "document_id": document_id,
                "document_name": document_name,
                "chunk_index": i,
            }
            for i in range(len(chunks))
        ]
        self.collection.add(
            ids=ids,
            embeddings=embeddings,
            documents=chunks,
            metadatas=metadatas,
        )

    # ──────────────────────────────────────────
    # ARAMA
    # ──────────────────────────────────────────

    def query(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        document_ids: Optional[List[str]] = None,
    ) -> List[Dict[str, Any]]:
        """
        En alakalı parçaları döner.
        document_ids verilirse yalnızca o dokümanlardan arar.
        """
        where = None
        if document_ids:
            if len(document_ids) == 1:
                where = {"document_id": document_ids[0]}
            else:
                where = {"$or": [{"document_id": did} for did in document_ids]}

        # Koleksiyonda hiç döküman yoksa boş dön
        if self.collection.count() == 0:
            return []

        actual_top_k = min(top_k, self.collection.count())

        results = self.collection.query(
            query_embeddings=[query_embedding],
            n_results=actual_top_k,
            where=where,
            include=["documents", "metadatas", "distances"],
        )

        chunks = []
        for i in range(len(results["documents"][0])):
            distance = results["distances"][0][i]
            similarity = 1 - distance  # cosine distance → similarity
            chunks.append(
                {
                    "text": results["documents"][0][i],
                    "metadata": results["metadatas"][0][i],
                    "score": round(similarity, 4),
                }
            )
        # En yüksek benzerlikten başlayarak sırala
        chunks.sort(key=lambda x: x["score"], reverse=True)
        return chunks

    # ──────────────────────────────────────────
    # YÖNETİM
    # ──────────────────────────────────────────

    def delete_document(self, document_id: str) -> None:
        """Bir dokümana ait tüm chunk'ları siler."""
        results = self.collection.get(where={"document_id": document_id})
        if results["ids"]:
            self.collection.delete(ids=results["ids"])

    def get_chunk_count(self, document_id: str) -> int:
        results = self.collection.get(where={"document_id": document_id})
        return len(results["ids"])

    def document_exists(self, document_id: str) -> bool:
        return self.get_chunk_count(document_id) > 0
