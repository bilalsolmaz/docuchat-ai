FROM python:3.12-slim

# Çalışma dizini
WORKDIR /app

# Sistem bağımlılıkları (PyMuPDF için)
RUN apt-get update && apt-get install -y \
    gcc \
    g++ \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Python bağımlılıkları
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Uygulama kodu
COPY . .

# Dizinler
RUN mkdir -p uploads chroma_db

# Port
EXPOSE 8000

# Başlatma
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--timeout-keep-alive", "300"]
