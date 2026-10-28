# Публичный хостинг Mirro — Runbook (деплой на VPS)

Краткий практический план, как выложить Mirro в интернет и открыть её по домену.
Все команды ниже — для Linux-сервера (VPS). На домашнем ПК тот же код работает
только для локальной сети; для интернета нужен выделенный IP и проброс порта.

---

## 0. Что нужно заранее

- **VPS / облако** (минимум 1–2 vCPU, 4 ГБ RAM; Mirro держит в памяти ~1,3 млн
  примеров и индекс, ей нужно ≥4 ГБ RAM и ~10 ГБ диска).
- **Домен** (см. shortlist свободных ниже) + DNS, где сменишь A-запись.
- **Сертификат HTTPS** — бесплатный через Let's Encrypt (certbot).
- **Git-репо** уже есть: `github.com/kepanasyuke/Mirro-` (не коммитит данные:
  корпус, кэш, секреты).

## 1. Домен

Шорт-лист (проверено 2026-10-28):

| Домен         | Статус     | Комментарий                                      |
|---------------|------------|--------------------------------------------------|
| `mirro.ru`    | ЗАНЯТ      | владелец другой; оплачен до 04.2027 (выкуп дорого)|
| `mirro-ai.ru` | СВОБОДЕН   | ✅ лучший свободный вариант «.ru»                 |
| `mirror-ai.ru`| ЗАНЯТ      | чужой, до 06.2027                                 |
| `mirro.app`   | не проверился | уточнить у регистратора                          |

Рекомендуется зарегистрировать `mirro-ai.ru` (или другое свободное) через
любого регистратора `.ru` (reg.ru, nic.ru и т.п.).

## 2. Развёртывание на VPS

```bash
# на VPS (Ubuntu/Debian)
sudo apt update && sudo apt install -y python3 python3-pip git
git clone https://github.com/kepanasyuke/Mirro-.git ~/mirro
cd ~/mirro

# положить ключ DeepSeek (необязательно) и токен доступа
mkdir -p core
printf '{"deepseek":"СКОПИРУЙ_КЛЮЧ"}' > core/providers_secret.json
# токен для публичного доступа — обязателен! (иначе сервер открыт всем)
export MIRRO_TOKEN='придумай_длинный_токен'

# запуск (слушает 0.0.0.0:3443)
MIRRO_HOST=0.0.0.0 MIRRO_PORT=3443 python3 core/mirro_core.py
```

## 3. HTTPS за фронт-прокси (рекомендуется)

Отдавать Mirro напрямую в интернет нельзя. Ставь nginx как терминатор HTTPS:

```nginx
# /etc/nginx/sites-available/mirro
server {
    listen 80;
    server_name mirro-ai.ru www.mirro-ai.ru;
    location / { return 301 https://$host$request_uri; }
}
server {
    listen 443 ssl;
    server_name mirro-ai.ru;
    # certbot выдаст сертификаты сюда
    ssl_certificate     /etc/letsencrypt/live/mirro-ai.ru/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/mirro-ai.ru/privkey.pem;

    client_max_body_size 2m;

    location / {
        proxy_pass http://127.0.0.1:3443;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

```bash
sudo certbot --nginx -d mirro-ai.ru -d www.mirro-ai.ru
sudo nginx -s reload
```

## 4. Безопасность публичного доступа

- ✅ **Токен обязателен**: запускай с `MIRRO_TOKEN=...`. Тогда API требует
  `Authorization: Bearer <token>` или `?token=`. Без токена — 401.
- ⚠️ `Access-Control-Allow-Origin: *` в Mirro — для публичного API предпочтительно
  ограничить (можно сузить на nginx уровнем).
- Не открывай порт 3443 наружу в обход nginx.

## 5. Автозапуск (systemd)

```ini
# /etc/systemd/system/mirro.service
[Unit]
Description=Mirro neural network
After=network.target

[Service]
WorkingDirectory=/root/mirro
Environment=MIRRO_TOKEN=__TOKEN__
EnvironmentFile=/etc/mirro.env
ExecStart=/usr/bin/python3 core/mirro_core.py
Restart=always
User=root

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now mirro
```

## 6. Проверка

```bash
curl -i "https://mirro-ai.ru/health?token=$MIRRO_TOKEN"     # 200
curl -i "https://mirro-ai.ru/health"                          # 401
curl -s "https://mirro-ai.ru/v1/chat/completions?token=$MIRRO_TOKEN" \
  -H 'Content-Type: application/json' \
  -d '{"messages":[{"role":"user","content":"привет"}]}'
```

---

## Деньги

- **DeepSeek API** — пополнение по токенам, единовременно начать можно и с ~100 ₽,
  хватит на большой объём; минимум на балансе у провайдера обычно ~$1–2.
- **Домен** (rub `mirro-ai.ru`) — обычно несколько сотен рублей в год.
- **VPS** — от ~150–300 ₽/мес (минимальная конфигурация).
- **certbot/Let's Encrypt** — бесплатно.

Замечание: регистрацию домена и оплату VPS делаешь ты через свои аккаунты;
я могу генерировать конфиги и автоматизировать деплой на VPS, когда он будет.