#!/usr/bin/env python3
"""
Parallel Ingestion Script for Large-Scale Document Processing
Usage: python parallel_ingest.py [--workers 5] [--folder-id id] [--batch-size 10]
"""

import os
import io
import sys
import time
import json
import argparse
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from datetime import datetime

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader
from docx import Document

# ============== CONFIG ==============
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
MAX_RETRIES = 3
RETRY_WAIT = 2
TIMEOUT = 60
BATCH_SIZE = 10
MAX_WORKERS = 5
CHECKPOINT_FILE = "ingestion_checkpoint.json"
LOG_FILE = "ingestion.log"

# ============== LOGGING ==============
def log(level, message):
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log_msg = f"[{timestamp}] [{level}] {message}"
    print(log_msg)
    with open(LOG_FILE, "a") as f:
        f.write(log_msg + "\n")

def log_info(msg): log("INFO", msg)
def log_warn(msg): log("WARN", msg)
def log_error(msg): log("ERROR", msg)
def log_success(msg): log("SUCCESS", msg)

# ============== CHECKPOINT ==============
class Checkpoint:
    @staticmethod
    def load():
        if Path(CHECKPOINT_FILE).exists():
            with open(CHECKPOINT_FILE) as f:
                return json.load(f)
        return {"processed": [], "failed": [], "skipped": []}
    
    @staticmethod
    def save(checkpoint):
        with open(CHECKPOINT_FILE, "w") as f:
            json.dump(checkpoint, f, indent=2)
    
    @staticmethod
    def add_processed(file_id):
        cp = Checkpoint.load()
        cp["processed"].append(file_id)
        Checkpoint.save(cp)
    
    @staticmethod
    def add_failed(file_id, reason):
        cp = Checkpoint.load()
        cp["failed"].append({"id": file_id, "reason": reason, "time": datetime.now().isoformat()})
        Checkpoint.save(cp)

# ============== SETUP ==============
def setup_services():
    """Initialize Google Drive & Dify services"""
    dify_key = os.environ.get("DIFY_API_KEY")
    dify_url = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai")
    google_creds = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
    
    if not dify_key:
        log_error("DIFY_API_KEY tidak diset")
        sys.exit(1)
    
    if not Path(google_creds).exists():
        log_error(f"Credentials tidak ditemukan: {google_creds}")
        sys.exit(1)
    
    # Google Drive
    creds = service_account.Credentials.from_service_account_file(google_creds, scopes=SCOPES)
    drive = build("drive", "v3", credentials=creds)
    
    # Dify headers
    headers = {
        "Authorization": f"Bearer {dify_key}",
        "Content-Type": "application/json",
    }
    
    log_info(f"Setup: Dify={dify_url}, Google Drive=Ready")
    return drive, headers, dify_url

# ============== FILE OPERATIONS ==============
def download_file(drive, file_id, name, mime_type):
    """Download & convert file to text"""
    try:
        if mime_type.startswith("application/vnd.google-apps"):
            if "document" in mime_type:
                req = drive.files().export_media(fileId=file_id, mimeType="text/plain")
                return req.execute().decode("utf-8")
            elif "spreadsheet" in mime_type:
                req = drive.files().export_media(fileId=file_id, mimeType="text/csv")
                return req.execute().decode("utf-8")
            return ""
        else:
            req = drive.files().get_media(fileId=file_id)
            fh = io.BytesIO()
            downloader = MediaIoBaseDownload(fh, req)
            while True:
                status, done = downloader.next_chunk()
                if done:
                    break
            fh.seek(0)
            
            if mime_type == "application/pdf":
                reader = PdfReader(fh)
                return "\n".join(page.extract_text() or "" for page in reader.pages)
            elif "word" in mime_type or "document" in mime_type:
                doc = Document(fh)
                return "\n".join(p.text for p in doc.paragraphs)
            else:
                return fh.getvalue().decode("utf-8", errors="ignore")
    except Exception as e:
        raise Exception(f"Download failed: {e}")

def upload_to_dify(headers, dify_url, text, filename, max_retries=MAX_RETRIES):
    """Upload text to Dify with retry logic"""
    if not text or len(text.strip()) == 0:
        raise Exception("Empty text")
    
    payload = {
        "objects": [{
            "type": "text",
            "text": text[:1_000_000],  # Limit to 1MB
            "metadata": {"filename": filename}
        }]
    }
    
    for attempt in range(max_retries):
        try:
            resp = requests.post(
                f"{dify_url}/v1/knowledge/objects",
                headers=headers,
                json=payload,
                timeout=TIMEOUT
            )
            resp.raise_for_status()
            return resp.json()
        except Exception as e:
            if attempt == max_retries - 1:
                raise
            wait = RETRY_WAIT * (2 ** attempt)
            log_warn(f"Retry {filename} in {wait}s ({e})")
            time.sleep(wait)

# ============== MAIN PROCESSING ==============
def process_file(args, file_info):
    """Process single file (run in thread)"""
    drive, headers, dify_url = args
    file_id, name, mime_type = file_info["id"], file_info["name"], file_info["mimeType"]
    
    checkpoint = Checkpoint.load()
    if file_id in checkpoint["processed"]:
        return {"status": "skipped", "file": name}
    
    try:
        # Download
        text = download_file(drive, file_id, name, mime_type)
        if not text:
            Checkpoint.add_failed(file_id, "Empty text")
            return {"status": "failed", "file": name, "reason": "Empty"}
        
        # Upload
        upload_to_dify(headers, dify_url, text, name)
        Checkpoint.add_processed(file_id)
        
        return {
            "status": "success",
            "file": name,
            "size": len(text),
            "time": time.time()
        }
    except Exception as e:
        Checkpoint.add_failed(file_id, str(e))
        return {"status": "failed", "file": name, "reason": str(e)[:100]}

def process_folder_parallel(drive, headers, dify_url, folder_id, workers=MAX_WORKERS):
    """Process folder with parallel workers"""
    # List files
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive.files().list(q=query, fields="files(id,name,mimeType,size)").execute()
    files = results.get("files", [])
    
    log_info(f"Folder {folder_id}: Found {len(files)} files")
    
    # Process
    results_data = {"success": 0, "failed": 0, "skipped": 0}
    start_time = time.time()
    
    with ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(process_file, (drive, headers, dify_url), f): f["name"]
            for f in files
        }
        
        for i, future in enumerate(as_completed(futures), 1):
            try:
                result = future.result()
                results_data[result["status"]] += 1
                
                if i % 10 == 0 or i == len(files):
                    elapsed = time.time() - start_time
                    rate = i / elapsed
                    remaining = (len(files) - i) / rate if rate > 0 else 0
                    log_info(f"Progress: {i}/{len(files)} | "
                            f"Success: {results_data['success']}, Failed: {results_data['failed']} | "
                            f"ETA: {remaining/60:.1f}min")
            except Exception as e:
                log_error(f"Error processing {futures[future]}: {e}")
                results_data["failed"] += 1
    
    elapsed = time.time() - start_time
    log_success(f"Folder done in {elapsed/60:.1f}min: "
               f"Success={results_data['success']}, "
               f"Failed={results_data['failed']}, "
               f"Skipped={results_data['skipped']}")
    
    return results_data

# ============== MAIN ==============
def main():
    parser = argparse.ArgumentParser(description="Parallel document ingestion")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS, help="Parallel workers")
    parser.add_argument("--folder-id", type=str, help="Process specific folder")
    parser.add_argument("--resume", action="store_true", help="Resume from checkpoint")
    parser.add_argument("--list-checkpoints", action="store_true", help="Show checkpoint status")
    
    args = parser.parse_args()
    
    # Show checkpoint status
    if args.list_checkpoints:
        cp = Checkpoint.load()
        print(f"\nCheckpoint Status:")
        print(f"  Processed: {len(cp['processed'])}")
        print(f"  Failed: {len(cp['failed'])}")
        print(f"  Skipped: {len(cp['skipped'])}")
        return
    
    # Setup
    drive, headers, dify_url = setup_services()
    
    # Folder IDs
    FOLDER_IDS = [
        "12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z",
        "1Y2SLCbyHoB53BaQTTwRta2T6dv_drRll",
        "1CHz8UWZXfJtXlcjp9-FPAo-t_KkfTztW",
        "1_SsZ7SkaZxvXUZ6RUAA_o7WR_GAtgEwT",
    ]
    
    folders = [args.folder_id] if args.folder_id else FOLDER_IDS
    
    # Process
    log_info(f"Starting ingestion with {args.workers} workers...")
    total_results = {"success": 0, "failed": 0, "skipped": 0}
    
    for folder_id in folders:
        results = process_folder_parallel(drive, headers, dify_url, folder_id, args.workers)
        for k in total_results:
            total_results[k] += results[k]
    
    log_success(f"\n=== FINAL RESULTS ===")
    log_success(f"Success: {total_results['success']}")
    log_success(f"Failed: {total_results['failed']}")
    log_success(f"Skipped: {total_results['skipped']}")
    log_success(f"Total: {sum(total_results.values())}")

if __name__ == "__main__":
    main()
