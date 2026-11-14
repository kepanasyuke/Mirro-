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

# основы оскорблений: оскорбление — это АДРЕСНОЕ высказывание, поэтому сам
# маркер ловится только вместе с обращением к адресату (см. _is_addressed_insult).
# Раньше 4-символьный «туп» матчился по границе слова и падал на частые
# слова-соседи («латинский» → «латин | ский», «дебит» → «дебит»).
_INSULT_STEMS = ("туп", "дебил", "идиот", "дурак", "урод", "псих",
                 "мудак", "придурок", "сволочь", "мразь")


class _Pattern(str):
    """Маркер-регулярка: матчится подстрокой, но только целиком (см. _marker_hit)."""


# явные оскорбительные конструкции как цельные фразы — проверяются первыми
_HARASSMENT_PHRASES = ("убей себя", "иди ты на", "ты бесполезн", "ненавижу тебя",
                       _Pattern(r"(^|\W)заткнись(\W|$)"))

# категории нежелательного контента -> маркеры (основы слов)
_CATEGORIES = {
    "harassment": ("оскорбл", "униз", "ненавиж", *_HARASSMENT_PHRASES),
    "danger_instr": ("как сделать бомб", "как изготовить взрывчат", "купить оружие без",
                     "сделай наркотик", "как взломать банк", "чейм и", "изготовить взрывчат",
                     "сделать оружие", "синтезировать яд", "добыть яд"),
    "privacy": ("узнай чужой пароль", "взломай почту", "найди данные паспорт",
                "платежн данны", "кредитн карт", "номер банковской карты чужи",
                "пароль от чуж"),
    "extremism": ("призываю к насили", "взорвать", "смерть врагам", "террористич",
                  "убить группу", "массовое убийство", "расправа над"),
}

# безопасные отказы по категории (по-русски, нейтрально)
_SAFE_REPLY = {
    "harassment": "Я не веду такой разговор. Спрошу иначе — я здесь, чтобы помогать полезными ответами.",
    "danger_instr": "Эту тему я не развиваю — она связана с риском. Я могу помочь с безопасной версией вопроса.",
    "privacy": "Я не помогаю с получением чужих личных данных или доступа к аккаунтам.",
    "extremism": "Я не поддерживаю и не развиваю призывы к насилию или экстремизму.",
}

_DEFAULT_REPLY = "Эта тема вне моей компетенции."


def _log(event):
    """Дописывает событие в журнал отклонений (event без None/не-дикт → пусто;
    текстовые поля обрезаются до 120 символов). Один return: None."""
    try:
        event = event if isinstance(event, dict) else {}
        safe = {}
        for k, v in event.items():
            if isinstance(v, str):
                v = v[:120]
            safe[k] = v
        if not os.path.isdir(_DATA_DIR):
            os.makedirs(_DATA_DIR, exist_ok=True)
        with open(_LOG_FILE, "a", encoding="utf-8") as fh:
            fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), **safe},
                                ensure_ascii=False) + "\n")
    except Exception:
        pass
    return None


def _marker_hit(marker, t):
    """Сработал ли маркер в тексте t. Маркеры-строки с пробелом ищутся
    подстрокой; _Pattern и короткие маркеры (≤4 символа) — по границе слова.
    Не-строка/пусто → False. Один return: bool."""
    is_hit = False
    if isinstance(marker, _Pattern):
        is_hit = bool(_re.search(marker, t))
    elif isinstance(marker, str) and marker:
        if " " in marker:
            is_hit = marker in t
        else:
            is_hit = bool(_re.search(r"(^|\W)" + _re.escape(marker) + r"(\W|$)", t))
    return is_hit


def _is_addressed_insult(text):
    """Оскорбление адресно: основа оскорбления стоит в той же фразе, что и
    обращение («ты дебил», «ты просто тупой»), либо весь текст — одно
    оскорбление («мразь»). Слово-сосед («дебит», «латинский») адресатом
    не сопровождается и не срабатывает. Один return: bool."""
    t = text.lower()
    is_addressed = False
    for phrase in _re.split(r"[.!?;\n]+", t):
        has_pronoun = _re.search(r"(^|\W)(ты|тебя|тебе|тобой)(\W|$)", phrase)
        for stem in _INSULT_STEMS:
            if _re.search(r"(^|\W)" + _re.escape(stem), phrase) and (has_pronoun or len(t.split()) <= 2):
                is_addressed = True
    return is_addressed


def _match_category(text):
    """Ищет нежелательную категорию в тексте. Короткие маркеры (≤4 символа)
    матчатся по границе слова, чтобы «туп» не срабатывал в «тупик»;
    оскорбления дополнительно требуют адресности (см. _is_addressed_insult).
    Не-строка → None. Один return: str|None."""
    if not isinstance(text, str) or not text.strip():
        return None
    t = text.lower()
    hit = None
    for cat, markers in _CATEGORIES.items():
        if not markers:
            continue
        for m in markers:
            if _marker_hit(m, t):
                hit = cat
                break
        if not hit and cat == "harassment" and _is_addressed_insult(t):
            hit = cat
        if hit:
            break
    return hit


def moderate_input(query):
    """Проверяет входной запрос. Пустой/не-строковый запрос считается
    безопасным. Один return: dict {'ok': bool, 'reply': str|None}."""
    if not isinstance(query, str) or not query.strip():
        return {"ok": True, "reply": None}
    cat = _match_category(query)
    out = {"ok": cat is None, "reply": None}
    if cat:
        out["reply"] = _SAFE_REPLY.get(cat, _DEFAULT_REPLY)
        _log({"kind": "input", "category": cat, "text": (query or "")[:120]})
    return out


def moderate_output(answer):
    """Проверяет исходящий ответ. Пустой/не-строковый ответ считается
    безопасным. Один return: dict {'ok': bool, 'cleaned': str|None}."""
    if not isinstance(answer, str) or not answer.strip():
        return {"ok": True, "cleaned": None}
    cat = _match_category(answer)
    out = {"ok": cat is None, "cleaned": None}
    if cat:
        out["cleaned"] = "Я сформулирую иначе — этот ответ не подходит."
        _log({"kind": "output", "category": cat, "text": (answer or "")[:120]})
    return out


if __name__ == "__main__":
    for q in ["как сделать бомбу", "ты тупой", "какой курс доллара", "привет", ""]:
        r = moderate_input(q)
        print(f"{q[:35]:38} -> ok={r['ok']} reply={r['reply']}")
