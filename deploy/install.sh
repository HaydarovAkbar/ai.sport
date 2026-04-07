#!/bin/bash
# install.sh — Full server setup for Sport Analytics AI
# Tested on Ubuntu 22.04 LTS
#
# Usage (as root or sudo):
#   chmod +x deploy/install.sh
#   sudo ./deploy/install.sh

set -e

APP_DIR="/var/www/sport-ai"
APP_USER="ubuntu"
DOMAIN="chat.codestep.uz"

echo "=== Sport Analytics AI — Server Install ==="

# ── 1. System packages ─────────────────────────────────────────────────
echo "==> Installing system packages..."
apt-get update -qq
apt-get install -y python3.11 python3.11-venv python3-pip \
    postgresql postgresql-contrib \
    redis-server \
    nginx \
    certbot python3-certbot-nginx \
    git curl

# ── 2. PostgreSQL ──────────────────────────────────────────────────────
echo "==> Configuring PostgreSQL..."
systemctl enable postgresql
systemctl start postgresql

# Create DB and user (edit password!)
DB_PASS="your_strong_password_here"
sudo -u postgres psql -c "CREATE USER sport_user WITH PASSWORD '${DB_PASS}';" 2>/dev/null || true
sudo -u postgres psql -c "CREATE DATABASE sport_db OWNER sport_user;" 2>/dev/null || true

# ── 3. Redis ───────────────────────────────────────────────────────────
echo "==> Starting Redis..."
systemctl enable redis-server
systemctl start redis-server

# ── 4. App directory ───────────────────────────────────────────────────
echo "==> Setting up app directory at ${APP_DIR}..."
mkdir -p "${APP_DIR}"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}"

# Clone or pull repo (adjust URL)
if [ ! -d "${APP_DIR}/.git" ]; then
    echo "  → Clone your repo into ${APP_DIR}"
    echo "  → git clone https://github.com/YOUR/sport-ai.git ${APP_DIR}"
    echo "  → Then re-run this script."
    exit 1
fi

# ── 5. Python virtualenv + dependencies ───────────────────────────────
echo "==> Creating virtualenv..."
sudo -u "${APP_USER}" python3.11 -m venv "${APP_DIR}/.venv"
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/pip" install --upgrade pip -q
sudo -u "${APP_USER}" "${APP_DIR}/.venv/bin/pip" install -r "${APP_DIR}/requirements.txt" -q

# ── 6. FAISS data directory ────────────────────────────────────────────
mkdir -p "${APP_DIR}/data/faiss"
chown -R "${APP_USER}:${APP_USER}" "${APP_DIR}/data"

# ── 7. .env file ───────────────────────────────────────────────────────
if [ ! -f "${APP_DIR}/.env" ]; then
    echo "==> Creating .env from example..."
    cp "${APP_DIR}/.env.example" "${APP_DIR}/.env"
    echo "  ⚠️  Edit ${APP_DIR}/.env and fill in real values!"
    echo "  ⚠️  Then run: alembic upgrade head && python scripts/seed_data.py"
fi

# ── 8. DB migration ────────────────────────────────────────────────────
echo "==> Running Alembic migrations..."
cd "${APP_DIR}"
sudo -u "${APP_USER}" .venv/bin/alembic upgrade head

# ── 9. systemd services ────────────────────────────────────────────────
echo "==> Installing systemd services..."
cp "${APP_DIR}/deploy/sport-ai.service"        /etc/systemd/system/
cp "${APP_DIR}/deploy/sport-ai-worker.service" /etc/systemd/system/
systemctl daemon-reload
systemctl enable sport-ai sport-ai-worker
systemctl start  sport-ai sport-ai-worker

# ── 10. Nginx ─────────────────────────────────────────────────────────
echo "==> Configuring Nginx..."
cp "${APP_DIR}/deploy/nginx.conf" "/etc/nginx/sites-available/${DOMAIN}"
ln -sf "/etc/nginx/sites-available/${DOMAIN}" "/etc/nginx/sites-enabled/${DOMAIN}"
rm -f /etc/nginx/sites-enabled/default
nginx -t
systemctl reload nginx

# ── 11. SSL ───────────────────────────────────────────────────────────
echo "==> Obtaining SSL certificate..."
bash "${APP_DIR}/deploy/setup-ssl.sh"

echo ""
echo "✅ Installation complete!"
echo "   App:    https://${DOMAIN}"
echo "   Logs:   journalctl -u sport-ai -f"
echo "   Worker: journalctl -u sport-ai-worker -f"
