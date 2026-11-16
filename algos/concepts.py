# -*- coding: utf-8 -*-
"""Единый реестр понятий: русская и английская базы как один индекс.

Русский текст берётся из `algos/module_knowledge.py` (`_KNOWLEDGE`),
английский — из `algos/english_kb.py` (`_EN_KB` и `_TOPIC_TEST`).
Модуль только читает обе базы и ничего не меняет: это индекс
«алиас -> понятие», поверх которого можно строить маршрутизацию по языку ответа.

Никаких внешних провайдеров и перевода здесь нет: понятие знает ровно те
формулировки, что уже лежат в проекте. Если у понятия нет русского текста,
это видно по полю `ru`: значит, формулировку ещё предстоит написать.
"""
import io
import json
import os
import re

_CACHE = {}
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORD = re.compile(r"[A-Za-zА-Яа-яЁё0-9_]+")


def _english():
    """Английская база: (словарь текстов, список триггеров)."""
    from algos import english_kb
    texts = english_kb._EN_KB if isinstance(english_kb._EN_KB, dict) else {}
    tests = english_kb._TOPIC_TEST if isinstance(english_kb._TOPIC_TEST, (list, tuple)) else []
    return texts, tests


def _russian():
    """Русская база: словарь записей _KNOWLEDGE."""
    from algos import module_knowledge
    return module_knowledge._KNOWLEDGE if isinstance(module_knowledge._KNOWLEDGE, dict) else {}


def _stem(word):
    """Русская основа слова (грубый стеммер проекта)."""
    from algos.module_knowledge import _stem_ru
    return _stem_ru(word)


def _bridged_aliases():
    """Русские ключи понятий из ru_bridge: тема английской базы -> слова."""
    from algos.ru_bridge import RU_KEYS
    return RU_KEYS.items()


def _russian_descriptions():
    """Русские описания из algos/ru_descriptions.py: тема -> текст."""
    from algos.ru_descriptions import RU_TEXT
    return RU_TEXT


def _wikidata_pairs():
    """Пары «тема → русское слово» из data/bilingual_map.json. Один return: dict.

    Карта собирается внешним скриптом по интервики Википедии и Викиданным,
    поэтому пары фильтруются: берём только кириллические подписи без служебных
    пометок вроде «(значения)». Ошибиться такая пара всё равно может
    («graph» → «граффити»), поэтому ручные ключи ru_bridge важнее — они
    добавляются первыми и в реестре остаются наравне.
    """
    pairs = {}
    path = os.path.join(_ROOT, "data", "bilingual_map.json")
    try:
        with io.open(path, encoding="utf-8") as handle:
            raw = json.load(handle)
        for topic, label in (raw.get("map") or {}).items():
            clean = str(label or "").strip()
            cyrillic = any("\u0400" <= char <= "\u04ff" for char in clean)
            usable = (len(clean) >= 3 and cyrillic and "(" not in clean
                      and clean.lower() != str(topic or "").lower())
            if usable:
                pairs[str(topic)] = (clean,)
    except (OSError, ValueError):
        pairs = {}
    return pairs


def _words(text):
    """Слова строки в нижнем регистре."""
    return [item.lower() for item in _WORD.findall(text or "")]


def _normal(name):
    """Нормализованное имя понятия: нижний регистр, подчёркивания как пробелы."""
    return " ".join(_words((name or "").replace("_", " ")))


def _russian_text(entry):
    """Русский текст записи: тема, что делает, пример — без пустых частей."""
    if not isinstance(entry, dict):
        return ""
    parts = [entry.get("topic") or "", entry.get("what") or "", entry.get("ex") or ""]
    return ". ".join(part.strip().rstrip(".") for part in parts if str(part).strip())


def _new(name):
    """Пустое понятие с заданным именем."""
    return {"id": _normal(name), "name": name, "ru": "", "en": "",
            "aliases": set(), "module": ""}


def _add_aliases(concept, values, taken=None):
    """Дописывает алиасы: короткие и уже занятые другими понятиями не берём."""
    for value in values:
        for word in _words(value):
            owner = taken.get(word) if taken is not None else None
            usable = len(word) >= 4 and owner in (None, concept["id"])
            if usable:
                concept["aliases"].add(word)
                if taken is not None:
                    taken[word] = concept["id"]
    return taken


def build():
    """Реестр понятий: один словарь на весь проект, собирается один раз."""
    if "concepts" in _CACHE:
        return _CACHE["concepts"]
    texts, tests = _english()
    registry = {}
    for name, text in texts.items():
        concept = _new(name)
        concept["en"] = text if isinstance(text, str) else ""
        concept["aliases"].add(_normal(name))
        registry[concept["id"]] = concept
    for topic, keys in tests:
        concept = registry.get(_normal(topic))
        if concept is not None:
            _add_aliases(concept, [topic] + list(keys or ()))
    taken = {}
    for concept in registry.values():
        for alias in concept["aliases"]:
            taken.setdefault(alias, concept["id"])
    for topic, keys in _bridged_aliases():
        concept = registry.get(_normal(topic))
        if concept is not None:
            _add_aliases(concept, list(keys), taken)
    for topic, keys in _wikidata_pairs().items():
        concept = registry.get(_normal(topic))
        if concept is not None:
            _add_aliases(concept, list(keys), taken)
    for topic, text in _russian_descriptions().items():
        concept = registry.get(_normal(topic))
        if concept is not None and not concept["ru"]:
            concept["ru"] = text
    for name, entry in _russian().items():
        key = _normal(name)
        concept = registry.get(key)
        if concept is None:
            concept = _new(name)
            concept["aliases"].add(key)
            registry[key] = concept
        concept["ru"] = _russian_text(entry)
        concept["module"] = str((entry or {}).get("module") or "")
        _add_aliases(concept, [name, (entry or {}).get("topic") or ""])
        for word in _words((entry or {}).get("topic") or ""):
            stem = _stem(word)
            if len(stem) >= 4:
                concept["aliases"].add(stem)
    for concept in registry.values():
        concept["aliases"] = tuple(sorted(concept["aliases"]))
    _CACHE["concepts"] = registry
    return registry


def find(query):
    """Лучшее понятие под запрос: {concept, alias, score} или None."""
    registry = build()
    low = (query or "").lower()
    best, best_alias = None, ""
    for concept in registry.values():
        for alias in concept["aliases"]:
            if alias and alias in low and len(alias) > len(best_alias):
                best, best_alias = concept, alias
    if best is None:
        return None
    score = len(best_alias) / max(len(low), 1)
    return {"concept": best, "alias": best_alias, "score": round(score, 3)}


def stats():
    """Счётчики реестра: сколько понятий и сколько из них с русским текстом."""
    registry = build()
    total = len(registry)
    with_ru = sum(1 for concept in registry.values() if concept["ru"])
    with_en = sum(1 for concept in registry.values() if concept["en"])
    return {"concepts": total, "with_ru": with_ru, "with_en": with_en,
            "ru_only": total - with_en, "en_only": total - with_ru}
