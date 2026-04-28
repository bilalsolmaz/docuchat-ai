# 🚀 GitHub'a Yükleme ve Teslim Rehberi

## Adım 1 — Git Başlat

```bash
cd docuchat

git init
git add .
git commit -m "feat: DocuChat RAG sistemi - ilk commit"
```

## Adım 2 — GitHub Repository Oluştur

1. https://github.com/new adresine git
2. Repository adı: `docuchat` (veya istediğin isim)
3. **Public** seç (jüri görebilsin)
4. README ekleme (zaten var)
5. "Create repository" tıkla

## Adım 3 — Remote Ekle ve Push Et

```bash
git remote add origin https://github.com/KULLANICI_ADIN/docuchat.git
git branch -M main
git push -u origin main
```

## Adım 4 — .env Kontrolü

`.env` dosyasının push'lanmadığını doğrula:
```bash
git status   # .env görünmemeli
```

---

## 🎬 Demo Video Çekimi (Teslim Şartı)

### Önerilen akış (~3-4 dakika):

1. **[0:00]** Projeyi çalıştır: `docker compose up --build`
2. **[0:30]** Tarayıcıda http://localhost:8000 aç — arayüzü göster
3. **[0:45]** Bir PDF yükle, chunk sayısını göster
4. **[1:00]** Bir DOCX yükle — çoklu doküman
5. **[1:20]** Soru sor — streaming cevabı göster
6. **[1:45]** Kaynak chiplerini göster (% skor)
7. **[2:00]** "Özetle" butonunu kullan
8. **[2:20]** API dokümantasyonunu göster: http://localhost:8000/api/docs
9. **[2:40]** Kod yapısını kısaca gez (document_processor, vector_store, llm_service)

### Ücretsiz kayıt araçları:
- **OBS Studio** (ücretsiz, Windows/Mac/Linux)
- **Loom** (ücretsiz, tarayıcıdan)

---

## ✅ Teslim Kontrol Listesi

- [ ] GitHub repository oluşturuldu ve kod push'landı
- [ ] README.md mevcut (kurulum + kullanım açıklaması)
- [ ] `.env` dosyası commit'lenmedi (sadece `.env.example`)
- [ ] Docker ile `docker compose up` çalışıyor
- [ ] Demo video çekildi ve linki README'ye eklendi
- [ ] http://localhost:8000 arayüzü açılıyor
- [ ] http://localhost:8000/api/docs Swagger açılıyor

---

## 💬 Jüriye Anlatacakların

**Teknik mimari:**
> "RAG mimarisini kullandık. Dokümanlar yüklendiğinde önce metin çıkarılıp temizleniyor, 
> ardından 1000 karakterlik örtüşen chunk'lara bölünüyor. Her chunk OpenAI'ın 
> text-embedding-3-small modeli ile vektöre dönüştürülüp ChromaDB'ye kaydediliyor.
> Kullanıcı soru sorduğunda soru da vektöre dönüştürülüyor, cosine similarity ile 
> en alakalı 5 chunk bulunuyor ve GPT-4o-mini bunları bağlam olarak kullanarak 
> streaming cevap üretiyor."

**Neden ChromaDB?**
> "Hafif, persistent, metadata filtreleme destekli. Üretim için Pinecone'a geçilebilir."

**Neden gpt-4o-mini?**
> "Çok ekonomik (gpt-4o'nun ~10'da biri), Türkçe desteği mükemmel, 128k context."
