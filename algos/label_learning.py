# -*- coding: utf-8 -*-
"""Русские имена понятий из опыта: связь «слово ↔ понятие» по совместной встречаемости.

Мирро не переводит, а запоминает: если русский вопрос не нашёлся, `neuro_answer`
пишет его в `data/gap_queue.jsonl` вместе с понятием, которое в итоге ответило.
Когда одно и то же слово несколько раз приходит к одному понятию, связь
принимается по взаимной информации (PMI), а не по совпадению строки.

Принятые пары лежат в `data/learned_aliases.jsonl` — отдельно от источника правды
`algos/english_kb.py`, поэтому реестр понятий не портится.
"""
import json
import os

from algos import concepts
from algos.information import pmi

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAPS = os.path.join(ROOT, "data", "gap_queue.jsonl")
LEARNED = os.path.join(ROOT, "data", "learned_aliases.jsonl")
MIN_COUNT = 3
MIN_PMI = 1.0

STOPWORDS = frozenset((
    "что", "как", "кака", "какой", "какие", "чем", "кто", "где", "когда", "зачем",
    "почему", "сколько", "такое", "такой", "означает", "значит", "определение",
    "напиши", "покажи", "расскажи", "объясни", "сделай", "функцию", "функция",
    "работает", "работают", "устроен", "устроена", "это", "этот", "для", "про",
    "мне", "нам", "тебе", "если", "чтобы", "можно", "нельзя", "есть", "быть",
    "важно", "важный", "вообще", "просто", "самое", "самый", "очень", "нужно",
    "what", "does", "tell", "about", "the", "and", "with",
))


def read_lines(path):
    """Записи JSONL; отсутствие файла даёт пустой список."""
    result = []
    if os.path.exists(path):
        with open(path, encoding="utf-8", errors="replace") as handle:
            for line in handle:
                line = line.strip()
                if line:
                    try:
                        result.append(json.loads(line))
                    except ValueError:
                        result.append({})
    return result


def gap_entries(path=None):
    """Пары «запрос ↔ понятие» из очереди пробелов."""
    result = [item for item in read_lines(path or GAPS)
              if isinstance(item, dict) and item.get("query") and item.get("concept")]
    return result


def _words(query):
    """Значимые русские слова запроса: основа от 4 символов, без служебных слов."""
    result = []
    for word in concepts._words(query):
        lite = concepts._lite(word)
        is_russian = bool(lite) and "\u0400" <= lite[0] <= "\u04FF"
        if len(lite) >= 4 and is_russian and word not in STOPWORDS and lite not in STOPWORDS:
            result.append(lite)
    return result


def candidates(entries=None):
    """Пары «слово → понятие» со счётчиками и PMI, отсортированные по PMI."""
    rows = entries if entries is not None else gap_entries()
    total = len(rows)
    pairs = {}
    words = {}
    targets = {}
    for row in rows:
        concept = row.get("concept")
        targets[concept] = targets.get(concept, 0) + 1
        for word in _words(row.get("query") or ""):
            words[word] = words.get(word, 0) + 1
            key = (word, concept)
            pairs[key] = pairs.get(key, 0) + 1
    result = [{"word": word, "concept": concept, "count": count,
               "pmi": round(pmi(count, words.get(word, 0), targets.get(concept, 0), total), 3)}
              for (word, concept), count in pairs.items()]
    result.sort(key=lambda item: (-item["pmi"], -item["count"], item["word"]))
    return result


def accepted(rows=None, min_count=MIN_COUNT, min_pmi=MIN_PMI):
    """Пары, которые можно принять: достаточно повторов и высокий PMI."""
    result = [item for item in (rows if rows is not None else candidates())
              if item["count"] >= min_count and item["pmi"] >= min_pmi]
    return result


def write_accepted(rows, path=None):
    """Дописывает принятые пары в файл выученных алиасов, без повторов."""
    destination = path or LEARNED
    known = {(item.get("word"), item.get("concept")) for item in read_lines(destination)}
    added = 0
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    with open(destination, "a", encoding="utf-8") as handle:
        for item in rows or ():
            key = (item["word"], item["concept"])
            if key not in known:
                handle.write(json.dumps({"word": item["word"], "concept": item["concept"],
                                         "count": item["count"], "pmi": item["pmi"]},
                                        ensure_ascii=False) + "\n")
                known.add(key)
                added += 1
    return added


def learned(path=None):
    """Словарь «основа слова -> понятие» из файла выученных пар."""
    result = {item.get("word"): item.get("concept")
              for item in read_lines(path or LEARNED) if item.get("word")}
    return result


def guess(query, path=None):
    """Понятие по выученному слову: имя понятия или None."""
    table = learned(path)
    result = None
    for word in _words(query or ""):
        if word in table and result is None:
            result = table[word]
    return result


def learn(path=None, aliases_path=None, min_count=MIN_COUNT, min_pmi=MIN_PMI):
    """Полный проход: очередь пробелов -> принятые пары -> файл."""
    rows = accepted(candidates(gap_entries(path)), min_count=min_count, min_pmi=min_pmi)
    return {"candidates": len(candidates(gap_entries(path))), "accepted": len(rows),
            "added": write_accepted(rows, aliases_path)}
