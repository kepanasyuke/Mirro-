#!/usr/bin/env bash
# =============================================================================
# Mirro — автодеплой на VPS (Ubuntu/Debian)
# -----------------------------------------------------------------------------
# Ставит зависимости, клонирует/обновляет репо, настраивает systemd-сервис с
# токеном доступа и env-файлом для ключа DeepSeek, показывает как выпустить
# HTTPS-сертификат. Запуск от root (или с sudo) на чистом VPS.
#
#   sudo bash scripts/deploy_vps.sh
#
# Перед запуском посмотри переменные ниже и подставь свои.
# =============================================================================
set -euo pipefail

# ---- Конфигурация (подставь свои значения) -------------------------------
REPO_URL="https://github.com/kepanasyuke/Mirro-.git"
APP_DIR="/opt/mirro"
RUN_USER="mirro"                # системный пользователь, от которого работает сервер
MIRRO_PORT="3443"
# Секреты/токены из env окружения или переменных ниже (НИКОГДА не коммить):
MIRRO_TOKEN="${MIRRO_TOKEN:-CHANGE_ME_длинный_случайный_токен}"
DEEPSEEK_KEY="${DEEPSEEK_KEY:-}"   # если пусто — DeepSeek включится позже
# ---------------------------------------------------------------------------

echo "==> [1/6] Базовые пакеты"
export DEBIAN_FRONTEND=noninteractive
apt-get update -y
apt-get install -y python3 python3-pip git curl nginx

echo "==> [2/6] Системный пользователь"
id -u "$RUN_USER" &>/dev/null || useradd -r -m -d "$APP_DIR" -s /usr/sbin/nologin "$RUN_USER"

echo "==> [3/6] Код"
if [ -d "$APP_DIR/.git" ]; then
  git -C "$APP_DIR" pull --ff-only
else
  git clone "$REPO_URL" "$APP_DIR"
fi
chown -R "$RUN_USER:" "$APP_DIR"

echo "==> [4/6] Секреты и токен"
cat > "$APP_DIR/core/providers_secret.json" <<JSON
{"deepseek": "${DEEPSEEK_KEY}"}
JSON
cat > /etc/mirro.env <<ENV
MIRRO_HOST=0.0.0.0
MIRRO_PORT=${MIRRO_PORT}
MIRRO_TOKEN=${MIRRO_TOKEN}
DEEPSEEK_API_KEY=${DEEPSEEK_KEY}
ENV
chmod 600 /etc/mirro.env

echo "==> [5/6] systemd-сервис"
cat > /etc/systemd/system/mirro.service <<UNIT
[Unit]
Description=Mirro neural network
After=network.target

[Service]
Type=simple
User=${RUN_USER}
WorkingDirectory=${APP_DIR}
EnvironmentFile=/etc/mirro.env
ExecStart=/usr/bin/python3 core/mirro_core.py
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
UNIT
systemctl daemon-reload
systemctl enable mirro

echo "==> [6/6] Nginx-порт (прокси на 3443)"
if ! grep -q "mirro-ai.ru" /etc/nginx/sites-enabled/* 2>/dev/null; then
cat > /etc/nginx/sites-available/mirro <<NGINX
server {
    listen 80;
    server_name mirro-ai.ru www.mirro-ai.ru;   # ← замени на свой домен
    client_max_body_size 2m;
    location / {
        proxy_pass http://127.0.0.1:${MIRRO_PORT};
        proxy_set_header Host \$host;
        proxy_set_header X-Real-IP \$remote_addr;
    }
}
NGINX
ln -sf /etc/nginx/sites-available/mirro /etc/nginx/sites-enabled/mirro
nginx -t
systemctl reload nginx || true
fi

echo "==> Запуск сервиса"
systemctl restart mirro
sleep 3
systemctl --no-pager status mirro --no-pager || true

echo
echo "Готово. Проверь:"
echo "  curl -i 'http://127.0.0.1:${MIRRO_PORT}/health?token=${MIRRO_TOKEN}'   # 200"
echo "  curl -i 'http://127.0.0.1:${MIRRO_PORT}/health'                        # 401"
echo "HTTPS (после того как домен прописан):"
echo "  sudo certbot --nginx -d mirro-ai.ru -d www.mirro-ai.ru"
echo
echo "⚠️  Домен 'mirro-ai.ru' замени в /etc/nginx/sites-available/mirro и в certbot."