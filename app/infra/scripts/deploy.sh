#!/usr/bin/env bash
# One-shot bootstrap for DigitalOcean Droplet (Ubuntu 24.04)
# Run as root or with sudo on 161.35.192.36.
set -euo pipefail

REPO_URL="${REPO_URL:-https://github.com/RazanLeo/The-Market-Lion.git}"
APP_DIR="/opt/the-market-lion"

echo ">> Updating apt"
apt-get update -y && apt-get upgrade -y

echo ">> Installing Docker + tools"
apt-get install -y ca-certificates curl gnupg git ufw fail2ban
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg | gpg --dearmor -o /etc/apt/keyrings/docker.gpg
chmod a+r /etc/apt/keyrings/docker.gpg
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.gpg] https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo $VERSION_CODENAME) stable" \
  > /etc/apt/sources.list.d/docker.list
apt-get update -y
apt-get install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

echo ">> Firewall"
ufw allow 22/tcp
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable

echo ">> Cloning repo"
mkdir -p "$APP_DIR"
if [ ! -d "$APP_DIR/.git" ]; then
  git clone "$REPO_URL" "$APP_DIR"
fi

cd "$APP_DIR/app"
if [ ! -f .env ]; then
  echo "!! .env missing — copy from .env.example and fill secrets, then re-run"
  cp .env.example .env
  echo "Edit /opt/the-market-lion/app/.env and re-run this script."
  exit 1
fi

echo ">> Building and starting stack"
docker compose -f docker-compose.prod.yml pull || true
docker compose -f docker-compose.prod.yml up -d --remove-orphans

echo ">> Waiting for backend health"
for i in {1..30}; do
  if curl -fsS http://localhost:8000/healthz; then echo "OK"; break; fi
  sleep 2
done

echo ">> Running migrations"
docker compose -f docker-compose.prod.yml exec -T backend alembic upgrade head

echo "Deployment complete. Caddy is serving 80/443."
