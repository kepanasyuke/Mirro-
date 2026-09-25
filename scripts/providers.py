# -*- coding: utf-8 -*-
"""
Mirro Providers — слой легальных ИИ-провайдеров.
==================================================
Mirro сначала ищет ответ в своей базе (TF-IDF), корпусе (RAG) и интернете.
Если ничего не нашла — подключается внешний провайдер (DeepSeek, OpenAI-совместимый).

Без внешних зависимостей: только urllib из стандартной библиотеки.

Провайдеры:
  - deepseek: api.deepseek.com (работает из РФ, OpenAI-совместимый)
  - openai:   api.openai.com   (по желанию)

Ключ берётся из переменной окружения DEEPSEEK_API_KEY (или OPENAI_API_KEY).
"""

import json
import os
from pathlib import Path
import urllib.request
import urllib.error

SYS_PROMPT = (
    "Ты — Mirro, эволюционная нейросеть знаний, созданная в России. "
    "Отвечай кратко, по делу, на русском языке. "
    "Если не знаешь — честно скажи, что не знаешь, не выдумывай."
)

DEFAULT_TIMEOUT = 30
MAX_TOKENS = 600

PROVIDERS = {
    "deepseek": {
        "env": "DEEPSEEK_API_KEY",
        "url": "https://api.deepseek.com/chat/completions",
        "model": "deepseek-chat",
    },
    "openai": {
        "env": "OPENAI_API_KEY",
        "url": "https://api.openai.com/v1/chat/completions",
        "model": "gpt-4o-mini",
    },
}


def _resolve_key(provider):
    """Ключ провайдера: env → файл secrets (не коммитится)."""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        return ""
    # 1) переменная окружения
    env_key = os.environ.get(cfg["env"], "").strip()
    if env_key:
        return env_key
    # 2) файл секретов D:\Mirro\core\providers_secret.json (в .gitignore)
    try:
        secret_file = Path(__file__).resolve().parent.parent / "core" / "providers_secret.json"
        if secret_file.exists():
            data = json.loads(secret_file.read_text("utf-8"))
            val = str(data.get(provider, "")).strip()
            if val and val.lower() not in ("", "none", "your-key-here"):
                return val
    except Exception:
        pass
    return ""


def _call_provider(provider, messages, timeout=DEFAULT_TIMEOUT):
    """Послать запрос провайдеру (OpenAI-совместимый формат). Вернуть текст ответа."""
    cfg = PROVIDERS.get(provider)
    if not cfg:
        return None
    key = _resolve_key(provider)
    if not key:
        return None

    body = {
        "model": cfg["model"],
        "messages": messages,
        "max_tokens": MAX_TOKENS,
        "temperature": 0.6,
    }
    req = urllib.request.Request(
        cfg["url"],
        data=json.dumps(body).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "Authorization": f"Bearer {key}",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            data = json.loads(resp.read().decode("utf-8"))
        return data["choices"][0]["message"]["content"].strip()
    except urllib.error.HTTPError as e:
        try:
            detail = e.read().decode("utf-8")[:200]
        except Exception:
            detail = str(e)
        return f"[провайдер {provider}: ошибка {e.code}] {detail}"
    except Exception as e:
        return None


def deepseek(prompt, system=None, timeout=DEFAULT_TIMEOUT):
    """Ответ DeepSeek на вопрос пользователя."""
    messages = [
        {"role": "system", "content": system or SYS_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return _call_provider("deepseek", messages, timeout)


def fallback(prompt, system=None, timeout=DEFAULT_TIMEOUT):
    """Финальный фоллбэк: пробуем по очереди провайдеров."""
    for provider in ("deepseek", "openai"):
        if not _resolve_key(provider):
            continue
        messages = [
            {"role": "system", "content": system or SYS_PROMPT},
            {"role": "user", "content": prompt},
        ]
        out = _call_provider(provider, messages, timeout)
        if out and not out.startswith("[провайдер"):
            return out
    return None


def status():
    """Статус подключённых провайдеров (без ключей)."""
    out = {}
    for name in PROVIDERS:
        out[name] = bool(_resolve_key(name))
    return out


def save_keys(deepseek="", openai=""):
    """Сохранить ключи в файл секретов (не коммитится). Пустая строка = не менять."""
    secret_file = Path(__file__).resolve().parent.parent / "core" / "providers_secret.json"
    data = {}
    if secret_file.exists():
        try:
            data = json.loads(secret_file.read_text("utf-8"))
        except Exception:
            data = {}
    if deepseek:
        data["deepseek"] = deepseek.strip()
    if openai:
        data["openai"] = openai.strip()
    secret_file.write_text(json.dumps(data, ensure_ascii=False, indent=2), "utf-8")
    return bool(data)