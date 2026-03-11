# Performance Analysis - Memproses Ribuan File dari Google Drive

## ⏱️ Estimasi Waktu

### Per-File Breakdown (Average)

| Operasi | Waktu | Catatan |
|---------|-------|---------|
| List files dari Drive API | 0.5s | per folder (batch operation) |
| Download file (100KB avg) | 1-2s | tergantung network & ukuran |
| Parse/Convert (PDF/DOCX) | 0.5-3s | PDF kompleks bisa lebih lama |
| Upload ke Dify API | 1-2s | tergantung ukuran text + latency |
| **Total per file** | **3-8 detik** | worst case |

### Total Time Estimates

**Untuk 1000 file:**
- **Optimistic**: 1000 × 3s = **50 menit**
- **Average**: 1000 × 5s = **83 menit (~1.5 jam)**
- **Pessimistic**: 1000 × 8s = **133 menit (~2.2 jam)**

**Untuk 5000 file:**
- **Optimistic**: 5000 × 3s = **4.2 jam**
- **Average**: 5000 × 5s = **7 jam**
- **Pessimistic**: 5000 × 8s = **11 jam**

---

## 🔍 Faktor yang Mempengaruhi

### 1. **Ukuran File** (Impact: HIGH)
```
File TXT 10KB    → ~3 detik
File PDF 500KB   → ~5-8 detik
File PDF 5MB     → ~10-20 detik
File DOCX 2MB    → ~8-15 detik
```

**Solusi:**
- Kompres/split file besar sebelum upload
- Skip file > threshold

### 2. **Network Speed** (Impact: CRITICAL)
```
Internet 10Mbps  → download/upload speed ~1.2 MB/s
Internet 50Mbps  → download/upload speed ~6 MB/s
Internet 100Mbps → download/upload speed ~12 MB/s
```

**Solusi:**
- Gunakan koneksi yang cepat & stabil
- Jalankan dari server (daripada laptop)

### 3. **Dify API Latency** (Impact: HIGH)
```
Local server (localhost) → ~100ms latency
cloud.dify.ai             → ~200-500ms latency
```

**Solusi:**
- Setup Dify lokal lebih cepat
- Batch multiple uploads jika Dify support

### 4. **CPU Processing** (Impact: MEDIUM)
```
Parse PDF kompleks (500+ halaman) → 5-10 detik
Parse DOCX besar → 2-5 detik
Extract text dari gambar (OCR) → 20+ detik
```

**Solusi:**
- Upgrade CPU
- Disable OCR jika tidak perlu
- Use faster PDF library (pdfplumber)

### 5. **Google Drive API Rate Limits** (Impact: MEDIUM)
```
Free tier: 1000 queries/100s
Per-user limit: 10,000 queries/100s
```

**Solusi:**
- Gunakan service account (higher quota)
- Batch queries

---

## 🚀 Optimization Strategies

### Strategy 1: Parallel Processing

Ganti script sequential ke parallel (menggunakan multiprocessing/asyncio):

```python
from concurrent.futures import ThreadPoolExecutor, as_completed
import time

MAX_WORKERS = 5  # Adjust berdasarkan sistem

def process_files_parallel(files):
    with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
        futures = {executor.submit(process_file, f): f for f in files}
        for future in as_completed(futures):
            try:
                future.result()
            except Exception as e:
                print(f"Error: {e}")

# Expected speedup: ~3-5x faster (limited by network)
```

**Estimasi waktu dengan 5 workers:**
- 1000 file: 50 menit → **10-15 menit**
- 5000 file: 7 jam → **1.5-2 jam**

### Strategy 2: Batch Upload

Upload multiple documents sekaligus daripada satu per satu:

```python
def batch_ingest(texts, batch_size=10):
    """Upload 10 dokumen dalam 1 API call"""
    for i in range(0, len(texts), batch_size):
        batch = texts[i:i+batch_size]
        payload = {
            "objects": [
                {"type": "text", "text": t["content"], 
                 "metadata": {"filename": t["name"]}}
                for t in batch
            ]
        }
        # Single API call untuk batch
        requests.post(url, json=payload)
```

**Estimasi speedup:**
- 50% lebih cepat (1 API call per 10 docs)

### Strategy 3: Pre-filtering & Compression

Skip file yang tidak perlu / terlalu besar:

```python
# Skip criteria
SKIP_CONDITIONS = [
    lambda f: f["size"] > 100 * 1024 * 1024,  # > 100MB
    lambda f: f["mimeType"] == "application/exe",  # executables
    lambda f: "cache" in f["name"].lower(),  # temp files
]

# Size estimation
MAX_TEXT_SIZE = 1_000_000  # 1MB text
```

**Estimasi speedup:**
- 20-40% lebih cepat (dengan skip criteria yang tepat)

### Strategy 4: Chunking Large Documents

Jika text > 100KB, split jadi chunks:

```python
def chunk_text(text, chunk_size=50000, overlap=1000):
    """Split large text into overlapping chunks"""
    chunks = []
    for i in range(0, len(text), chunk_size - overlap):
        chunk = text[i:i+chunk_size]
        chunks.append(chunk)
    return chunks

# Upload setiap chunk
for i, chunk in enumerate(chunks):
    upload_to_dify(chunk, f"{filename}_part_{i}")
```

---

## 📊 Rekomendasi

### Untuk 1000 file:
```
Strategy         | Time  | Complexity
Standard         | 1.5h  | Low ✓
+ Parallel (5x)  | 20min | Medium
+ Batch Upload   | 15min | Medium
+ Filtering      | 10min | Medium-High
Combined         | 5min  | High
```

### Untuk 5000+ file:

**Fase 1: Setup**
```bash
# 1. Opsi A: Cloud processing (recommended)
# - Gunakan AWS Lambda / Google Cloud Run
# - Auto-scaling workers
# - Estimated: 1-2 jam untuk 5000 file

# 2. Opsi B: Local high-performance
# - High-end CPU (16+ cores)
# - 5-10 parallel workers
# - Estimated: 2-3 jam
```

**Fase 2: Monitoring**
```python
# Track progress
import time
from tqdm import tqdm

start_time = time.time()
for i, file in enumerate(tqdm(files)):
    process_file(file)
    if i % 100 == 0:
        elapsed = time.time() - start_time
        rate = i / elapsed
        remaining = (len(files) - i) / rate
        print(f"ETA: {remaining/60:.1f} menit")
```

---

## 💡 Best Practices

### 1. Jangan Upload Sekaligus
- Jalankan di background job
- Split per folder
- Monitor progress dengan checkpoint

### 2. Error Handling
```python
# Retry dengan exponential backoff
import time

def retry(func, max_retries=3):
    for attempt in range(max_retries):
        try:
            return func()
        except Exception as e:
            wait_time = 2 ** attempt  # 1s, 2s, 4s
            print(f"Retry in {wait_time}s...")
            time.sleep(wait_time)
```

### 3. Checkpoint & Resume
```python
# Save progress ke file
import json

def save_checkpoint(processed_files):
    with open("checkpoint.json", "w") as f:
        json.dump(processed_files, f)

def load_checkpoint():
    try:
        with open("checkpoint.json") as f:
            return json.load(f)
    except FileNotFoundError:
        return []

# Resume dari checkpoint jika ada error
processed = load_checkpoint()
remaining = [f for f in all_files if f["id"] not in processed]
```

### 4. Logging & Monitoring
```python
import logging

logging.basicConfig(
    filename="ingestion.log",
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)
logger.info(f"Started processing {len(files)} files")
```

---

## ⚡ Quick Summary

| Scenario | Time | Method |
|----------|------|--------|
| 100 file (test) | 10 menit | Standard |
| 1000 file | 1.5 jam | Standard |
| 1000 file (optimized) | 15 menit | Parallel + Batch |
| 5000 file | 7+ jam | Standard |
| 5000 file (optimized) | 1-2 jam | Cloud + Parallel |

---

## 📞 Support Scripts

Script parallel processing sudah disiapkan di folder `scripts/`:
- `parallel_ingest.py` - Multiprocessing version
- `batch_upload.py` - Batch processing
- `progress_monitor.py` - Real-time monitoring
- `checkpoint_resume.py` - Error recovery
