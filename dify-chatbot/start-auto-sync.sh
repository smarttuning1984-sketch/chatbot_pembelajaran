#!/bin/bash
set -e

# Start Auto-Sync with proper environment setup

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║         Starting Dify Auto-Sync (Continuous Mode)          ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check environment
if [ -z "$DIFY_API_KEY" ]; then
    echo "❌ ERROR: DIFY_API_KEY not set"
    echo ""
    echo "Setup:"
    echo "  export DIFY_API_KEY=\"sk-...\""
    echo "  export DIFY_BASE_URL=\"http://localhost\""
    echo "  export GOOGLE_APPLICATION_CREDENTIALS=\"\$(pwd)/credentials.json\""
    exit 1
fi

if [ -z "$DIFY_BASE_URL" ]; then
    echo "⚠️  DIFY_BASE_URL not set, using default: http://localhost"
    export DIFY_BASE_URL="http://localhost"
fi

if [ ! -f "credentials.json" ]; then
    export GOOGLE_APPLICATION_CREDENTIALS="${GOOGLE_APPLICATION_CREDENTIALS:-credentials.json}"
    if [ ! -f "$GOOGLE_APPLICATION_CREDENTIALS" ]; then
        echo "❌ ERROR: Credentials file not found: $GOOGLE_APPLICATION_CREDENTIALS"
        exit 1
    fi
else
    export GOOGLE_APPLICATION_CREDENTIALS="$(pwd)/credentials.json"
fi

# Activate venv if exists
if [ -d "venv" ]; then
    source venv/bin/activate
fi

# Parse arguments
INTERVAL=300
WATCH_FOLDER=""

while [[ $# -gt 0 ]]; do
    case $1 in
        --interval) INTERVAL="$2"; shift 2 ;;
        --watch-folder) WATCH_FOLDER="$2"; shift 2 ;;
        *) echo "Unknown option: $1"; exit 1 ;;
    esac
done

# Print configuration
echo "🔧 Configuration:"
echo "   Dify URL: $DIFY_BASE_URL"
echo "   API Key: ${DIFY_API_KEY:0:10}...${DIFY_API_KEY: -5}"
echo "   Sync Interval: ${INTERVAL}s"
if [ -n "$WATCH_FOLDER" ]; then
    echo "   Watch Folder: $WATCH_FOLDER"
else
    echo "   Watch Folders: All (4 folders)"
fi
echo ""
echo "📊 Output:"
echo "   Logs: auto_sync.log (tail -f)"
echo "   State: sync_state.json"
echo ""
echo "💡 Tips:"
echo "   - Stop with Ctrl+C (graceful shutdown)"
echo "   - Monitor progress: tail -f auto_sync.log"
echo "   - Check state: cat sync_state.json"
echo ""
echo "Starting auto-sync..."
echo "════════════════════════════════════════════════════════════"
echo ""

# Run auto-sync
if [ -n "$WATCH_FOLDER" ]; then
    python auto_sync.py --interval $INTERVAL --watch-folder $WATCH_FOLDER
else
    python auto_sync.py --interval $INTERVAL
fi
