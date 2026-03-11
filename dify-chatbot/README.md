# Dify Chatbot with Google Drive Integration 🚗

Chatbot terintegrasi dengan dokumen dari Google Drive menggunakan platform [Dify](https://github.com/langgenius/dify) - open source LLM orchestration platform.

## Overview

1. **Setup Dify** – Self-hosted dengan Docker atau gunakan cloud service
2. **Google Drive Credentials** – Service account dengan akses ke folders
3. **Download & Convert** – Ekstrak konten dari PDF, DOCX, Google Docs/Sheets
4. **Ingest ke Knowledge Base** – Upload ke Dify via API
5. **Chat Application** – Query knowledge base dengan chatbot

## 🚀 Quick Start (5 Menit)

Lihat [QUICKSTART.md](QUICKSTART.md)

## Requirements

- Python 3.8+
- Docker & Docker Compose (untuk Dify)
- Google Service Account credentials

Dependencies:

```
google-api-python-client
google-auth-httplib2
google-auth-oauthlib
requests
python-docx
PyPDF2
```

Setup environment:

```bash
python -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

## Configuration

```bash
export GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"
export DIFY_API_KEY="sk-..."
export DIFY_BASE_URL="http://localhost"
```

Atau gunakan `.env.example` sebagai template.

## 🎯 Two Processing Options

### Standard (Sequential) - Untuk Testing
```bash
bash run.sh
# Waktu: ~5 detik per file
```

### Parallel (Optimized) - Untuk 100-10,000 file ⚡
```bash
python parallel_ingest.py --workers 5
# 5-10x lebih cepat!
# Dengan checkpoint & auto-resume
```

### Auto-Sync (NEW!) - Untuk Continuous Sync 🔄
```bash
# Continuous monitoring & syncing dari Google Drive
bash start-auto-sync.sh

# Features:
# ✓ Auto-detect file changes
# ✓ Auto-reconnect on errors (exponential backoff)
# ✓ Server health monitoring
# ✓ State persistence & resume
# ✓ Graceful shutdown
```

**Perlu tahu estimasi waktu?** Lihat [PERFORMANCE_QUICK_REF.md](PERFORMANCE_QUICK_REF.md)
**Butuh continuous sync?** Lihat [AUTO_SYNC.md](AUTO_SYNC.md)

---

## 📁 Scripts Available

| Script | Purpose | Best For |
|--------|---------|----------|
| `run.sh` | Simple sequential ingestion | Testing, < 100 file |
| `parallel_ingest.py` | Parallel processing (optimized) | 100-10000 file |
| `auto_sync.py` | Continuous auto-sync | Production, ongoing sync |
| `start-auto-sync.sh` | Start auto-sync with config | Easy startup |
| `monitor-auto-sync.sh` | Monitor sync status | Check progress |
| `check-dify.sh` | Verify Dify server status | Debugging |
| `setup.sh` | Setup environment checker | First-time setup |

## 📊 Performance

**Time Estimates:**

| Files | Sequential | Parallel (5x) |
|-------|-----------|---------------|
| 100 | 8 min | 2 min |
| 1000 | 1.5h | 18 min |
| 5000 | 7h | 1.5h |
| 10000 | 14h | 3h |

See [PERFORMANCE_QUICK_REF.md](PERFORMANCE_QUICK_REF.md) for detailed analysis.

---

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - 5-minute setup
- **[setup-guide.md](setup-guide.md)** - Complete setup guide
- **[AUTO_SYNC.md](AUTO_SYNC.md)** - 🔄 Auto-sync with auto-reconnect
- **[PERFORMANCE_QUICK_REF.md](PERFORMANCE_QUICK_REF.md)** - ⚡ Waktu estimasi & tips
- **[PERFORMANCE.md](PERFORMANCE.md)** - Deep dive performance analysis

---

The following script demonstrates how to list files in a folder and upload their text to Dify.