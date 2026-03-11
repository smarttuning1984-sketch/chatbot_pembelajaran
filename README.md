# Chatbot Pembelajaran Mekanik Mobil Indonesia 🚗

Chatbot bertenaga AI yang terintegrasi dengan dokumen dari Google Drive, dibangun dengan platform **Dify** (open-source) untuk memberikan solusi pembelajaran dan konsultasi mekanik mobil Indonesia.

## 🎯 Fitur Utama

- **Integrasi Google Drive**: Otomatis mengambil dokumen dari folder Google Drive yang ditentukan
- **Knowledge Base**: Semua dokumen dikonversi menjadi knowledge base yang dapat di-query
- **Multi-Format Support**: Mendukung PDF, DOCX, Google Docs, Google Sheets, dan file teks
- **Bahasa Indonesia**: Bot menjawab pertanyaan dalam Bahasa Indonesia dengan istilah teknis bengkel
- **REST API**: Akses chatbot melalui API untuk integrasi ke aplikasi lain
- **Self-Hosted**: Jalankan di server Anda sendiri dengan Docker
- **🆕 Auto-Sync**: Continuous synchronization dengan auto-reconnect & resilience
- **🆕 Parallel Processing**: 5-10x lebih cepat untuk ribuan file

## 📋 Prasyarat

- Docker & Docker Compose
- Python 3.8+
- Google Service Account credentials (untuk akses Google Drive)
- Internet connection

## 🚀 Quick Start

### 1. Clone Repository

```bash
git clone https://github.com/smarttuning1984-sketch/chatbot_pembelajaran.git
cd chatbot_pembelajaran/dify-chatbot
```

### 2. Setup Environment

```bash
# Buat & aktifkan Python virtual environment
python3 -m venv venv
source venv/bin/activate  # Linux/macOS
# atau: venv\Scripts\activate  (Windows)

# Install dependencies
pip install -r requirements.txt

# Copy credentials.json (dapatkan dari Google Cloud Console)
cp /path/to/credentials.json ./credentials.json
```

### 3. Jalankan Dify Server

```bash
# Clone & jalankan Dify di folder terpisah
cd /tmp
git clone https://github.com/langgenius/dify.git
cd dify/docker
docker compose -f docker-compose.yaml up -d

# Tunggu ~3 menit hingga semua services ready
docker compose -f docker-compose.yaml ps
```

### 4. Setup Admin Account & API Key

1. Buka browser: **http://localhost**
2. Buat admin account (email + password)
3. Login → Account → Settings → **API Keys**
4. Create new API key → copy key (format: `sk-...`)

### 5. Jalankan Ingestion

Kembali ke folder `dify-chatbot`:

```bash
# Set environment variables
export DIFY_BASE_URL="http://localhost"
export DIFY_API_KEY="sk-xxx"  # dari step 4
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"

# Run ingestion script
bash run.sh
```

Script akan:
1. Membaca daftar folder dari Google Drive
2. Download & convert semua dokumen menjadi teks
3. Upload ke Dify knowledge base
4. Siap untuk chatbot query

## 📁 Struktur Project

```
chatbot_pembelajaran/
├── README.md                    # File ini
├── .gitignore                   # Git ignore patterns
└── dify-chatbot/               # Folder utama project
    ├── requirements.txt         # Python dependencies
    ├── credentials.json         # ⚠️ NOT INCLUDED (tambahkan sendiri)
    ├── .env.example             # Template environment variables
    │
    ├── google_drive_ingest.py   # Script utama ingestion
    ├── run.sh                   # Script runner dengan validation
    ├── setup.sh                 # Setup checker
    ├── check-dify.sh            # Cek status Dify
    │
    ├── README.md                # Dokumentasi detail
    ├── QUICKSTART.md            # Quick start guide
    ├── setup-guide.md           # Setup guide lengkap
    │
    └── venv/                    # ⚠️ NOT INCLUDED (local only)
```

## 🔑 Environment Variables

Buat file `.env` atau export variables:

```bash
# Dify
DIFY_BASE_URL="http://localhost"          # URL Dify server
DIFY_API_KEY="sk-xxx"                     # API key dari dashboard

# Google Drive
GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"
```

Atau gunakan `.env.example` sebagai template.

## 🗂️ Google Drive Folders

Script ini terintegrasi dengan folder Google Drive berikut:

```python
FOLDER_IDS = [
    "12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z",  # Folder 1
    "1Y2SLCbyHoB53BaQTTwRta2T6dv_drRll",  # Folder 2
    "1CHz8UWZXfJtXlcjp9-FPAo-t_KkfTztW",  # Folder 3
    "1_SsZ7SkaZxvXUZ6RUAA_o7WR_GAtgEwT",  # Folder 4
]
```

**Catatan**: Share folder ini ke service account agar dapat diakses.

## 📊 Menggunakan Chatbot

### Via Dify Web UI

1. Buka: http://localhost
2. Buat **Chat** app
3. Enable **Knowledge** → pilih knowledge base
4. Set system prompt (contoh untuk mekanik):

```
Kamu adalah asisten virtual untuk mekanik mobil Indonesia.
Jawab dalam Bahasa Indonesia dengan istilah teknis bengkel.
Jika tidak tahu, minta klarifikasi dari pengguna.
```

5. Publish dan test langsung

### Via REST API

```bash
curl -X POST "http://localhost/api/v1/chat-messages" \
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

## 🐛 Troubleshooting

| Problem | Solution |
|---------|----------|
| `Connection refused localhost` | Pastikan `docker compose up -d` running di `/tmp/dify/docker` |
| `API key invalid` | Buat ulang key di Settings → API Keys |
| `FileNotFoundError: credentials.json` | Pastikan file ada di folder `dify-chatbot/` |
| `Timeout saat ingestion` | Normal untuk file besar, tunggu atau jalankan folder per folder |
| JSON parse error | Pastikan credentials.json valid JSON (tidak ada trailing comma) |

Lihat `setup-guide.md` untuk troubleshooting lebih lengkap.

## ⚙️ Maintenance

### Stop Dify
```bash
cd /tmp/dify/docker
docker compose down
```

### Lihat Logs
```bash
docker compose logs -f api
```

### Restart Services
```bash
docker compose restart
```

### Update Dokumentasi
Edit `google_drive_ingest.py` untuk:
- Menambah folder baru
- Mengubah format ekstraksi dokumen
- Menambah preprocessing

## 🚀 Deployment

Untuk production:

1. **Setup VPS/Server** dengan Docker
2. **Configure HTTPS** (SSL certificate)
3. **Setup Authentication** di layer aplikasi
4. **Use API Gateway** (nginx/traefik) untuk rate limiting
5. **Monitor & Logging** (ELK stack atau cloud monitoring)
6. **Backup Knowledge Base** secara berkala

## 📚 Dokumentasi Lengkap

- [QUICKSTART.md](dify-chatbot/QUICKSTART.md) - Quick start guide (5 menit)
- [setup-guide.md](dify-chatbot/setup-guide.md) - Setup guide detail
- [Dify Documentation](https://docs.dify.ai) - Documentation resmi Dify
- [Google Drive API](https://developers.google.com/docs/api) - Google Drive API docs

## 📝 License

MIT License - Lihat LICENSE file untuk detail

## 🤝 Contributing

Kontribusi welcome! Silakan:

1. Fork repository
2. Buat branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add some AmazingFeature'`)
4. Push ke branch (`git push origin feature/AmazingFeature`)
5. Buka Pull Request

## 📞 Support

Untuk pertanyaan atau  issues:

- 📧 Email: [contact-info]
- 🐛 GitHub Issues: [GitHub Issues link]
- 💬 Discussions: [GitHub Discussions link]

---

**Build dengan ❤️ untuk komunitas mekanik Indonesia** 🚗