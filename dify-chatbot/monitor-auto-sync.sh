#!/bin/bash
# Monitor auto-sync progress and state

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║              Auto-Sync Monitor Dashboard                   ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

# Check if auto-sync is running
if pgrep -f "python.*auto_sync.py" > /dev/null; then
    echo "✅ auto_sync.py is RUNNING"
    pgrep -f "python.*auto_sync.py" | xargs ps -o pid,cmd,etime | tail -1
else
    echo "❌ auto_sync.py is NOT running"
fi

echo ""
echo "📊 Sync State:"
if [ -f "sync_state.json" ]; then
    python3 -c "
import json
with open('sync_state.json') as f:
    state = json.load(f)
print(f\"   Success Count: {state['success_count']}\")
print(f\"   Failed Count: {state['failed_count']}\")
print(f\"   Synced Files: {len(state['synced_files'])}\")
print(f\"   Failed Files: {len(state['failed_files'])}\")
print(f\"   Last Sync: {state['last_sync_time']}\")
"
else
    echo "   No sync state found (first run)"
fi

echo ""
echo "📝 Recent Logs:"
if [ -f "auto_sync.log" ]; then
    tail -10 auto_sync.log
else
    echo "   No logs yet"
fi

echo ""
echo "🔧 Available Commands:"
echo "   bash start-auto-sync.sh              # Start auto-sync"
echo "   tail -f auto_sync.log                # Live logs"
echo "   pkill -f auto_sync.py                # Stop auto-sync"
echo "   rm sync_state.json                   # Reset state"
echo ""
