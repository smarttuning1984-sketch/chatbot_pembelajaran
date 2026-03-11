# ⚡ Quick Performance Reference

## Estimasi Waktu Memproses Ribuan File

### Standard (Sequential) Processing
```
100 file   (avg 5s/file) → 8 menit
1,000 file (avg 5s/file) → 1.5 jam
5,000 file (avg 5s/file) → 7 jam
10,000 file (avg 5s/file) → 14 jam
```

### Optimized (Parallel + Batch Upload)
```
100 file   (5 workers) → 2 menit
1,000 file (5 workers) → 15 menit
5,000 file (5 workers) → 1.5 jam
10,000 file (10 workers) → 2.5 jam
```

**Speedup: 5-10x lebih cepat** ⚡

---

## Faktor Kecepatan (dari cepat ke lambat)

| Factor | Impact | Solution |
|--------|--------|----------|
| **Network Speed** | 🔴 CRITICAL | Gunakan koneksi 100Mbps+ |
| **API Latency** | 🟠 HIGH | Setup Dify lokal (localhost) |
| **File Size** | 🟠 HIGH | Skip file > 100MB |
| **CPU Power** | 🟡 MEDIUM | Use 8+ core processor |
| **Parallel Workers** | 🟡 MEDIUM | Set 5-10 workers |

---

## 🚀 Mode Operasi

### Mode 1: Quick Test (10-100 file)
```bash
python google_drive_ingest.py  # Sequential OK
# Waktu: < 5 menit
```

### Mode 2: Normal (100-1000 file)
```bash
python parallel_ingest.py --workers 5
# Waktu: 15 menit - 1 jam
# Checkpoint auto-resume enabled
```

### Mode 3: Large Scale (1000+ file)
```bash
# Terminal 1: Folder 1 & 2
python parallel_ingest.py --workers 10 --folder-id 12ffd7Gq...

# Terminal 2: Folder 3 & 4
python parallel_ingest.py --workers 10 --folder-id 1Y2SLCby...

# Resume jika ada error:
python parallel_ingest.py --resume --workers 10
# Waktu: 1-3 jam untuk 5000 file
```

### Mode 4: Ultra High Scale (10000+ file)
```bash
# Setup Cloud Processing (AWS Lambda / Google Cloud Run)
# OR
# Linux server dengan 16+ cores dan 32GB RAM
# Start 20 parallel workers (2-3 instances)
# Waktu: 2-4 jam
```

---

## 📊 Comparison Table

| Scenario | Sequential | Parallel (5x) | Parallel (10x) |
|----------|-----------|---------------|----------------|
| 100 | 8 min | 2 min | 1 min |
| 500 | 40 min | 8 min | 4 min |
| 1,000 | 1.5h | 18 min | 9 min |
| 5,000 | 7h | 1.5h | 45 min |
| 10,000 | 14h | 3h | 1.5h |

---

## 💡 Tips Mempercepat

### Hardware
- [ ] Gunakan SSD (bukan HDD)
- [ ] Minimal 8GB RAM, ideal 16GB+
- [ ] 8+ cores CPU
- [ ] Koneksi 100Mbps+

### Software
- [ ] Update library: `pip install --upgrade PyPDF2 python-docx`
- [ ] Skip binary files (images, videos)
- [ ] Set workers = CPU cores / 2

### Configuration
```bash
# Fast setup
export DIFY_BASE_URL="http://localhost"  # Not cloud
export MAX_WORKERS=8  # Adjust to CPU cores
python parallel_ingest.py
```

---

## 🐛 Bottleneck Analysis

### Jika lambat di **Download** (> 3s/file)
```
✓ Upgrade network
✓ Reduce file size
✓ Use bulk export API
```

### Jika lambat di **Parse** (> 2s/file)
```
✓ Use faster PDF library: pdfplumber
✓ Disable OCR
✓ Upgrade CPU
```

### Jika lambat di **Upload** (> 2s/file)
```
✓ Run Dify locally (http://localhost)
✓ Batch upload (10 docs per API call)
✓ Use faster network
```

---

## ✅ Checklist untuk 10,000 File

- [ ] Setup Dify lokal (tidak cloud) → `http://localhost`
- [ ] Test dengan 100 file dulu
- [ ] Configure workers = (CPU cores - 2)
- [ ] Enable checkpoint resume
- [ ] Set timeout tinggi (> 60s)
- [ ] Monitor dengan logging
- [ ] Split ke multiple terminals jika perlu
- [ ] Backup knowledge base berkala

---

## 🔥 Pro Tips

**Run multiple parallel instances:**
```bash
# Terminal 1
python parallel_ingest.py --workers 8 --folder-id 12ffd7Gq...

# Terminal 2
python parallel_ingest.py --workers 8 --folder-id 1Y2SLCby...

# Terminal 3
python parallel_ingest.py --workers 8 --folder-id 1CHz8UW...

# Terminal 4
python parallel_ingest.py --workers 8 --folder-id 1_SsZ7S...

# Total: 32 workers, processing 4 folders in parallel
# Estimated time for 10,000 file: 30-45 menit!
```

**Monitor progress:**
```bash
# Check checkpoint status anytime
python parallel_ingest.py --list-checkpoints

# Watch logs
tail -f ingestion.log
```

---

**Butuh bantuan? Lihat:** [PERFORMANCE.md](PERFORMANCE.md) untuk analisis detail
