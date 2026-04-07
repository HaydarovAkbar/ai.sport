#!/bin/bash
# setup-ssl.sh — Install certbot and obtain Let's Encrypt SSL for chat.codestep.uz
# Run as root (or with sudo) on the production server.
#
# Usage:
#   chmod +x deploy/setup-ssl.sh
#   sudo ./deploy/setup-ssl.sh

set -e

DOMAIN="chat.codestep.uz"
EMAIL="admin@codestep.uz"     # ← change to your real email

echo "==> Installing certbot..."
apt-get update -qq
apt-get install -y certbot python3-certbot-nginx

echo "==> Creating webroot for ACME challenge..."
mkdir -p /var/www/certbot

echo "==> Obtaining SSL certificate for ${DOMAIN}..."
certbot --nginx \
    -d "${DOMAIN}" \
    --non-interactive \
    --agree-tos \
    --email "${EMAIL}" \
    --redirect

echo "==> Setting up auto-renewal..."
# certbot installs a systemd timer by default; verify:
systemctl status certbot.timer || true

echo "==> Testing Nginx config..."
nginx -t

echo "==> Reloading Nginx..."
systemctl reload nginx

echo ""
echo "✅ SSL setup complete!"
echo "   Certificate: /etc/letsencrypt/live/${DOMAIN}/fullchain.pem"
echo "   Auto-renewal: systemctl status certbot.timer"
