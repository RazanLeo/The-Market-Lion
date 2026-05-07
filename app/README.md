# 🦁 The Market Lion — أسد السوق

**Razan AI Trading Platform — "Bot & Indicator"**

منصة تداول احترافية بالذكاء الاصطناعي تدمج 89+ مدرسة تحليل و120+ مؤشر فني، تربط مباشرة بحسابات التداول الحقيقية وتقدّم تحليلاً شاملاً واتخاذ قرار آلي/يدوي بنظام تصويت متعدد المدارس.

## بنية المستودع

```
app/
├── frontend/           # Next.js 14 (App Router) + TypeScript + Tailwind + 12 لغة
├── backend/            # FastAPI + SQLAlchemy + Celery + Postgres/TimescaleDB + Redis
├── infra/              # Caddy + Prometheus + Grafana + scripts النشر
├── docs/               # ARCHITECTURE.md + DEPLOY.md + API.md + ALGORITHMS.md
└── .github/workflows/  # CI/CD
```

## التشغيل المحلي السريع

```bash
cp .env.example .env
docker compose -f docker-compose.dev.yml up --build
# Frontend: http://localhost:3000
# Backend:  http://localhost:8000
# Admin:    http://localhost:3000/admin (يحتاج حساب super_admin)
```

## النشر الإنتاجي

راجع `docs/DEPLOY.md` لخطوات النشر على DigitalOcean Droplet 161.35.192.36.

## الترخيص والامتثال

راجع `docs/COMPLIANCE.md` و `frontend/app/[locale]/(static)/risk/page.tsx`.
الإفصاح القانوني يظهر في الفوتر فقط + سطر مختصر في صفحة الاشتراك.

## الشعار

ملف الشعار الرسمي: `frontend/public/brand/logo.jpg` — يُستخدم نسخاً ولصقاً.

## المرجع الرسمي

البرومبت الكامل المُحقَّق: `../MARKET_LION_MASTER_PROMPT.docx` و `../MARKET_LION_MASTER_PROMPT.md`.

— © 2026 The Market Lion. All Rights Reserved.
