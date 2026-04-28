# 📄 DocuChat — Dokümanlarınla Sohbet Et

> RAG (Retrieval-Augmented Generation) tabanlı doküman soru-cevap sistemi.  
> **Stack:** Python · FastAPI · OpenAI GPT-4o · ChromaDB · Docker

---

## 🏗️ Mimari

```
Kullanıcı → Doküman Yükle
              ↓
         Metin Çıkarma (PDF/DOCX/TXT)
              ↓
         Metin Temizleme
              ↓
         Chunking (1000 karakter, 200 örtüşme)
              ↓
         OpenAI Embedding (text-embedding-3-small)
              ↓
         ChromaDB'ye Kayıt

Kullanıcı → Soru Sor
              ↓
         Soruyu Vektöre Çevir
              ↓
         ChromaDB'de Benzer Chunk'ları Bul
              ↓
         GPT-4o-mini ile Cevap Üret (Streaming)
              ↓
         Kaynaklarla Birlikte Göster
```

---

## 🚀 Kurulum ve Çalıştırma

### Yöntem 1 — Docker (Önerilen)

```bash
# 1. Repoyu klonla
git clone https://github.com/KULLANICI_ADI/docuchat.git
cd docuchat

# 2. Ortam dosyasını oluştur
cp .env.example .env
# .env dosyasını aç ve OPENAI_API_KEY değerini gir

# 3. Başlat
docker compose up --build

# Tarayıcıda aç:
# http://localhost:8000
```

### Yöntem 2 — Manuel (Geliştirme)

```bash
# Python 3.12 gerekli

cd backend
pip install -r requirements.txt

cp .env.example .env
# .env içindeki OPENAI_API_KEY değerini gir

uvicorn app.main:app --reload --port 8000
```

Frontend'i ayrı bir tarayıcı sekmesinde aç:
```bash
# frontend/index.html içindeki API sabitini değiştir:
# const API = 'http://localhost:8000/api';
```

---

## 📡 API Endpoints

| Method | Endpoint | Açıklama |
|--------|----------|----------|
| GET | `/api/health` | Sağlık kontrolü |
| POST | `/api/documents/upload` | Dosya yükle (çoklu) |
| GET | `/api/documents/` | Doküman listesi |
| DELETE | `/api/documents/{id}` | Doküman sil |
| POST | `/api/chat/ask` | Soru sor (tek seferlik) |
| POST | `/api/chat/stream` | Soru sor (streaming SSE) |
| POST | `/api/chat/summarize` | Özet çıkar |

**Swagger UI:** http://localhost:8000/api/docs

---

## ✨ Özellikler

- ✅ TXT, PDF, DOC, DOCX format desteği
- ✅ Çoklu doküman yükleme ve analiz
- ✅ Metin çıkarma ve temizleme
- ✅ Örtüşmeli chunking (bağlam kaybı önlenir)
- ✅ OpenAI embedding ile vektörizasyon
- ✅ ChromaDB ile kalıcı vektör depolama
- ✅ Cosine similarity ile semantik arama
- ✅ GPT-4o-mini ile cevap üretimi
- ✅ **Streaming response** (kelime kelime akış)
- ✅ **Kaynak gösterme** (hangi dokümandan, kaç % benzerlik)
- ✅ Özet çıkarma
- ✅ Çoklu doküman üzerinden birleşik cevap
- ✅ **Docker** desteği
- ✅ Modern, dark-mode arayüz

---

## 🗂️ Proje Yapısı

```
docuchat/
├── backend/
│   ├── app/
│   │   ├── main.py              # FastAPI uygulaması
│   │   ├── config.py            # Ayarlar (pydantic-settings)
│   │   ├── models.py            # Request/Response modelleri
│   │   ├── routers/
│   │   │   ├── documents.py     # Yükleme, listeleme, silme
│   │   │   └── chat.py          # Soru-cevap, streaming, özet
│   │   └── services/
│   │       ├── document_processor.py  # Metin çıkarma + chunking
│   │       ├── vector_store.py        # ChromaDB işlemleri
│   │       ├── llm_service.py         # OpenAI entegrasyonu
│   │       └── metadata_store.py      # Doküman metadata (JSON)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   └── index.html               # Tek dosya SPA arayüz
├── docker-compose.yml
├── .env.example
└── README.md
```

---

## 🔑 Ortam Değişkenleri

| Değişken | Açıklama | Varsayılan |
|----------|----------|-----------|
| `OPENAI_API_KEY` | OpenAI API anahtarı | **Zorunlu** |
| `CHAT_MODEL` | Kullanılacak LLM | `gpt-4o-mini` |
| `EMBEDDING_MODEL` | Embedding modeli | `text-embedding-3-small` |
| `CHUNK_SIZE` | Chunk karakter boyutu | `1000` |
| `CHUNK_OVERLAP` | Örtüşme miktarı | `200` |
| `TOP_K` | Arama sonuç sayısı | `5` |

---

## 💡 Kullanım

1. Sol panelden dosya yükle (sürükle-bırak desteklenir)
2. Bir veya birden fazla doküman seç
3. Soru yaz ve Enter'a bas
4. Cevap gerçek zamanlı akacak, altında kaynaklar gösterilecek
5. "✨ Özetle" butonuyla seçili dokümanların özetini al

---

## 📝 Notlar

- Maksimum dosya boyutu: 20 MB
- Doküman verileri `uploads_vol/` ve `chroma_vol/` klasörlerinde kalıcı saklanır
- `gpt-4o-mini` modeli çok ekonomiktir (~1000 soru = ~1$)
- Türkçe dokümanlar ve sorular tam desteklenmektedir
