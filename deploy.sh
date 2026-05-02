#!/bin/bash
# Market Lion — Deploy to DigitalOcean
# Usage: ./deploy.sh [server_ip]

SERVER=${1:-161.35.192.36}
REMOTE_DIR=/root/market-lion-v2

echo "🦁 Deploying Market Lion to $SERVER..."

# Push to server
rsync -avz --exclude='.git' --exclude='node_modules' --exclude='__pycache__' \
  --exclude='.next' --exclude='*.pyc' \
  ./ root@$SERVER:$REMOTE_DIR/

# Run on server
ssh root@$SERVER << 'ENDSSH'
  cd /root/market-lion-v2

  # Copy env if not exists
  if [ ! -f .env ]; then
    cp .env.example .env
    echo "⚠️  Created .env from example — edit it with real credentials!"
  fi

  # Build and start
  docker compose down --remove-orphans
  docker compose build --no-cache
  docker compose up -d

  # Wait and check
  sleep 10
  docker compose ps
  echo ""
  echo "✅ Deployment complete!"
  echo "🌐 Frontend: http://161.35.192.36"
  echo "🔌 API: http://161.35.192.36/api"
ENDSSH
