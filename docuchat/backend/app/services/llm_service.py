from typing import List, AsyncGenerator
from openai import AsyncOpenAI
from app.config import settings

# Tek bir OpenAI istemci örneği (singleton)
_client: AsyncOpenAI | None = None


def get_client() -> AsyncOpenAI:
    global _client
    if _client is None:
        _client = AsyncOpenAI(api_key=settings.openai_api_key)
    return _client


# ──────────────────────────────────────────────
# EMBEDDING
# ──────────────────────────────────────────────

async def create_embedding(text: str) -> List[float]:
    """Tek bir metin için vektör oluşturur."""
    client = get_client()
    response = await client.embeddings.create(
        model=settings.embedding_model,
        input=text,
    )
    return response.data[0].embedding


async def create_embeddings_batch(texts: List[str]) -> List[List[float]]:
    """
    Birden fazla metin için toplu vektör oluşturur.
    API maliyetini düşürmek için batch kullanılır.
    """
    client = get_client()
    # OpenAI max 2048 input per request — büyük listeler için böl
    all_embeddings = []
    batch_size = 100

    for i in range(0, len(texts), batch_size):
        batch = texts[i : i + batch_size]
        response = await client.embeddings.create(
            model=settings.embedding_model,
            input=batch,
        )
        all_embeddings.extend([item.embedding for item in response.data])

    return all_embeddings


# ──────────────────────────────────────────────
# RAG SYSTEM PROMPT
# ──────────────────────────────────────────────

def build_system_prompt() -> str:
    return (
        "Sen bir doküman analiz asistanısın. "
        "Kullanıcıya yalnızca sağlanan BAĞLAM metinlerine dayanarak cevap ver. "
        "Eğer bağlamda yeterli bilgi yoksa bunu açıkça belirt. "
        "Cevaplarını Türkçe ver. "
        "Her zaman hangi bilginin hangi kaynaktan geldiğini belirtmeye çalış."
    )


def build_rag_prompt(question: str, context_chunks: List[dict]) -> str:
    context_parts = []
    for i, chunk in enumerate(context_chunks, start=1):
        doc_name = chunk["metadata"]["document_name"]
        context_parts.append(
            f"[Kaynak {i} - {doc_name}]\n{chunk['text']}"
        )

    context_text = "\n\n---\n\n".join(context_parts)

    return (
        f"Aşağıdaki bağlam metinlerini kullanarak soruyu yanıtla:\n\n"
        f"{context_text}\n\n"
        f"---\n\n"
        f"Soru: {question}\n\n"
        f"Cevabında kaynak numaralarına ([Kaynak 1], [Kaynak 2] vb.) atıfta bulun."
    )


# ──────────────────────────────────────────────
# NORMAL CHAT (tek seferlik cevap)
# ──────────────────────────────────────────────

async def generate_answer(question: str, context_chunks: List[dict]) -> str:
    client = get_client()
    prompt = build_rag_prompt(question, context_chunks)

    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        max_tokens=settings.max_tokens,
        temperature=0.3,  # Daha tutarlı, gerçeğe yakın cevaplar için düşük tutulur
    )
    return response.choices[0].message.content


# ──────────────────────────────────────────────
# STREAMING CHAT (anlık kelime kelime akış)
# ──────────────────────────────────────────────

async def generate_answer_stream(
    question: str, context_chunks: List[dict]
) -> AsyncGenerator[str, None]:
    client = get_client()
    prompt = build_rag_prompt(question, context_chunks)

    stream = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {"role": "system", "content": build_system_prompt()},
            {"role": "user", "content": prompt},
        ],
        max_tokens=settings.max_tokens,
        temperature=0.3,
        stream=True,
    )

    async for chunk in stream:
        delta = chunk.choices[0].delta
        if delta.content:
            yield delta.content


# ──────────────────────────────────────────────
# ÖZETLEMEaccount
# ──────────────────────────────────────────────

async def generate_summary(chunks: List[dict]) -> str:
    """Seçilen dokümanların özet çıkarımını yapar."""
    client = get_client()

    # İlk 10 chunk yeterli özet için (token sınırı)
    top_chunks = chunks[:10]
    context_parts = []
    for chunk in top_chunks:
        doc_name = chunk["metadata"]["document_name"]
        context_parts.append(f"[{doc_name}]\n{chunk['text']}")

    context_text = "\n\n---\n\n".join(context_parts)

    response = await client.chat.completions.create(
        model=settings.chat_model,
        messages=[
            {
                "role": "system",
                "content": (
                    "Sen bir özetleme asistanısın. "
                    "Verilen metinlerin ana fikirlerini Türkçe olarak açık ve anlaşılır biçimde özetle."
                ),
            },
            {
                "role": "user",
                "content": (
                    f"Aşağıdaki doküman içeriklerini özetle:\n\n{context_text}"
                ),
            },
        ],
        max_tokens=800,
        temperature=0.3,
    )
    return response.choices[0].message.content
