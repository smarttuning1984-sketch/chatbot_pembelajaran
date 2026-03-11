#!/usr/bin/env python3
"""
Auto-Sync Google Drive to Dify Knowledge Base
Features:
- Continuous monitoring & syncing
- Auto-reconnect on server failure
- Resilient to network interruptions
- State management & checkpoint resume
- Health checks & graceful shutdown

Usage: python auto_sync.py [--interval 300] [--watch-folder FOLDER_ID]
"""

import os
import sys
import time
import json
import signal
import logging
from pathlib import Path
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict
import hashlib

import requests
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

# ============== CONFIG ==============
SCOPES = ["https://www.googleapis.com/auth/drive.readonly"]
STATE_FILE = "sync_state.json"
LOG_FILE = "auto_sync.log"
HEALTH_CHECK_INTERVAL = 30  # seconds
SYNC_INTERVAL = 300  # seconds (5 minutes)
MAX_RETRIES = 5
INITIAL_BACKOFF = 2  # seconds
MAX_BACKOFF = 300  # 5 minutes

# ============== LOGGING SETUP ==============
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler(LOG_FILE),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# ============== DATACLASSES ==============
@dataclass
class SyncState:
    """Track sync state for resumption"""
    last_sync_time: str
    synced_files: Dict[str, str]  # file_id -> hash
    failed_files: Dict[str, str]  # file_id -> reason
    failed_count: int = 0
    success_count: int = 0
    
    def to_dict(self):
        return asdict(self)
    
    @staticmethod
    def from_dict(data):
        return SyncState(**data)

@dataclass
class FileInfo:
    """File metadata"""
    id: str
    name: str
    mime_type: str
    modified_time: str
    size: int

# ============== STATE MANAGEMENT ==============
class StateManager:
    """Persistent state for resumption"""
    
    @staticmethod
    def load() -> SyncState:
        """Load sync state from file"""
        if Path(STATE_FILE).exists():
            try:
                with open(STATE_FILE) as f:
                    data = json.load(f)
                return SyncState.from_dict(data)
            except Exception as e:
                logger.warning(f"Failed to load state: {e}, starting fresh")
                return StateManager.create_fresh()
        return StateManager.create_fresh()
    
    @staticmethod
    def create_fresh() -> SyncState:
        """Create fresh state"""
        return SyncState(
            last_sync_time=datetime.now().isoformat(),
            synced_files={},
            failed_files={},
            failed_count=0,
            success_count=0
        )
    
    @staticmethod
    def save(state: SyncState):
        """Save state to file"""
        with open(STATE_FILE, "w") as f:
            json.dump(state.to_dict(), f, indent=2)
    
    @staticmethod
    def update_synced(state: SyncState, file_id: str, content_hash: str):
        """Mark file as synced"""
        state.synced_files[file_id] = content_hash
        state.success_count += 1
        StateManager.save(state)
    
    @staticmethod
    def update_failed(state: SyncState, file_id: str, reason: str):
        """Mark file as failed"""
        state.failed_files[file_id] = reason
        state.failed_count += 1
        StateManager.save(state)

# ============== RETRY LOGIC ==============
class RetryManager:
    """Handle reconnection with exponential backoff"""
    
    def __init__(self, max_retries=MAX_RETRIES, initial_backoff=INITIAL_BACKOFF, max_backoff=MAX_BACKOFF):
        self.max_retries = max_retries
        self.initial_backoff = initial_backoff
        self.max_backoff = max_backoff
    
    def execute_with_retry(self, func, *args, **kwargs):
        """Execute function with exponential backoff retry"""
        backoff = self.initial_backoff
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return func(*args, **kwargs)
            except (requests.ConnectionError, requests.Timeout, HttpError) as e:
                last_exception = e
                if attempt < self.max_retries - 1:
                    logger.warning(
                        f"Attempt {attempt + 1}/{self.max_retries} failed. "
                        f"Retrying in {backoff}s... Error: {str(e)[:100]}"
                    )
                    time.sleep(backoff)
                    backoff = min(backoff * 2, self.max_backoff)
                else:
                    logger.error(f"All {self.max_retries} attempts failed for {func.__name__}")
        
        raise last_exception

# ============== HEALTH CHECK ==============
class HealthChecker:
    """Monitor Dify server health"""
    
    def __init__(self, dify_url: str, api_key: str):
        self.dify_url = dify_url
        self.api_key = api_key
        self.is_healthy = True
        self.last_check = None
    
    def check(self) -> bool:
        """Check if Dify server is healthy"""
        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            # Try a simple API call
            resp = requests.get(
                f"{self.dify_url}/api/version",
                headers=headers,
                timeout=5
            )
            
            self.is_healthy = resp.status_code < 500
            self.last_check = datetime.now()
            
            if not self.is_healthy:
                logger.warning(f"Dify health check failed: {resp.status_code}")
            else:
                logger.debug("Dify server is healthy")
            
            return self.is_healthy
        except Exception as e:
            self.is_healthy = False
            self.last_check = datetime.now()
            logger.error(f"Health check error: {e}")
            return False
    
    def wait_until_healthy(self, timeout=600):
        """Wait for server to become healthy"""
        start_time = time.time()
        wait_time = 2
        
        while time.time() - start_time < timeout:
            if self.check():
                logger.info("Server is back online!")
                return True
            
            logger.info(f"Waiting for server recovery... ({wait_time}s)")
            time.sleep(wait_time)
            wait_time = min(wait_time * 2, 30)
        
        logger.error(f"Server did not recover within {timeout}s")
        return False

# ============== GOOGLE DRIVE OPERATIONS ==============
class DriveClient:
    """Google Drive API client with retry logic"""
    
    def __init__(self, credentials_path: str):
        self.retry_manager = RetryManager()
        
        try:
            creds = service_account.Credentials.from_service_account_file(
                credentials_path, scopes=SCOPES
            )
            self.service = build("drive", "v3", credentials=creds)
            logger.info("Google Drive client initialized")
        except Exception as e:
            logger.error(f"Failed to initialize Drive client: {e}")
            raise
    
    def list_files(self, folder_id: str, modified_after=None) -> List[FileInfo]:
        """List files in folder with retry"""
        def _list():
            query = f"'{folder_id}' in parents and trashed=false"
            
            if modified_after:
                # Format: RFC 3339 timestamp
                query += f" and modifiedTime > '{modified_after}'"
            
            results = self.service.files().list(
                q=query,
                fields="files(id,name,mimeType,modifiedTime,size)",
                pageSize=1000
            ).execute()
            
            files = results.get("files", [])
            return [
                FileInfo(
                    id=f["id"],
                    name=f["name"],
                    mime_type=f.get("mimeType", ""),
                    modified_time=f.get("modifiedTime", ""),
                    size=f.get("size", 0)
                )
                for f in files
            ]
        
        return self.retry_manager.execute_with_retry(_list)
    
    def download_file(self, file_id: str, name: str, mime_type: str) -> Optional[str]:
        """Download & convert file to text with retry"""
        def _download():
            import io
            from PyPDF2 import PdfReader
            from docx import Document
            
            if mime_type.startswith("application/vnd.google-apps"):
                if "document" in mime_type:
                    req = self.service.files().export_media(
                        fileId=file_id, mimeType="text/plain"
                    )
                    return req.execute().decode("utf-8")
                elif "spreadsheet" in mime_type:
                    req = self.service.files().export_media(
                        fileId=file_id, mimeType="text/csv"
                    )
                    return req.execute().decode("utf-8")
                return ""
            else:
                req = self.service.files().get_media(fileId=file_id)
                fh = io.BytesIO()
                from googleapiclient.http import MediaIoBaseDownload
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
        
        return self.retry_manager.execute_with_retry(_download)

# ============== DIFY OPERATIONS ==============
class DifyClient:
    """Dify API client with retry logic"""
    
    def __init__(self, base_url: str, api_key: str):
        self.base_url = base_url
        self.api_key = api_key
        self.retry_manager = RetryManager()
        self.health_checker = HealthChecker(base_url, api_key)
    
    def upload(self, text: str, filename: str) -> Optional[Dict]:
        """Upload text to Dify with retry"""
        if not text or len(text.strip()) == 0:
            logger.warning(f"Skipping {filename}: empty content")
            return None
        
        def _upload():
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            }
            
            payload = {
                "objects": [{
                    "type": "text",
                    "text": text[:1_000_000],
                    "metadata": {"filename": filename}
                }]
            }
            
            resp = requests.post(
                f"{self.base_url}/v1/knowledge/objects",
                headers=headers,
                json=payload,
                timeout=60
            )
            resp.raise_for_status()
            return resp.json()
        
        try:
            return self.retry_manager.execute_with_retry(_upload)
        except Exception as e:
            logger.error(f"Failed to upload {filename}: {e}")
            return None

# ============== AUTO SYNC MANAGER ==============
class AutoSyncManager:
    """Main auto-sync orchestrator"""
    
    def __init__(self, folder_ids: List[str], sync_interval=SYNC_INTERVAL):
        self.folder_ids = folder_ids
        self.sync_interval = sync_interval
        self.should_stop = False
        
        # Initialize clients
        self.drive_client = DriveClient(
            os.environ.get("GOOGLE_APPLICATION_CREDENTIALS", "credentials.json")
        )
        self.dify_client = DifyClient(
            os.environ.get("DIFY_BASE_URL", "http://localhost"),
            os.environ.get("DIFY_API_KEY")
        )
        
        # Load state
        self.state = StateManager.load()
        
        # Signal handlers
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)
        
        logger.info("AutoSyncManager initialized")
    
    def _signal_handler(self, signum, frame):
        """Handle shutdown signals gracefully"""
        logger.info(f"Received signal {signum}, shutting down gracefully...")
        self.should_stop = True
    
    def sync_folder(self, folder_id: str) -> Tuple[int, int]:
        """Sync single folder"""
        try:
            logger.info(f"Syncing folder {folder_id}...")
            
            # Get last sync time
            last_sync = datetime.fromisoformat(self.state.last_sync_time)
            modified_after = last_sync.isoformat() + "Z"
            
            # List files
            files = self.drive_client.list_files(folder_id, modified_after)
            logger.info(f"Found {len(files)} files to process")
            
            success = 0
            failed = 0
            
            for file_info in files:
                if self.should_stop:
                    break
                
                try:
                    # Check if already synced
                    file_hash = hashlib.md5(
                        (file_info.id + file_info.modified_time).encode()
                    ).hexdigest()
                    
                    if file_info.id in self.state.synced_files:
                        if self.state.synced_files[file_info.id] == file_hash:
                            logger.debug(f"Skipping {file_info.name} (already synced)")
                            continue
                    
                    # Download & upload
                    logger.info(f"Processing {file_info.name}...")
                    content = self.drive_client.download_file(
                        file_info.id, file_info.name, file_info.mime_type
                    )
                    
                    if content:
                        result = self.dify_client.upload(content, file_info.name)
                        if result:
                            StateManager.update_synced(self.state, file_info.id, file_hash)
                            success += 1
                        else:
                            StateManager.update_failed(self.state, file_info.id, "Upload failed")
                            failed += 1
                    else:
                        StateManager.update_failed(self.state, file_info.id, "Empty content")
                        failed += 1
                
                except Exception as e:
                    logger.error(f"Error processing {file_info.name}: {e}")
                    StateManager.update_failed(self.state, file_info.id, str(e)[:100])
                    failed += 1
                    time.sleep(1)  # Brief pause before next file
            
            # Update last sync time
            self.state.last_sync_time = datetime.now().isoformat()
            StateManager.save(self.state)
            
            logger.info(f"Folder sync complete: {success} success, {failed} failed")
            return success, failed
        
        except Exception as e:
            logger.error(f"Error syncing folder {folder_id}: {e}")
            return 0, len(self.folder_ids)
    
    def run(self):
        """Main sync loop"""
        logger.info("Starting auto-sync loop...")
        
        while not self.should_stop:
            try:
                # Health check
                if not self.dify_client.health_checker.check():
                    logger.warning("Dify server is down, waiting for recovery...")
                    if not self.dify_client.health_checker.wait_until_healthy():
                        logger.error("Server recovery timeout, retrying later...")
                        time.sleep(self.sync_interval)
                        continue
                
                # Sync all folders
                total_success = 0
                total_failed = 0
                
                for folder_id in self.folder_ids:
                    if self.should_stop:
                        break
                    
                    success, failed = self.sync_folder(folder_id)
                    total_success += success
                    total_failed += failed
                    time.sleep(2)  # Brief pause between folders
                
                logger.info(
                    f"Sync cycle complete: "
                    f"{total_success} success, {total_failed} failed. "
                    f"Next sync in {self.sync_interval}s"
                )
                
                # Wait for next sync
                time.sleep(self.sync_interval)
            
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Unexpected error in sync loop: {e}", exc_info=True)
                time.sleep(self.sync_interval)
        
        logger.info("Auto-sync loop stopped")
        self._print_summary()
    
    def _print_summary(self):
        """Print final summary"""
        logger.info("=== SYNC SUMMARY ===")
        logger.info(f"Total synced: {self.state.success_count}")
        logger.info(f"Total failed: {self.state.failed_count}")
        logger.info(f"Last sync: {self.state.last_sync_time}")
        if self.state.failed_files:
            logger.info(f"Failed files: {len(self.state.failed_files)}")

# ============== MAIN ==============
def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="Auto-sync Google Drive to Dify")
    parser.add_argument("--interval", type=int, default=SYNC_INTERVAL, 
                       help="Sync interval in seconds")
    parser.add_argument("--watch-folder", type=str, 
                       help="Watch specific folder instead of all")
    parser.add_argument("--health-check-interval", type=int, 
                       default=HEALTH_CHECK_INTERVAL, 
                       help="Health check interval in seconds")
    
    args = parser.parse_args()
    
    # Folder IDs
    DEFAULT_FOLDERS = [
        "12ffd7GqHAiy3J62Vu65LbVt6-ultog5Z",
        "1Y2SLCbyHoB53BaQTTwRta2T6dv_drRll",
        "1CHz8UWZXfJtXlcjp9-FPAo-t_KkfTztW",
        "1_SsZ7SkaZxvXUZ6RUAA_o7WR_GAtgEwT",
    ]
    
    folder_ids = [args.watch_folder] if args.watch_folder else DEFAULT_FOLDERS
    
    # Initialize & run
    manager = AutoSyncManager(folder_ids, args.interval)
    manager.run()

if __name__ == "__main__":
    main()
