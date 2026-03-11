# Dify Chatbot with Google Drive Integration

This example shows how to build a chatbot using the [Dify](https://github.com/langgenius/dify) platform that is aware of files stored in Google Drive.

## Overview

1. **Run Dify** – self‑hosted or cloud service.
2. **Obtain Google Drive credentials** – OAuth2 or service account with access to your folders.
3. **Download and preprocess files** from each Drive folder.
4. **Ingest content** into Dify's knowledge base via its API (vector store).
5. **Create a chat app** that queries Dify.

## Requirements

- Python 3.8+
- `google-api-python-client`, `google-auth-httplib2`, `google-auth-oauthlib`
- `requests`, `python-docx`, `PyPDF2` or similar converters

Install requirements:

```bash
cd dify-chatbot
python -m venv venv
source venv/bin/activate  # Linux/macOS
pip install -r requirements.txt
```

## Configuration

Set environment variables:

```bash
export GOOGLE_APPLICATION_CREDENTIALS="/path/to/your-service-account.json"
export DIFY_API_KEY="your-dify-api-key"
export DIFY_BASE_URL="https://your-dify-instance.com"   # or http://localhost:3000
```

## Usage

1. Run the ingestion script to pull documents from Google Drive and push them to Dify:

   ```bash
   python google_drive_ingest.py
   ```

2. Use the Dify admin UI to create a chatbot model, selecting the knowledge base created by the ingestion script.

3. Interact with the chatbot via Dify's built-in Web UI or via the REST API:

   ```bash
   curl -X POST "$DIFY_BASE_URL/api/v1/chat/completions" \
     -H "Authorization: Bearer $DIFY_API_KEY" \
     -H "Content-Type: application/json" \
     -d '{"model":"gpt-4","messages":[{"role":"user","content":"..."}],"knowledge_ids":["<your-knowledge-id>"]}'
   ```

---

The following script demonstrates how to list files in a folder and upload their text to Dify.