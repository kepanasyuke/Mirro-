# -*- coding: utf-8 -*-
"""Мост между русским вопросом и английской базой знаний Mirro.

Английская база (`algos/english_kb.py`, 2241 тема) знает понятия, но отвечает
только на английские вопросы: вход закрыт проверкой `_is_english_query`.
При этом многие понятия вошли в русский язык как заимствования
(`algorithm` → «алгоритм», `graph` → «граф»), поэтому их можно связать
без словаря и без внешних вызовов.

Как это работает:
1. латинская тема переводится в русскую запись простыми правилами;
2. русское слово из вопроса ищется среди таких записей;
3. найденное понятие объясняется по-русски из знаниевого графа.

Если граф понятия не знает — возвращается None, и отвечает другой обработчик:
лучше честное «не знаю», чем английский текст в ответ на русский вопрос.
"""
import re as _re

from algos.english_kb import _EN_KB

# Диграфы обрабатываются до отдельных букв, иначе «sh» станет «сх»
_PAIRS = (("sh", "ш"), ("ch", "ч"), ("th", "т"), ("ph", "ф"),
          ("ya", "я"), ("yu", "ю"), ("kh", "х"), ("zh", "ж"))

_LETTERS = {"a": "а", "b": "б", "c": "к", "d": "д", "e": "е", "f": "ф",
            "g": "г", "h": "х", "i": "и", "j": "дж", "k": "к", "l": "л",
            "m": "м", "n": "н", "o": "о", "p": "п", "q": "к", "r": "р",
            "s": "с", "t": "т", "u": "у", "v": "в", "w": "в", "x": "кс",
            "y": "и", "z": "з"}

_LATIN = _re.compile(r"[a-zA-Z]")
_ALIASES = None


def transliterate(word):
    """Русская запись латинского слова по простым правилам. Один return: str."""
    text = (word or "").lower()
    for src, dst in _PAIRS:
        text = text.replace(src, dst)
    return "".join(_LETTERS.get(ch, ch) for ch in text)


def build_aliases():
    """Карта «русская запись → английская тема» для заимствованных понятий.
    Один return: dict."""
    aliases = {}
    for topic in _EN_KB:
        if not isinstance(topic, str):
            continue
        ru = transliterate(topic)
        if ru and ru != topic and ru not in aliases:
            aliases[ru] = topic
    return aliases


def aliases():
    """Ленивая карта алиасов (строится один раз). Один return: dict."""
    global _ALIASES
    if _ALIASES is None:
        _ALIASES = build_aliases()
    return _ALIASES


def find_concept(query):
    """Английская тема, на которую указывает русское слово в запросе.
    Один return: str или None."""
    words = _re.findall(r"[а-яё]{3,}", (query or "").lower())
    found = [(len(word), aliases().get(word)) for word in words if aliases().get(word)]
    found.sort(reverse=True)
    return found[0][1] if found else None


def _explain_first(kg, names):
    """Первое непустое объяснение из списка имён. Один return: str или None."""
    texts = [kg.explain(name) for name in names if name]
    found = [text for text in texts if text]
    return found[0] if found else None


def try_bilingual(query):
    """Русский вопрос о заимствованном понятии → объяснение по-русски из графа.
    Один return: str или None (не наш случай — отвечают другие обработчики)."""
    ans = None
    text = (query or "").strip()
    is_russian = bool(text) and not _LATIN.search(text)
    if is_russian:
        topic = find_concept(text)
        if topic:
            from algos.knowledge_graph import kg
            ans = _explain_first(kg, (transliterate(topic), topic))
    return ans
