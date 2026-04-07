# Deploy qo'llanmasi — chat.codestep.uz

**Server:** 64.226.104.135
**User:** root
**App papkasi:** /var/www/auth/aichat
**Port:** 8035 (Nginx orqali 443/80 → 8035)

---

## 1. Serverga kirish va tayyorgarlik

```bash
ssh root@64.226.104.135
```

```bash
# Tizim paketlarini yangilash
apt-get update && apt-get upgrade -y

# Kerakli paketlar
apt-get install -y python3.11 python3.11-venv python3-pip \
    redis-server nginx certbot python3-certbot-nginx git
```

---

## 2. Redisni yoqish

```bash
systemctl enable redis-server
systemctl start redis-server

# Tekshirish
redis-cli ping
# PONG chiqishi kerak
```

---

## 3. Loyihani serverga yuklash

**Variant A — git clone:**
```bash
mkdir -p /var/www/auth/aichat
git clone https://github.com/YOUR/sport-ai.git /var/www/auth/aichat
```

**Variant B — scp (lokal kompyuterdan):**
```bash
# Lokal kompyuterda (git bash / terminal)
scp -r d:/sport/ai.sport/* root@64.226.104.135:/var/www/auth/aichat/
```

---

## 4. Python virtual muhit va kutubxonalar

```bash
cd /var/www/auth/aichat

# Venv yaratish
python3.11 -m venv .venv

# Activate
source .venv/bin/activate

# Kutubxonalarni o'rnatish
pip install --upgrade pip
pip install -r requirements.txt
```

---

## 5. .env faylini tekshirish

```bash
cat /var/www/auth/aichat/.env
```

`.env` to'g'ri ko'rinishi kerak (OPENAI_API_KEY hali bo'sh bo'lsa ham):
```
POSTGRES_HOST=64.226.104.135   # yoki localhost
POSTGRES_DB=aisport
POSTGRES_USER=postgres
POSTGRES_PASSWORD=new_secure_password
SECRET_KEY=76d132bce...
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_DB=0
PORT=8035
```

> ⚠️ POSTGRES_HOST: agar app va DB bir xil serverdda bo'lsa `localhost` yaxshiroq!

---

## 6. Ma'lumotlar bazasi migratsiyasi

```bash
cd /var/www/auth/aichat
source .venv/bin/activate

alembic upgrade head
```

Muvaffaqiyatli bo'lsa:
```
INFO  [alembic.runtime.migration] Running upgrade  -> 001, Initial schema
```

---

## 7. Namuna ma'lumotlarni kiritish (ixtiyoriy)

```bash
python scripts/seed_data.py
```

---

## 8. FAISS indeksini qurish

> ⚠️ Bu qadam OPENAI_API_KEY bo'lgandan keyin bajariladi!

```bash
python scripts/build_index.py
```

---

## 9. Systemd service fayllarini o'rnatish

```bash
# Fayllarni nusxalash
cp /var/www/auth/aichat/deploy/sport-ai.service        /etc/systemd/system/
cp /var/www/auth/aichat/deploy/sport-ai-worker.service /etc/systemd/system/

# Reload
systemctl daemon-reload

# Yoqish va ishga tushurish
systemctl enable sport-ai sport-ai-worker
systemctl start  sport-ai sport-ai-worker

# Holat tekshirish
systemctl status sport-ai
systemctl status sport-ai-worker
```

Muvaffaqiyatli bo'lsa:
```
● sport-ai.service - Sport Analytics AI — FastAPI (port 8035)
   Active: active (running)
```

---

## 10. Nginx sozlash

```bash
# Config faylini joylashtirish
cp /var/www/auth/aichat/deploy/nginx.conf \
   /etc/nginx/sites-available/chat.codestep.uz

# Yoqish
ln -s /etc/nginx/sites-available/chat.codestep.uz \
      /etc/nginx/sites-enabled/chat.codestep.uz

# Eski default o'chirish (agar bo'lsa)
rm -f /etc/nginx/sites-enabled/default

# Tekshirish
nginx -t

# Ishga tushurish
systemctl enable nginx
systemctl reload nginx
```

---

## 11. SSL sertifikat olish (Let's Encrypt)

> ⚠️ Avval `chat.codestep.uz` DNS da serverga (64.226.104.135) yo'naltirilgan bo'lishi shart!

```bash
# DNS tekshirish
nslookup chat.codestep.uz
# 64.226.104.135 chiqishi kerak

# SSL olish
certbot --nginx -d chat.codestep.uz \
    --non-interactive --agree-tos \
    --email admin@codestep.uz \
    --redirect

# Nginx reload
systemctl reload nginx
```

---

## 12. Tekshirish

```bash
# App ishlayaptimi?
curl http://127.0.0.1:8035/login

# HTTPS ishlayaptimi?
curl https://chat.codestep.uz/login

# Loglar
journalctl -u sport-ai        -f   # FastAPI logs
journalctl -u sport-ai-worker -f   # ARQ worker logs

# Redis job navbati
redis-cli llen arq:queue:default
```

---

## Keyingi yangilanishlar

```bash
cd /var/www/auth/aichat
git pull

source .venv/bin/activate
pip install -r requirements.txt   # yangi kutubxona bo'lsa

alembic upgrade head               # yangi migration bo'lsa

systemctl restart sport-ai sport-ai-worker
```

---

## Foydali komandalar

```bash
# Servislarni to'xtatish/ishga tushurish
systemctl stop    sport-ai sport-ai-worker
systemctl start   sport-ai sport-ai-worker
systemctl restart sport-ai sport-ai-worker

# Real-time loglar
journalctl -u sport-ai -n 50 --no-pager

# FAISS indeksini qayta qurish (admindan ham qilsa bo'ladi)
cd /var/www/auth/aichat && source .venv/bin/activate
python scripts/build_index.py

# SSL yangilash (avtomatik, lekin qo'lda ham)
certbot renew --dry-run
```
