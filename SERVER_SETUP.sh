#!/bin/bash
# ================================================================
# The Market Lion — إعداد السيرفر ونشر المنصة
# شغّلي هذا على السيرفر بعد الـ SSH:
#   bash SERVER_SETUP.sh
# ================================================================

set -euo pipefail
echo ""
echo "🦁 The Market Lion — Server Setup"
echo "=================================="

# ── 1. تثبيت Docker إذا لم يكن موجوداً ──────────────────────
if ! command -v docker &>/dev/null; then
  echo "📦 تثبيت Docker..."
  curl -fsSL https://get.docker.com | sh
  systemctl enable docker && systemctl start docker
else
  echo "✅ Docker موجود: $(docker --version)"
fi

# ── 2. استنساخ الريبو ────────────────────────────────────────
if [ ! -d /opt/the-market-lion ]; then
  echo "📥 استنساخ الكود من GitHub..."
  git clone https://github.com/RazanLeo/The-Market-Lion.git /opt/the-market-lion
else
  echo "🔄 تحديث الكود..."
  cd /opt/the-market-lion && git pull
fi

cd /opt/the-market-lion/app

# ── 3. نسخ ملف docker-compose.server.yml ─────────────────────
echo "📋 نسخ ملف الـ compose..."
# (هذا الملف رُفع مع الكود)

# ── 4. إعداد ملف .env ────────────────────────────────────────
if [ ! -f .env ]; then
  echo ""
  echo "⚠️  لم يُوجد ملف .env — جارٍ نسخ القيم الافتراضية..."
  echo "⚠️  عدّلي الملف بعد الانتهاء إذا أردتِ ربط Capital.com أو Stripe"
  cp .env.example .env
  # توليد مفاتيح عشوائية تلقائياً
  JWT_SECRET=$(openssl rand -hex 64)
  ENC_KEY=$(openssl rand -base64 32)
  DB_PASS=$(openssl rand -hex 16)
  sed -i "s|replace-with-long-random-string-min-64-chars|$JWT_SECRET|g" .env
  sed -i "s|replace-with-32-byte-base64-key.*|$ENC_KEY|g" .env
  sed -i "s|change_me_strong_password|$DB_PASS|g" .env
  sed -i "s|DATABASE_URL=postgresql+asyncpg://marketlion:change_me_strong_password|DATABASE_URL=postgresql+asyncpg://marketlion:$DB_PASS|g" .env
  sed -i "s|DATABASE_URL_SYNC=postgresql://marketlion:change_me_strong_password|DATABASE_URL_SYNC=postgresql://marketlion:$DB_PASS|g" .env
  sed -i "s|APP_ENV=development|APP_ENV=production|g" .env
  sed -i "s|NODE_ENV=development|NODE_ENV=production|g" .env
  sed -i "s|APP_URL=http://localhost:3000|APP_URL=http://161.35.192.36|g" .env
  sed -i "s|API_URL=http://localhost:8000|API_URL=http://161.35.192.36/api|g" .env
  sed -i "s|PUBLIC_API_URL=http://localhost:8000|PUBLIC_API_URL=http://161.35.192.36/api|g" .env
  echo "✅ .env جاهز بمفاتيح عشوائية آمنة"
else
  echo "✅ .env موجود بالفعل"
fi

# ── 5. نسخ compose file ───────────────────────────────────────
cp /opt/the-market-lion/app/docker-compose.server.yml /opt/the-market-lion/app/docker-compose.server.yml 2>/dev/null || true

# ── 6. بناء وتشغيل ───────────────────────────────────────────
echo ""
echo "🏗️  بناء الصور Docker (قد يأخذ 5-10 دقائق)..."
docker compose -f docker-compose.server.yml build --parallel

echo ""
echo "🚀 تشغيل المنصة..."
docker compose -f docker-compose.server.yml up -d

# ── 7. تشغيل migrations ──────────────────────────────────────
echo "⏳ انتظار قاعدة البيانات..."
sleep 15
docker compose -f docker-compose.server.yml exec -T backend alembic upgrade head 2>/dev/null || \
  echo "⚠️  migrations: تحقّقي يدوياً لاحقاً"

# ── 8. التحقق ────────────────────────────────────────────────
echo ""
echo "🔍 التحقق من الخدمات..."
sleep 5
docker compose -f docker-compose.server.yml ps

echo ""
API_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/v1/health 2>/dev/null || echo "---")
echo "API Health: $API_STATUS"

FRONT_STATUS=$(curl -s -o /dev/null -w "%{http_code}" http://localhost/ 2>/dev/null || echo "---")
echo "Frontend: $FRONT_STATUS"

echo ""
echo "================================================================"
echo "✅ المنصة تعمل على: http://161.35.192.36/dashboard"
echo "================================================================"
