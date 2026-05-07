#!/bin/bash
# ================================================================
# The Market Lion — الخطوة 1: رفع الكود على GitHub
# شغّلي في Terminal:
#
#   cd ~/Documents/Claude/Projects
#   cd "The Market Lion (Razan AI Trading Platform \"Bot & Indicator\")"
#   bash PUSH_AND_DEPLOY.sh
#
# ================================================================

set -e
PROJ_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
REMOTE="https://github.com/RazanLeo/The-Market-Lion.git"

echo ""
echo "🦁 The Market Lion — GitHub Push"
echo "=================================="
echo ""

cd "$PROJ_DIR"

# ─── حذف index.lock إن وُجد ───────────────────────────────────
if [ -f ".git/index.lock" ]; then
  echo "🔓 حذف index.lock..."
  rm -f ".git/index.lock"
fi

# ─── إضافة كل الملفات ─────────────────────────────────────────
echo "📦 إضافة الملفات..."
git add .

COUNT=$(git status --short | wc -l | xargs)
echo "   ✅ $COUNT ملف جاهز"

# ─── Commit ───────────────────────────────────────────────────
echo ""
echo "💾 Commit..."
git commit -m "🚀 Initial commit — The Market Lion v1.0

Backend: FastAPI + 295 analyzer (140 schools + 135 indicators + 20 tools)
Frontend: Next.js 14 + 8 interactive tables + WebSocket live data
Data sources: Yahoo Finance + Stooq (free, no API keys needed)
Docker: Full production stack with Caddy reverse proxy
Auth: JWT + 2FA + Admin panel
i18n: Arabic + English" 2>/dev/null || echo "ℹ️  لا توجد تغييرات جديدة للـ commit"

# ─── ضبط الـ Remote ───────────────────────────────────────────
echo ""
echo "🔗 ضبط remote..."
git remote remove origin 2>/dev/null || true
git remote add origin "$REMOTE"

# ─── Rename branch to main ────────────────────────────────────
CURRENT_BRANCH=$(git branch --show-current 2>/dev/null || git rev-parse --abbrev-ref HEAD)
if [ "$CURRENT_BRANCH" != "main" ]; then
  echo "🔀 تحويل الـ branch إلى main..."
  git branch -M main
fi

# ─── Push ─────────────────────────────────────────────────────
echo ""
echo "⬆️  رفع الكود..."
echo "   Username: RazanLeo"
echo "   Password: Personal Access Token من GitHub"
echo ""
git push -u origin main

echo ""
echo "✅ تم رفع الكود!"
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "الخطوة 2: تشغيل المنصة على السيرفر"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""
echo "اتصلي بالسيرفر:"
echo "  ssh root@161.35.192.36"
echo ""
echo "ثم الصقي هذه الأوامر دفعة واحدة:"
echo ""
echo '  cd /opt && git clone https://github.com/RazanLeo/The-Market-Lion.git the-market-lion'
echo '  cd the-market-lion/app'
echo '  cp .env.example .env'
echo '  JWT=$(openssl rand -hex 64)'
echo '  DB=$(openssl rand -hex 16)'
echo '  sed -i "s|replace-with-long-random-string-min-64-chars|$JWT|g" .env'
echo '  sed -i "s|change_me_strong_password|$DB|g" .env'
echo '  sed -i "s|APP_ENV=development|APP_ENV=production|g" .env'
echo '  docker compose -f docker-compose.server.yml build --parallel'
echo '  docker compose -f docker-compose.server.yml up -d'
echo '  sleep 15 && docker compose -f docker-compose.server.yml exec -T backend alembic upgrade head'
echo '  curl http://localhost:8000/api/v1/health'
echo ""
echo "🎉 المنصة ستكون على: http://161.35.192.36/dashboard"
