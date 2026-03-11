#!/bin/bash
set -e

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m'

cd "$(dirname "$0")"

echo -e "${YELLOW}Mengaktifkan Python environment...${NC}"
source venv/bin/activate

echo -e "${YELLOW}Setup environment variables...${NC}"
export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"

# Check if Dify variables are set
if [ -z "$DIFY_API_KEY" ] || [ -z "$DIFY_BASE_URL" ]; then
    echo -e "${RED}ERROR: Variabel Dify belum diset!${NC}"
    echo ""
    echo "Silakan jalankan setup terlebih dahulu:"
    echo ""
    echo -e "${YELLOW}# Setup untuk Dify lokal (Docker - DIREKOMENDASIKAN)${NC}"
    echo "export DIFY_BASE_URL='http://localhost'"
    echo "export DIFY_API_KEY='<API_KEY_dari_dashboard>'"
    echo "bash run.sh"
    echo ""
    echo -e "${YELLOW}# Atau setup untuk Dify Cloud${NC}"
    echo "export DIFY_BASE_URL='https://api.dify.ai'"
    echo "export DIFY_API_KEY='<API_KEY_dari_app.dify.ai>'"
    echo "bash run.sh"
    echo ""
    exit 1
fi

echo -e "${GREEN}✓ DIFY_BASE_URL: $DIFY_BASE_URL${NC}"
echo -e "${GREEN}✓ DIFY_API_KEY: ${DIFY_API_KEY:0:10}...${NC}"
echo -e "${GREEN}✓ GOOGLE_APPLICATION_CREDENTIALS: $GOOGLE_APPLICATION_CREDENTIALS${NC}"
echo ""

echo -e "${YELLOW}Menjalankan ingestion script...${NC}"
echo ""
python google_drive_ingest.py

echo ""
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo -e "${GREEN}Selesai!${NC}"
echo -e "${GREEN}════════════════════════════════════════${NC}"
echo ""
echo "Langkah selanjutnya:"
echo "1. Buka Dify dashboard: $DIFY_BASE_URL"
echo "2. Periksa Knowledge base yang baru dibuat"
echo "3. Buat Chat app dan pilih knowledge tersebut"
echo ""
