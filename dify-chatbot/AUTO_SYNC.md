# 🔄 Auto-Sync Feature Documentation

Continuous synchronization dari Google Drive ke Dify Knowledge Base dengan auto-reconnect & resilience.

## Features

✅ **Auto Monitoring** - Continuous file change detection
✅ **Auto Reconnect** - Exponential backoff retry mechanism
✅ **Server Health Check** - Detect & wait for server recovery
✅ **State Persistence** - Remember sync state for resumption
✅ **Graceful Shutdown** - Clean shutdown with signal handling
✅ **Detailed Logging** - Track sync activity & errors

---

## Quick Start

### Jalankan Auto-Sync

```bash
# Setup environment (jika belum)
export DIFY_BASE_URL="http://localhost"
export DIFY_API_KEY="sk-..."
export GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"

# Jalankan auto-sync
python auto_sync.py

# Dengan custom interval (default 5 menit)
python auto_sync.py --interval 600  # 10 menit

# Watch specific folder
python auto_sync.py --watch-folder 12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z
```

### Stop Auto-Sync

```bash
# Gracefully shutdown dengan Ctrl+C
# atau di terminal lain:
pkill -f auto_sync.py
```

---

## How It Works

```
┌─────────────────────────────────────────────────────────┐
│ Auto-Sync Loop (runs every 5 minutes)                  │
├─────────────────────────────────────────────────────────┤
│                                                         │
│ 1. Health Check                                         │
│    ↓ Dify server healthy?                             │
│    │   YES → continue                                  │
│    │   NO → wait for recovery (max 10 min)            │
│    └───────────────────────────────────────────────── │
│                                                         │
│ 2. List Changed Files                                  │
│    ↓ Query Google Drive for files modified since      │
│    │  last sync time                                   │
│    └───────────────────────────────────────────────── │
│                                                         │
│ 3. Process Each File                                   │
│    ├─ Download & Convert (with retry)                │
│    ├─ Check hash (skip if already synced)            │
│    ├─ Upload to Dify (with retry)                    │
│    └─ Update sync state                              │
│                                                         │
│ 4. Save State                                          │
│    └─ Persist to sync_state.json for resumption      │
│                                                         │
│ 5. Wait for Next Cycle                                 │
│    └─ Sleep 5 minutes before next sync                │
│                                                         │
└─────────────────────────────────────────────────────────┘
```

---

## Configuration

### Environment Variables

```bash
# Required
DIFY_API_KEY="sk-..."               # API key dari Dify dashboard
DIFY_BASE_URL="http://localhost"    # URL Dify server
GOOGLE_APPLICATION_CREDENTIALS="./credentials.json"  # Google creds

# Optional (dalam script)
SYNC_INTERVAL=300                   # Sync setiap X detik (default 5 menit)
HEALTH_CHECK_INTERVAL=30            # Health check setiap X detik
MAX_RETRIES=5                       # Max retry attempts
MAX_BACKOFF=300                     # Max backoff time (5 menit)
```

### Command Line Options

```bash
# Custom sync interval (seconds)
python auto_sync.py --interval 600

# Watch specific folder only
python auto_sync.py --watch-folder 12ffd7GqHAiy...

# Custom health check interval
python auto_sync.py --health-check-interval 60
```

---

## Reconnect Logic

### Exponential Backoff

Jika terjadi error (network/server), script akan retry dengan delay yang meningkat:

```
Attempt 1: 2 seconds → failed
Attempt 2: 4 seconds → failed
Attempt 3: 8 seconds → failed
Attempt 4: 16 seconds → failed
Attempt 5: 32 seconds → failed
(Max: 300 seconds / 5 menit)
```

### Error Types Handled

```
✓ Connection Error (network down)
✓ Timeout Error (server slow)
✓ HTTP 500+ Errors (server error)
✓ Google Drive API errors
✓ File parsing errors
```

### Recovery Strategy

```
Jika Dify down:
1. Health check gagal → log "Server down"
2. Wait up to 10 menit for recovery
3. Retry health check setiap 2-30 detik (exponential)
4. Kalo recover → resume sync
5. Kalo timeout → wait untuk next sync cycle
```

---

## State Management

### sync_state.json

Track progress untuk resumption:

```json
{
  "last_sync_time": "2026-03-11T21:45:00.123456",
  "synced_files": {
    "file_id_1": "hash_value",
    "file_id_2": "hash_value"
  },
  "failed_files": {
    "file_id_3": "reason for failure",
    "file_id_4": "another reason"
  },
  "failed_count": 2,
  "success_count": 45
}
```

### Checkpoint Resume

Jika process di-interrupt/restart:
1. Load `sync_state.json`
2. Resume dari `last_sync_time`
3. Only process files modified setelah `last_sync_time`
4. Skip files yang sudah ter-sync (compare hash)

---

## Monitoring

### Log File: `auto_sync.log`

Real-time monitoring:

```bash
# Tail logs (live)
tail -f auto_sync.log

# Search untuk errors
grep ERROR auto_sync.log

# Monitor sync progress
grep "Processing\|Sync complete" auto_sync.log
```

### Log Levels

```
INFO    - Sync start/end, files processed
WARNING - Server down, retry attempts
ERROR   - Failed uploads, critical errors
DEBUG   - Detailed processing info (not by default)
```

### Example Log Output

```
2026-03-11 21:45:00 - INFO - Starting auto-sync loop...
2026-03-11 21:45:05 - INFO - Dify server is healthy
2026-03-11 21:45:10 - INFO - Syncing folder 12ffd7Gq...
2026-03-11 21:45:12 - INFO - Found 3 files to process
2026-03-11 21:45:15 - INFO - Processing manual-servis.pdf...
2026-03-11 21:45:20 - INFO - ✓ manual-servis.pdf (12450 chars)
2026-03-11 21:47:45 - INFO - Folder sync complete: 3 success, 0 failed
2026-03-11 21:47:50 - INFO - Sync cycle complete: 12 success, 0 failed
2026-03-11 21:47:50 - INFO - Next sync in 300s
```

---

## Advanced Usage

### Run as Background Service (Linux)

Create systemd service:

```bash
# /etc/systemd/system/dify-auto-sync.service
[Unit]
Description=Dify Auto Sync Service
After=network.target

[Service]
Type=simple
User=ubuntu
WorkingDirectory=/opt/dify-chatbot
ExecStart=/usr/bin/python3 auto_sync.py
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Jalankan service:

```bash
sudo systemctl start dify-auto-sync
sudo systemctl enable dify-auto-sync
sudo systemctl status dify-auto-sync

# Monitor logs
sudo journalctl -u dify-auto-sync -f
```

### Multiple Instances

Jalankan beberapa instance untuk folder berbeda:

```bash
# Terminal 1: Watch folder 1
python auto_sync.py --watch-folder 12ffd7Gq... --interval 300

# Terminal 2: Watch folder 2
python auto_sync.py --watch-folder 1Y2SLCby... --interval 300

# Terminal 3: Watch folder 3
python auto_sync.py --watch-folder 1CHz8UW... --interval 300

# Terminal 4: Watch folder 4
python auto_sync.py --watch-folder 1_SsZ7S... --interval 300
```

### Docker Container

Run di container (recommended untuk production):

```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY auto_sync.py .
COPY credentials.json .

CMD ["python", "auto_sync.py", "--interval", "300"]
```

Build & run:

```bash
docker build -t dify-auto-sync .
docker run -d \
  -e DIFY_API_KEY="sk-..." \
  -e DIFY_BASE_URL="http://localhost" \
  -e GOOGLE_APPLICATION_CREDENTIALS="/app/credentials.json" \
  dify-auto-sync
```

---

## Troubleshooting

### Script stops immediately

❌ **Problem**: Auto-sync tidak berjalan
✅ **Solution**:
```bash
# Check credentials
python -c "import json; json.load(open('credentials.json'))"

# Check Dify connection
curl -X GET "http://localhost/api/version" -H "Authorization: Bearer $DIFY_API_KEY"

# Check logs
tail -20 auto_sync.log
```

### "Server is down" messages

❌ **Problem**: Continuous server down warnings
✅ **Solution**:
```bash
# Verify Dify running
docker compose ps

# Check Dify logs
docker compose logs api

# Restart Dify
docker compose restart
```

### High memory usage

❌ **Problem**: Script consuming lot of memory
✅ **Solution**:
- Reduce `--interval` (scan lebih jarang)
- Watch specific folder (reduce load)
- Check for very large files (> 100MB)
- Aumentar `--health-check-interval`

### Failed uploads keep happening

❌ **Problem**: Same files keep failing
✅ **Solution**:
```bash
# Check failed_files in sync_state.json
cat sync_state.json | jq .failed_files

# Remove problematic file hash to force re-sync
python -c "
import json
with open('sync_state.json') as f:
    state = json.load(f)
# Remove specific file from synced_files
del state['synced_files']['problematic_file_id']
with open('sync_state.json', 'w') as f:
    json.dump(state, f, indent=2)
"

# Restart auto-sync
```

---

## Performance Considerations

### Tuning Sync Interval

```
Very Frequent (30s)   → High load, frequent API calls
Frequent (5m)         → Balanced, recommended
Slow (30m)            → Low load, delayed sync

Recommendation: 5-10 menit untuk most use cases
```

### Network Impact

```
Per cycle:
- List files:  1 API call (minimal)
- Download:   1 call per file
- Upload:     1 API call per file
- Health:     1 call per cycle

Estimation: 50 files × 2 API calls = 100 API calls per 5 min
```

### Storage Requirements

```
sync_state.json  → ~1-5 KB (small)
auto_sync.log    → grows over time, rotate as needed
Total overhead   → minimal
```

---

## Best Practices

### 1. Monitoring
- [ ] Check logs regularly
- [ ] Set up alerts for errors
- [ ] Monitor sync_state.json

### 2. Maintenance
- [ ] Rotate log files periodically
- [ ] Clean failed_files when resolved
- [ ] Test reconnect by stopping Dify

### 3. Deployment
- [ ] Run as systemd service or Docker
- [ ] Use reloatable configuration
- [ ] Back up sync_state.json

### 4. Performance
- [ ] Start with default interval (300s)
- [ ] Monitor CPU/memory impact
- [ ] Tune as needed

---

## API Reference

### AutoSyncManager

```python
from auto_sync import AutoSyncManager, StateManager

# Initialize
manager = AutoSyncManager(
    folder_ids=["12ffd7Gq...", "1Y2SLCby..."],
    sync_interval=300
)

# Run
manager.run()

# Programmatic access to state
state = StateManager.load()
print(f"Synced: {state.success_count}")
print(f"Failed: {state.failed_count}")
```

### RetryManager

```python
from auto_sync import RetryManager

retry_mgr = RetryManager(max_retries=5)
result = retry_mgr.execute_with_retry(some_function, arg1, arg2)
```

### HealthChecker

```python
from auto_sync import HealthChecker

checker = HealthChecker("http://localhost", "sk-...")
if checker.check():
    print("Server is healthy")
else:
    checker.wait_until_healthy(timeout=600)
```

---

**Running auto_sync = Set it and forget it!** 🚀
