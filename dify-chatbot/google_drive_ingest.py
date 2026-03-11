import os
import io
import sys
import json
import mimetypes
import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload
from PyPDF2 import PdfReader
from docx import Document

# Colors for terminal output
class Colors:
    OK = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'

def log_info(msg):
    print(f"{Colors.OK}[INFO]{Colors.ENDC} {msg}")

def log_warn(msg):
    print(f"{Colors.WARNING}[WARN]{Colors.ENDC} {msg}")

def log_error(msg):
    print(f"{Colors.FAIL}[ERROR]{Colors.ENDC} {msg}")

# IDs of folders to ingest (replace with your own)
FOLDER_IDS = [
    "12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z",  # folder 1
    "1Y2SLCbyHoB53BaQTTwRta2T6dv_drRll",  # folder 2
    "1CHz8UWZXfJtXlcjp9-FPAo-t_KkfTztW",  # folder 3
    "1_SsZ7SkaZxvXUZ6RUAA_o7WR_GAtgEwT",  # folder 4
]

# Dify configuration
DIFY_API_KEY = os.environ.get("DIFY_API_KEY")
DIFY_BASE_URL = os.environ.get("DIFY_BASE_URL", "https://api.dify.ai")
GOOGLE_CREDS = os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")

if not DIFY_API_KEY:
    log_error("DIFY_API_KEY tidak diset. Set dulu:")
    print('  export DIFY_API_KEY="your-api-key"')
    sys.exit(1)

if not os.path.exists(GOOGLE_CREDS):
    log_error(f"File kredensial tidak ditemukan: {GOOGLE_CREDS}")
    sys.exit(1)

log_info(f"Menggunakan Dify: {DIFY_BASE_URL}")
log_info(f"Menggunakan credentials: {GOOGLE_CREDS}")

headers = {
    "Authorization": f"Bearer {DIFY_API_KEY}",
    "Content-Type": "application/json",
}

# set up Google Drive client using service account credentials
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
try:
    credentials = service_account.Credentials.from_service_account_file(
        GOOGLE_CREDS, scopes=SCOPES
    )
    drive_service = build("drive", "v3", credentials=credentials)
    log_info("Google Drive client siap")
except Exception as e:
    log_error(f"Gagal setup Google Drive client: {e}")
    sys.exit(1)


def list_files_in_folder(folder_id):
    query = f"'{folder_id}' in parents and trashed=false"
    results = drive_service.files().list(q=query, fields="files(id,name,mimeType)").execute()
    return results.get("files", [])


def download_file(file_id, name, mime_type):
    # determine export format if Google Docs
    if mime_type.startswith("application/vnd.google-apps"):
        # convert to plain text or PDF
        if "document" in mime_type:
            request = drive_service.files().export_media(fileId=file_id, mimeType="text/plain")
            data = request.execute()
            return data.decode("utf-8")
        elif "spreadsheet" in mime_type:
            request = drive_service.files().export_media(fileId=file_id, mimeType="text/csv")
            return request.execute().decode("utf-8")
        else:
            # add additional conversions as needed
            return ""
    else:
        request = drive_service.files().get_media(fileId=file_id)
        fh = io.BytesIO()
        downloader = MediaIoBaseDownload(fh, request)
        done = False
        while not done:
            status, done = downloader.next_chunk()
        fh.seek(0)

        # attempt to decode by type
        if mime_type == "application/pdf":
            reader = PdfReader(fh)
            text = "\n".join(page.extract_text() or "" for page in reader.pages)
            return text
        elif mime_type in [
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            "application/msword",
        ]:
            doc = Document(fh)
            return "\n".join(p.text for p in doc.paragraphs)
        else:
            try:
                return fh.getvalue().decode("utf-8")
            except Exception:
                return ""  # binary or unsupported


def ingest_text_to_dify(text, filename="unnamed"):
    """Upload text ke Dify knowledge base"""
    if not text or len(text.strip()) == 0:
        log_warn(f"  {filename}: Isi kosong, skip")
        return None
    
    payload = {
        "objects": [
            {"type": "text", "text": text, "metadata": {"filename": filename}}
        ]
    }
    url = f"{DIFY_BASE_URL}/v1/knowledge/objects"
    try:
        r = requests.post(url, headers=headers, json=payload, timeout=30)
        r.raise_for_status()
        log_info(f"  ✓ {filename} ({len(text)} chars)")
        return r.json()
    except requests.exceptions.ConnectionError:
        log_error(f"  ✗ {filename}: Tidak bisa connect ke Dify di {DIFY_BASE_URL}")
        log_error("  Pastikan Dify server berjalan dan DIFY_BASE_URL benar")
        raise
    except Exception as e:
        log_error(f"  ✗ {filename}: {e}")
        raise


def process_folder(folder_id):
    try:
        files = list_files_in_folder(folder_id)
        log_info(f"Folder {folder_id}: ditemukan {len(files)} file")
        
        success = 0
        for f in files:
            try:
                content = download_file(f["id"], f["name"], f["mimeType"])
                if content:
                    ingest_text_to_dify(content, filename=f["name"])
                    success += 1
            except Exception as e:
                log_warn(f"  Skip {f['name']}: {str(e)[:100]}")
        
        log_info(f"Folder {folder_id}: berhasil {success}/{len(files)} file\n")
    except Exception as e:
        log_error(f"Gagal process folder {folder_id}: {e}")


if __name__ == "__main__":
    log_info(f"Mulai ingestion dari {len(FOLDER_IDS)} folder...")
    print()
    
    for fid in FOLDER_IDS:
        process_folder(fid)
    
    print()
    log_info("Ingestion selesai!")
    log_info("Buka dashboard Dify dan periksa Knowledge base")
