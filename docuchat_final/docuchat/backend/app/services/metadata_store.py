"""
Doküman metadata'sını JSON dosyasında saklar.
Gerçek projede PostgreSQL/SQLite tercih edilir,
ancak no-code/low-code challenge için JSON yeterlidir.
"""

import json
import os
from typing import Dict, List, Optional
from datetime import datetime


METADATA_FILE = "./uploads/documents_metadata.json"


def _load() -> Dict:
    if os.path.exists(METADATA_FILE):
        with open(METADATA_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    return {}


def _save(data: Dict) -> None:
    os.makedirs(os.path.dirname(METADATA_FILE), exist_ok=True)
    with open(METADATA_FILE, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def save_document(doc_id: str, name: str, size: int, chunks: int) -> None:
    data = _load()
    data[doc_id] = {
        "id": doc_id,
        "name": name,
        "size": size,
        "chunks": chunks,
        "created_at": datetime.now().isoformat(),
    }
    _save(data)


def get_all_documents() -> List[Dict]:
    data = _load()
    return list(data.values())


def get_document(doc_id: str) -> Optional[Dict]:
    data = _load()
    return data.get(doc_id)


def delete_document(doc_id: str) -> bool:
    data = _load()
    if doc_id in data:
        del data[doc_id]
        _save(data)
        return True
    return False


def document_exists_by_name(name: str) -> Optional[str]:
    """Aynı isimde doküman varsa id'sini döner."""
    data = _load()
    for doc_id, doc in data.items():
        if doc["name"] == name:
            return doc_id
    return None
