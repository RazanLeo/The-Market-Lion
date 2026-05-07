# Deploy Guide — The Market Lion

## Production target: DigitalOcean Droplet `161.35.192.36` (Ubuntu 24.04)

### One-liner (run inside DigitalOcean Web Console)

```bash
curl -fsSL https://raw.githubusercontent.com/RazanLeo/The-Market-Lion/main/app/infra/scripts/deploy.sh | bash
```

That script will:
1. Install Docker + Compose + UFW + fail2ban.
2. Clone repo → `/opt/the-market-lion`.
3. Copy `.env.example` → `.env` (you must then edit with secrets).
4. Bring up the entire stack (Caddy + Postgres/TimescaleDB + Redis + backend + workers + beat + frontend).
5. Run Alembic migrations.
6. Smoke-test `/healthz`.

### Filling secrets (only the first time)

```bash
nano /opt/the-market-lion/app/.env
```

Required at minimum:
- `JWT_SECRET=$(openssl rand -base64 64 | head -c 64)`
- `ENCRYPTION_KEY=$(openssl rand -base64 32 | head -c 32)`
- `POSTGRES_PASSWORD` (any strong)
- `CAPITAL_API_KEY` / `CAPITAL_API_PASSWORD` / `CAPITAL_IDENTIFIER` (Capital.com Demo or Live)

After filling, re-run the same one-liner — it is idempotent.

### DNS

Point `marketlion.ai` (or your chosen domain) A-record → `161.35.192.36`.
Caddy handles Let's Encrypt automatically.

### Create super-admin (Razan)

```bash
docker compose -f /opt/the-market-lion/app/docker-compose.prod.yml exec backend python -c "
import asyncio
from app.db.base import AsyncSessionLocal
from app.db.models import User
from app.core.security import hash_password
async def main():
    async with AsyncSessionLocal() as db:
        u = User(email='razan.tawfiq@gmail.com', password_hash=hash_password('CHANGE_THIS_NOW_xxxx'),
                full_name='Razan Tawfiq', role='super_admin', status='active', email_verified=True)
        db.add(u); await db.commit()
asyncio.run(main())
"
```

### Updates

```bash
cd /opt/the-market-lion && git pull
cd app && docker compose -f docker-compose.prod.yml pull && docker compose -f docker-compose.prod.yml up -d
docker compose -f docker-compose.prod.yml exec backend alembic upgrade head
```

### Backups

`pgBackRest` daily + DO Spaces snapshots. See `infra/scripts/`.

### Monitoring

Prometheus + Grafana running inside compose; dashboards at `http://<host>:3001` after wiring port. Sentry: set `SENTRY_DSN` in `.env`.
