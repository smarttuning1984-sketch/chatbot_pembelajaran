# Quick Start - Chatbot Mekanik Mobil Indonesia

## Masalah Anda Sekarang

### ❌ Error 1: File `credentials.json` tidak ditemukan
**Status**: ✅ SUDAH DIPERBAIKI
- File sudah dicopy ke folder `dify-chatbot/`

### ❌ Error 2: Tidak bisa connect ke `localhost:3000`
**Alasan**: Dify server belum berjalan

---

## 🚀 Solusi Cepat (5 menit)

### Terminal 1: Jalankan Dify Server

```bash
# Clone Dify (hanya sekali)
cd /tmp
git clone https://github.com/langgenius/dify.git
cd dify

# Jalankan Docker
docker compose up -d

# Tunggu 2-3 menit, cek status
docker compose ps

# Buka browser → http://localhost:3000
```

**Catatan**: 
- Pertama kali mungkin butuh download image Docker (~2GB)
- Tunggu semua service "up" sebelum lanjut

### Terminal 2: Setup & Run Ingestion

Di terminal baru, di folder `dify-chatbot`:

```bash
# 1. Aktifkan venv
source venv/bin/activate

# 2. Set environment variables
export GOOGLE_APPLICATION_CREDENTIALS="$PWD/credentials.json"
export DIFY_BASE_URL="http://localhost:3000"
export DIFY_API_KEY="xxx" # (lihat langkah berikutnya)

# 3. Run setup check
bash setup.sh

# 4. Run ingestion
python google_drive_ingest.py
```

---

## 🔑 Dapatkan `DIFY_API_KEY`

### Saat Dify sudah running:

1. Buka: http://localhost:3000
2. Default login (cek docker-compose.yml):
   - **Username**: `admin`
   - **Password**: `Dify123456` (atau yang tercantum di file)
3. Pergi ke: **Settings** → **API Keys**
4. Klik **Create API Key**
5. Copy key → paste ke command:

```bash
export DIFY_API_KEY="sk-..."
```

---

## ✅ Verifikasi Ingestion Berhasil

Setelah `python google_drive_ingest.py` berjalan:

```
[INFO] Mulai ingestion dari 4 folder...

[INFO] Folder 12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z: ditemukan 5 file
[INFO]   ✓ manual-servis.pdf (12450 chars)
[INFO]   ✓ parts-catalog.xlsx (8900 chars)
...
[INFO] Ingestion selesai!
```

📊 **Buka Dify Dashboard**:
- Settings → Knowledge → periksa item yang masuk
- Catat **Knowledge ID** untuk step berikutnya

---

## 🤖 Buat Chatbot

1. Dify Dashboard → **+ Create App**
2. Pilih **Chat**
3. Pilih Model: GPT-4, Claude, Llama, dll
4. **Enable Knowledge** → pilih knowledge yang tadi dibuat
5. Set prompt system:

```
Kamu adalah asisten virtual untuk mekanik mobil Indonesia.
Jawab di Bahasa Indonesia.
Gunakan istilah bengkel yang sederhana.
```

6. **Publish** dan test

---

## 🧪 Test Chat via API

```bash
curl -X POST "http://localhost:3000/api/v1/chat-messages" \
  -H "Authorization: Bearer $DIFY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Bagaimana cara mengatasi mesin panas?",
    "inputs": {},
    "response_mode": "blocking",
    "conversation_id": "",
    "user": "user123"
  }' | jq .
```

---

## 🆘 Troubleshooting

| Error | Solusi |
|-------|--------|
| `Connection refused localhost:3000` | Jalankan `docker compose up -d` di folder dify |
| `API key invalid` | Buat ulang key di Settings → API Keys |
| `Knowledge not found` | Pastikan ingestion script sukses & refresh page |
| `File too large` | Edit `google_drive_ingest.py` tambahkan chunking |
| `Timeout` | Pastikan koneksi internet stabil, coba folder 1 per 1 |

---

## 📝 Next Steps

1. ✅ Setup Dify lokal atau cloud
2. ✅ Run ingestion script
3. ✅ Buat chatbot di Dify
4. 🔄 (Optional) Buat webapp frontend
5. 🔄 (Optional) Deploy ke production

Lihat `setup-guide.md` untuk dokumentasi lengkap.

---

**Tanya-jawab cepat?** Jalankan `bash setup.sh` untuk verifikasi setup Anda.
