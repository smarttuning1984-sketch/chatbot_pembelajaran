# Setup Chatbot Mekanik Mobil dengan Dify

## Prasyarat
- Docker & Docker Compose
- Python 3.8+
- Google Service Account credentials

## Langkah 1: Setup Dify Server

### Opsi A: Jalankan Dify secara lokal dengan Docker

```bash
# Clone repository Dify
cd /tmp
git clone https://github.com/langgenius/dify.git
cd dify

# Jalankan dengan Docker Compose
docker compose up -d

# Tunggu ~2-3 menit hingga semua service aktif
# Cek status
docker compose ps
```

Dify akan tersedia di `http://localhost:3000`.

### Opsi B: Gunakan Dify Cloud
- Buat akun di https://app.dify.ai
- Buat API key baru
- Catat: `DIFY_BASE_URL` dan `DIFY_API_KEY`

---

## Langkah 2: Setup Environment Variables

Di terminal di folder `dify-chatbot`, set environment:

```bash
# Set Google credentials
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/credentials.json"

# Set Dify config
# Jika lokal:
export DIFY_BASE_URL="http://localhost:3000"
export DIFY_API_KEY="your-api-key-here"

# Jika cloud:
export DIFY_BASE_URL="https://api.dify.ai"
export DIFY_API_KEY="your-cloud-api-key"
```

> **Catatan**: Di lokal Docker, Anda perlu membuat API key lewat admin panel Dify terlebih dahulu.

---

## Langkah 3: Ambil API Key dari Dify

**Jika Dify lokal (Docker)**:
1. Buka browser → `http://localhost:3000`
2. Login dengan akun admin default (username/password standar dari docker-compose.yml)
3. Pergi ke **Settings** → **API Keys**
4. Buat key baru, copy nilainya → set sebagai `DIFY_API_KEY`

**Jika Dify Cloud**:
1. Buka `https://app.dify.ai` → login
2. Settings → API Keys → buat key baru

---

## Langkah 4: Jalankan Ingestion Script

```bash
cd /workspaces/Materi_pembelajaran/dify-chatbot

# Pastikan venv aktif
source venv/bin/activate

# Jalankan script
python google_drive_ingest.py
```

Expected output:
```
Found 5 file(s) in folder 12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z
  -> manual-servis.pdf application/pdf
  -> parts-catalog.xlsx application/vnd.openxmlformats-officedocument.spreadsheetml.sheet
...
Ingestion complete. Check your Dify dashboard for the new knowledge items.
```

---

## Langkah 5: Periksa Knowledge Base di Dify

1. Kembali ke dashboard Dify (`http://localhost:3000`)
2. **Knowledge** → periksa apakah dokumen sudah masuk
3. Catat **Knowledge ID** (Anda perlukan ini untuk chat bot)

---

## Langkah 6: Buat Chat Application

1. Di Dify dashboard → **Create App** → pilih **Chat**
2. Pilih Model (GPT-4, Claude, Llama2, dll.)
3. **Enable Knowledge** → pilih knowledge base yang sudah dibuat
4. Set system prompt (contoh untuk mekanik):

```
Kamu adalah asisten virtual untuk mekanik mobil di Indonesia.
Jawablah dalam Bahasa Indonesia.
Gunakan istilah teknis yang umum di bengkel.
Jika tidak yakin, minta klarifikasi dari pengguna.
```

5. **Publish** app tersebut

---

## Langkah 7: Test Chat

### Via Dify Web UI
- Buka app yang telah dipublish
- Ketik pertanyaan: "Bagaimana cara mengatasi mesin panas?"
- Bot akan menjawab berdasarkan dokumen di knowledge base

### Via REST API

```bash
# Pastikan env variables sudah set
export DIFY_API_KEY="xxx"
export DIFY_BASE_URL="http://localhost:3000"

# Test API (ganti KNOWLEDGE_ID dengan ID yang sebenarnya)
curl -X POST "$DIFY_BASE_URL/api/v1/chat-messages" \
  -H "Authorization: Bearer $DIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bagaimana cara mengatasi mesin panas?",
    "inputs": {},
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "user123"
  }'
```

---

## Troubleshooting

### Error: "Couldn't connect to server"
- Pastikan Dify sudah berjalan: `docker compose ps`
- Jika belum, jalankan: `docker compose up -d`

### Error: "Unauthorized" / API key invalid
- Periksa `DIFY_API_KEY` sudah benar
- Recreate key jika perlu

### Error: "Knowledge not found"
- Pastikan ingestion script berhasil (lihat folder Knowledge di dashboard)
- Coba run ulang: `python google_drive_ingest.py`

### Script lambat / timeout
- Folder berisi file besar? Tambahkan chunking di script
- Atau jalankan folder satu per satu dengan modifikasi `FOLDER_IDS`

---

## Deployment ke Production

Untuk production (bukan localhost):

1. **Setup Dify Cloud** atau **VPS dengan Docker**
2. **Configure SSL/HTTPS** (important untuk API security)
3. **Setup authentication** di layer aplikasi Anda
4. **Gunakan API Gateway** (traefik, nginx) untuk rate limiting
5. **Monitor & logging**: setup ELK stack atau cloud monitoring

---

Silakan ikuti langkah-langkah di atas dan laporkan jika ada error baru!
