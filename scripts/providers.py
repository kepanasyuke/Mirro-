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
    key = ""
    if cfg:
        # 1) переменная окружения
        env_key = os.environ.get(cfg["env"], "").strip()
        if env_key:
            key = env_key
        # 2) файл секретов <корень>/core/providers_secret.json (в .gitignore)
        if not key:
            try:
                secret_file = Path(__file__).resolve().parent.parent / "core" / "providers_secret.json"
                if secret_file.exists():
                    data = json.loads(secret_file.read_text("utf-8"))
                    val = str(data.get(provider, "")).strip()
                    if val and val.lower() not in ("", "none", "your-key-here"):
                        key = val
            except Exception:
                pass
    return key


def _call_provider(provider, messages, timeout=DEFAULT_TIMEOUT):
    """Послать запрос провайдеру (OpenAI-совместимый формат). Вернуть текст ответа."""
    cfg = PROVIDERS.get(provider)
    key = _resolve_key(provider)
    out = None
    if cfg and key:
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
            out = data["choices"][0]["message"]["content"].strip()
        except urllib.error.HTTPError as e:
            try:
                detail = e.read().decode("utf-8")[:200]
            except Exception:
                detail = str(e)
            out = f"[провайдер {provider}: ошибка {e.code}] {detail}"
        except Exception:
            out = None
    return out


def deepseek(prompt, system=None, timeout=DEFAULT_TIMEOUT):
    """Ответ DeepSeek на вопрос пользователя."""
    messages = [
        {"role": "system", "content": system or SYS_PROMPT},
        {"role": "user", "content": prompt},
    ]
    return _call_provider("deepseek", messages, timeout)


def fallback(prompt, system=None, timeout=DEFAULT_TIMEOUT):
    """Финальный фоллбэк: пробуем по очереди провайдеров. Один return: str|None."""
    result = None
    for provider in ("deepseek", "openai"):
        if _resolve_key(provider):
            messages = [
                {"role": "system", "content": system or SYS_PROMPT},
                {"role": "user", "content": prompt},
            ]
            out = _call_provider(provider, messages, timeout)
            if out and not out.startswith("[провайдер"):
                result = out
                break
    return result


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