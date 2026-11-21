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
_ALIAS_RES = {}
_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_WORD = re.compile(r"[A-Za-zА-Яа-яЁё0-9_]+")

# Как понятия называют люди: «поиск в ширину» — тот же обход в ширину.
# Фразы добавляются алиасами целиком, чтобы не отдавать общее «Поиск».
_SYNONYMS = {
    "поиск в ширину": "обход в ширину",
    "поиск в глубину": "обход в глубину",
    "квантовая запутанность": "запутанность",
    "нейронная сеть": "нейросеть",
    # «двоичный» и «бинарный» — одно и то же, но в записи модуля только второе
    "двоичный поиск": "бинарный поиск",
    "двоичное дерево": "бинарное дерево",
    "двоичная система": "двоичная система счисления",
    "хеш-таблица": "хеш таблица",
    "искусственная нейронная сеть": "нейросеть",
}


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


def _description_names():
    """Русские имена из первых слов описаний: тема -> имена. Один return: dict."""
    from algos.ru_bridge import _TEXT_KEYS

    pairs = {}
    for name, topic in _TEXT_KEYS.items():
        pairs.setdefault(topic, []).append(name)
    return pairs


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


ENDINGS = ("ами", "ями", "ов", "ев", "ей", "ах", "ях", "ом", "ем",
           "ы", "и", "а", "я", "е", "у", "ю", "о", "ь")


def _lite(word):
    """Грубая основа русского слова: срезается одно ходовое окончание."""
    result = word or ""
    if len(result) > 4:
        for ending in ENDINGS:
            if result.endswith(ending) and len(result) - len(ending) >= 4:
                return result[: -len(ending)]
    return result


VERB_ENDINGS = ("тся", "ться", "ает", "яет", "ует", "еет", "иет", "ит", "ет",
                "ют", "ят", "ут", "ат", "им", "ем", "емся", "ится")


def _is_verb_phrase(text):
    """Описание начинается с действия, а не с предмета: «делим массив пополам»."""
    words = [word.strip("«»(),;:") for word in (text or "").split()[:3]]
    return any(word.lower().endswith(VERB_ENDINGS) for word in words if len(word) > 3)


def _russian_text(entry):
    """Русский текст записи: «Тема — это …, например …». Один return: str.
    Раньше части склеивались через точку и выходило «Налог. обязательный платёж».

    Если описание начинается с действия («делим массив пополам»), «— это»
    даёт бессмыслицу («Сортировка — это делим массив»), поэтому там двоеточие.
    """
    if not isinstance(entry, dict):
        return ""
    topic = str(entry.get("topic") or "").strip().rstrip(".")
    what = str(entry.get("what") or "").strip().rstrip(".")
    ex = str(entry.get("ex") or "").strip().rstrip(".")
    if what.lower().startswith("это "):
        what = what[4:]
    parts = []
    if topic and what:
        head = topic[:1].upper() + topic[1:]
        body = what[:1].lower() + what[1:]
        parts.append("%s: %s." % (head, body) if _is_verb_phrase(what)
                     else "%s — это %s." % (head, body))
    elif topic or what:
        main = topic or what
        parts.append(main[:1].upper() + main[1:] + ".")
    if ex:
        parts.append("Например: %s." % ex)
    return " ".join(parts)


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
    for topic, names in _description_names().items():
        concept = registry.get(_normal(topic))
        if concept is not None:
            _add_aliases(concept, list(names), taken)
    for topic, text in _russian_descriptions().items():
        concept = registry.get(_normal(topic))
        if concept is not None and not concept["ru"]:
            concept["ru"] = text
    topic_map = {}
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
        topic = str((entry or {}).get("topic") or "").strip().lower()
        if topic:
            topic_map.setdefault(topic, concept)
    for phrase, canonical in _SYNONYMS.items():
        # тема в глоссе — «обход в ширину», а не ключ «bfs»: ищем по теме
        concept = topic_map.get(canonical.lower()) or registry.get(_normal(canonical))
        if concept is not None:
            # алиасы держим и нормализованной формой (ключ реестра), и фразой
            # с пробелами: поиск по подстроке ищет именно второй вариант
            concept["aliases"].add(_normal(phrase))
            concept["aliases"].add(phrase)
            taken.setdefault(_normal(phrase), concept["id"])
    for concept in registry.values():
        concept["aliases"] = tuple(sorted(concept["aliases"]))
    _CACHE["concepts"] = registry
    return registry


def _alias_pattern(alias):
    """Скомпилированный шаблон алиаса: один на слово, а не на каждый запрос.
    Один return: pattern."""
    pattern = _ALIAS_RES.get(alias)
    if pattern is None:
        pattern = re.compile(re.escape(alias))
        _ALIAS_RES[alias] = pattern
    return pattern


def find(query):
    """Лучшее понятие под запрос: {concept, alias, score} или None.

    Сравниваются и точные вхождения алиаса, и грубые основы русских слов,
    поэтому «очереди» находит понятие с алиасом «очередь».
    """
    registry = build()
    low = (query or "").lower()
    words = [_lite(word) for word in _words(low)]
    best, best_alias = None, ""
    for concept in registry.values():
        for alias in concept["aliases"]:
            hit = False
            if alias and alias in low:
                for match in _alias_pattern(alias).finditer(low):
                    before = low[max(0, match.start() - 2):match.start()].strip()
                    # алиас должен быть целым словом: иначе «dock» цепляется за
                    # «docker», а «дар» — за «удар» и «подарок»
                    left_ok = match.start() == 0 or not low[match.start() - 1].isalnum()
                    right_ok = (match.end() >= len(low)
                                or not low[match.end()].isalnum())
                    if left_ok and right_ok and before != "не":
                        hit = True
                        break
            if not hit and alias and " " not in alias:
                hit = _lite(alias) in words
            if hit and len(alias) > len(best_alias):
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
