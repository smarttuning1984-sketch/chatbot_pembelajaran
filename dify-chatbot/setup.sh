#!/bin/bash
set -e

# Colors
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}"
cat << "EOF"
╔════════════════════════════════════════════════════════════╗
║  Chatbot Pembelajaran Mekanik Mobil Indonesia - Setup      ║
║  Platform: Dify + Google Drive                             ║
╚════════════════════════════════════════════════════════════╝
EOF
echo -e "${NC}"

# Check prerequisites
echo -e "${YELLOW}[1/4] Checking prerequisites...${NC}"

if ! command -v python3 &> /dev/null; then
    echo -e "${RED}✗ Python3 tidak terinstall${NC}"
    exit 1
fi
echo -e "${GREEN}✓ Python3 ditemukan$(python3 --version)${NC}"

if ! command -v docker &> /dev/null; then
    echo -e "${YELLOW}⚠ Docker tidak terinstall (opsional jika Anda pakai Dify cloud)${NC}"
else
    echo -e "${GREEN}✓ Docker terinstall${NC}"
fi

# Check credentials file
echo -e "${YELLOW}[2/4] Checking credentials...${NC}"
if [ ! -f "credentials.json" ]; then
    echo -e "${RED}✗ credentials.json tidak ditemukan${NC}"
    exit 1
fi
echo -e "${GREEN}✓ credentials.json ada${NC}"

# Setup Python venv
echo -e "${YELLOW}[3/4] Setup Python environment...${NC}"
if [ ! -d "venv" ]; then
    python3 -m venv venv
    echo -e "${GREEN}✓ Virtual environment dibuat${NC}"
else
    echo -e "${GREEN}✓ Virtual environment sudah ada${NC}"
fi

source venv/bin/activate
pip install -q -r requirements.txt
echo -e "${GREEN}✓ Dependencies terinstall${NC}"

# Configuration check
echo -e "${YELLOW}[4/4] Configuration setup...${NC}"

if [ -z "$DIFY_API_KEY" ]; then
    echo -e "${RED}✗ DIFY_API_KEY belum diset${NC}"
    echo ""
    echo -e "${YELLOW}Silakan set environment variables:${NC}"
    echo "  export DIFY_API_KEY=\"your-api-key\""
    echo "  export DIFY_BASE_URL=\"http://localhost:3000\"  # atau https://api.dify.ai"
    echo ""
    echo -e "${YELLOW}Untuk mendapatkan DIFY_API_KEY:${NC}"
    echo "  1. Jalankan: docker compose up -d  (dari folder dify yang sudah di-clone)"
    echo "  2. Buka: http://localhost:3000"
    echo "  3. Settings → API Keys → Create new"
    echo ""
    exit 1
fi
echo -e "${GREEN}✓ DIFY_API_KEY diset${NC}"
echo -e "${GREEN}✓ DIFY_BASE_URL: $DIFY_BASE_URL${NC}"

# Summary
echo ""
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo -e "${GREEN}Setup selesai! Siap untuk menjalankan ingestion.${NC}"
echo -e "${GREEN}════════════════════════════════════════════════════════════${NC}"
echo ""
echo "Langkah selanjutnya:"
echo "  1. Pastikan Dify server sudah running (cek: http://localhost:3000)"
echo "  2. Jalankan: python google_drive_ingest.py"
echo "  3. Buka Dify dashboard untuk cek knowledge base"
echo ""
