#!/bin/bash
set -e

echo ""
echo "╔════════════════════════════════════════════════════════════╗"
echo "║           ✅ Dify Server is RUNNING & READY!               ║"
echo "╚════════════════════════════════════════════════════════════╝"
echo ""

echo "📍 Akses Dify Dashboard:"
echo "   http://localhost"
echo ""

echo "⚠️  PENTING: Setup Admin Account"
echo "   Pertama kali akses, Anda akan diminta membuat admin account"
echo "   - Email: gunakan email apapun (cth: admin@localhost)"
echo "   - Password: buat password yang kuat"
echo "   - Setelah selesai, login dengan credentials tersebut"
echo ""

echo "🔑 Dapatkan API Key:"
echo "   1. Login ke dashboard"
echo "   2. Pergi ke: Account (pojok kanan atas) → Settings"
echo "   3. Pilih: API Keys (di sidebar kiri)"
echo "   4. Klik: + Create API Key"
echo "   5. Copy key yang tampil (format: sk-...)"
echo ""

echo "💾 Simpan API Key ke environment:"
echo "   export DIFY_API_KEY=\"sk-...\""
echo "   export DIFY_BASE_URL=\"http://localhost\""
echo ""

echo "▶️  Jalankan Ingestion Script:"
echo "   cd /workspaces/Materi_pembelajaran/dify-chatbot"
echo "   bash run.sh"
echo ""

echo "📊 Status Services:"
cd /tmp/dify/docker
docker compose -f docker-compose.yaml ps | awk 'NR==1 {print; next} {printf "   %-30s %s\n", $1, $5}'

echo ""
echo "💡 Tips:"
echo "   - Jika lupa API key, buat baru yang lain"
echo "   - Untuk stop Dify: cd /tmp/dify/docker && docker compose down"
echo "   - Untuk lihat logs: docker compose logs -f api"
echo ""
