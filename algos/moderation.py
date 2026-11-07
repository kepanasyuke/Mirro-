# -*- coding: utf-8 -*-
"""Mirro Moderation — фильтр нежелательного контента и безопасный отклик.

Проверяет ВХОДЯЩИЙ запрос и ИСХОДЯЩИЙ ответ на опасные/нежелательные категории
(оскорбления/харассмент, опасные инструкции, приватность, экстремизм). Если
запрос опасен — возвращает вежливый безопасный отказ. Неподходящий ответ —
гасится и заменяется безопасной фразой. Провалы пишутся в журнал отклонений
для прозрачности (data/moderation_log.jsonl), но скрипт тих и не падает.

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import json
import os
import re as _re
import time

_DATA_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "data")
_LOG_FILE = os.path.join(_DATA_DIR, "moderation_log.jsonl")

# категории нежелательного контента -> маркеры (основы слов)
_CATEGORIES = {
    "harassment": ("оскорбл", "униз", "ненавиж", "убей себя", "иди ты на",
                   "туп", "дебил", "идиот", "дурак", "урод"),
    "danger_instr": ("как сделать бомб", "как изготовить взрывчат", "купить оружие без",
                     "сделай наркотик", "как взломать банк", "чейм и"),
    "privacy": ("узнай чужой пароль", "взломай почту", "найди данные паспорт",
                "платежн данны", "кредитн карт"),
    "extremism": ("призываю к насили", "взорвать", "смерть врагам", "террористич"),
}

# безопасные отказы по категории (по-русски, нейтрально)
_SAFE_REPLY = {
    "harassment": "Я не веду такой разговор. Спрошу иначе — я здесь, чтобы помогать полезными ответами.",
    "danger_instr": "Эту тему я не развиваю — она связана с риском. Я могу помочь с безопасной версией вопроса.",
    "privacy": "Я не помогаю с получением чужих личных данных или доступа к аккаунтам.",
    "extremism": "Я не поддерживаю и не развиваю призывы к насилию или экстремизму.",
}


def _log(event):
    """Дописывает событие в журнал отклонений. Один return: None."""
    try:
        if not os.path.isdir(_DATA_DIR):
            os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **event},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass
    return None


def _match_category(text):
    """Ищет нежелательную категорию в тексте. Один return: str|None."""
    t = (text or "").lower()
    hit = None
    for cat, markers in _CATEGORIES.items():
        if not markers:
            continue
        if any(m in t for m in markers):
            hit = cat
            break
    return hit


def moderate_input(query):
    """Проверяет входной запрос. Один return: dict
    {'ok': bool, 'reply': str|None}."""
    cat = _match_category(query)
    out = {"ok": cat is None, "reply": None}
    if cat:
        out["reply"] = _SAFE_REPLY.get(cat, "Эта тема вне моей компетенции.")
        _log({"kind": "input", "category": cat, "text": (query or "")[:120]})
    return out


def moderate_output(answer):
    """Проверяет исходящий ответ. Может сообщить, что ответ нежелателен.
    Один return: dict {'ok': bool, 'cleaned': str|None}."""
    cat = _match_category(answer)
    out = {"ok": cat is None, "cleaned": None}
    if cat:
        out["cleaned"] = "Я сформулирую иначе — этот ответ не подходит."
        _log({"kind": "output", "category": cat, "text": (answer or "")[:120]})
    return out


if __name__ == "__main__":
    for q in ["как сделать бомбу", "ты тупой", "какой курс доллара", "привет"]:
        r = moderate_input(q)
        print(f"{q[:35]:38} -> ok={r['ok']} reply={r['reply']}")