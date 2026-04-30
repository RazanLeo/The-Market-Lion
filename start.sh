#!/usr/bin/env bash
# ═══════════════════════════════════════════════════════════════════════════
#  أسد السوق — The Market Lion  |  Quick Start Script
#  Usage: ./start.sh [dev|docker|stop|logs|status]
# ═══════════════════════════════════════════════════════════════════════════
set -euo pipefail

LION_GREEN='\033[0;32m'
LION_GOLD='\033[0;33m'
LION_RED='\033[0;31m'
LION_CYAN='\033[0;36m'
NC='\033[0m'

banner() {
  echo -e "${LION_GOLD}"
  echo "  ██╗     ██╗ ██████╗ ███╗   ██╗"
  echo "  ██║     ██║██╔═══██╗████╗  ██║"
  echo "  ██║     ██║██║   ██║██╔██╗ ██║"
  echo "  ██║     ██║██║   ██║██║╚██╗██║"
  echo "  ███████╗██║╚██████╔╝██║ ╚████║"
  echo "  ╚══════╝╚═╝ ╚═════╝ ╚═╝  ╚═══╝"
  echo -e "${NC}  أسد السوق — The Market Lion  v2.0${NC}"
  echo ""
}

info()    { echo -e "${LION_CYAN}ℹ  $*${NC}"; }
success() { echo -e "${LION_GREEN}✅ $*${NC}"; }
warn()    { echo -e "${LION_GOLD}⚠  $*${NC}"; }
error()   { echo -e "${LION_RED}❌ $*${NC}"; exit 1; }

# ── Pre-flight checks ───────────────────────────────────────────────────────
check_docker() {
  if ! command -v docker &>/dev/null; then
    error "Docker غير مثبت. ثبّته من https://docker.com ثم أعد المحاولة."
  fi
  if ! docker info &>/dev/null; then
    error "Docker daemon غير مُشغَّل. شغّل Docker Desktop ثم أعد المحاولة."
  fi
  if ! docker compose version &>/dev/null; then
    error "Docker Compose v2 مطلوب. حدّث Docker Desktop أو ثبّت plugin Compose."
  fi
}

# ── .env setup ──────────────────────────────────────────────────────────────
setup_env() {
  if [ ! -f .env ]; then
    cp .env.example .env
    warn "تم إنشاء ملف .env من القالب"
    warn "يجب ملء مفاتيح الـ API قبل بدء التشغيل الكامل:"
    echo ""
    echo "  المفاتيح الإلزامية:"
    echo "  ┌─ JWT_SECRET      — سلسلة عشوائية طويلة (64+ حرف)"
    echo "  ├─ ENCRYPTION_KEY  — مفتاح Fernet (انظر التعليمات في .env.example)"
    echo ""
    echo "  مفاتيح البيانات (مجانية):"
    echo "  ├─ ALPHA_VANTAGE_KEY  — https://alphavantage.co"
    echo "  ├─ NEWSAPI_KEY        — https://newsapi.org"
    echo "  ├─ FRED_API_KEY       — https://fred.stlouisfed.org/docs/api/"
    echo "  └─ TELEGRAM_BOT_TOKEN — من BotFather في تيليغرام"
    echo ""
    read -rp "هل تريد تعديل .env الآن؟ [y/N] " ans
    if [[ "$ans" =~ ^[Yy] ]]; then
      ${EDITOR:-nano} .env
    fi
  fi

  # Validate JWT_SECRET
  JWT_VAL=$(grep -E '^JWT_SECRET=' .env | cut -d= -f2- | tr -d '"' || echo "")
  if [[ -z "$JWT_VAL" || "$JWT_VAL" == "change_me"* ]]; then
    warn "JWT_SECRET يجب تغييره في .env قبل الإنتاج!"
  fi
}

# ── Wait for healthy service ─────────────────────────────────────────────────
wait_healthy() {
  local svc="$1"
  local max_attempts="${2:-30}"
  local attempt=0
  info "انتظار جاهزية $svc ..."
  while [ $attempt -lt $max_attempts ]; do
    status=$(docker compose ps --format json "$svc" 2>/dev/null | python3 -c "
import sys, json
lines = sys.stdin.read().strip().split('\n')
for line in lines:
    if line:
        d = json.loads(line)
        print(d.get('Health','').lower() or d.get('State','').lower())
        break
" 2>/dev/null || echo "")
    if [[ "$status" == "healthy" || "$status" == "running" ]]; then
      success "$svc جاهز"
      return 0
    fi
    attempt=$((attempt + 1))
    sleep 3
  done
  warn "انتهت مهلة الانتظار لـ $svc (قد يكون لا يزال يعمل)"
}

# ── Mode: docker ─────────────────────────────────────────────────────────────
run_docker() {
  info "بدء تشغيل كل الخدمات عبر Docker Compose ..."
  docker compose up --build -d

  echo ""
  info "انتظار جاهزية قواعد البيانات ..."
  wait_healthy postgres 30
  wait_healthy redis 20
  wait_healthy mongodb 25

  info "انتظار جاهزية الـ Gateway ..."
  wait_healthy gateway 40

  echo ""
  success "أسد السوق يعمل! 🦁"
  echo ""
  echo -e "  ${LION_GOLD}الروابط:${NC}"
  echo "  ┌─ لوحة التحكم:  http://localhost:3000"
  echo "  ├─ API Gateway:  http://localhost:8000"
  echo "  ├─ API Docs:     http://localhost:8000/docs"
  echo "  ├─ Auth Service: http://localhost:8001"
  echo "  ├─ Backtesting:  http://localhost:8002"
  echo "  ├─ Grafana:      http://localhost:3001  (admin / انظر GRAFANA_PASSWORD في .env)"
  echo "  └─ Prometheus:   http://localhost:9090"
  echo ""
}

# ── Mode: dev ────────────────────────────────────────────────────────────────
run_dev() {
  info "وضع التطوير — قواعد البيانات في Docker، الخدمات محلياً"
  docker compose up -d postgres timescaledb mongodb redis

  echo ""
  wait_healthy postgres 25
  wait_healthy redis 15

  info "تثبيت متطلبات Python ..."
  (cd backend && pip install -r requirements.txt -q)

  info "تشغيل الـ Gateway ..."
  (cd backend && uvicorn gateway.main:app --host 0.0.0.0 --port 8000 --reload) &
  BACKEND_PID=$!

  info "تثبيت متطلبات Node.js ..."
  (cd frontend/web && npm install -q)

  info "تشغيل Next.js frontend ..."
  (cd frontend/web && npm run dev) &
  FRONTEND_PID=$!

  success "وضع التطوير جاهز!"
  echo "  Dashboard: http://localhost:3000"
  echo "  API:       http://localhost:8000"
  echo "  Docs:      http://localhost:8000/docs"
  echo ""
  echo "  اضغط Ctrl+C للإيقاف"
  trap "kill \$BACKEND_PID \$FRONTEND_PID 2>/dev/null; docker compose down" EXIT
  wait
}

# ── Mode: stop ───────────────────────────────────────────────────────────────
run_stop() {
  info "إيقاف جميع الخدمات ..."
  docker compose down
  success "تم إيقاف جميع الخدمات"
}

# ── Mode: logs ───────────────────────────────────────────────────────────────
run_logs() {
  docker compose logs -f --tail=100 "${@:2}"
}

# ── Mode: status ─────────────────────────────────────────────────────────────
run_status() {
  docker compose ps
}

# ── Main ─────────────────────────────────────────────────────────────────────
banner
check_docker
setup_env

MODE="${1:-docker}"

case "$MODE" in
  dev)    run_dev    ;;
  docker) run_docker ;;
  stop)   run_stop   ;;
  logs)   run_logs "$@" ;;
  status) run_status ;;
  *)
    echo "الاستخدام: ./start.sh [dev|docker|stop|logs|status]"
    echo ""
    echo "  docker  — تشغيل كل شيء في Docker (الافتراضي)"
    echo "  dev     — قواعد البيانات في Docker والخدمات محلياً"
    echo "  stop    — إيقاف جميع الخدمات"
    echo "  logs    — عرض سجلات الخدمات"
    echo "  status  — حالة الخدمات"
    ;;
esac
