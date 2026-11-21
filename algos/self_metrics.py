# -*- coding: utf-8 -*-
"""Самометрика: что система знает о себе и как это меняется.

Считает покрытие базы (сколько понятий с русским текстом, сколько с причинами),
размер очереди пробелов, число выученных имён и распределение типов вопросов.
Раз в N обращений пишет строку в `data/metrics.jsonl`, чтобы прогресс был виден
не на словах, а числами.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
METRICS = os.path.join(ROOT, "data", "metrics.jsonl")
SAMPLE = ("что такое стек", "как работает mean", "чем отличается стек от очереди",
          "почему луна", "с чем связана музыка", "what is music?")


def coverage():
    """Покрытие базы: понятия, языки, причины, очередь, выученные имена."""
    from algos import causality, concepts, label_learning
    stats = concepts.stats()
    gaps = len(label_learning.gap_entries())
    learned = len(label_learning.learned())
    result = {"concepts": stats["concepts"], "with_ru": stats["with_ru"],
              "with_en": stats["with_en"], "en_only": stats["en_only"],
              "causes": len(causality.index()), "gaps": gaps, "learned": learned,
              "ru_share": round(stats["with_ru"] / max(stats["concepts"], 1), 3)}
    return result


def intents(questions=None):
    """Сколько вопросов какого типа распознаётся."""
    from algos.plan_router import classify
    result = {}
    for question in (questions if questions is not None else SAMPLE):
        intent = classify(question)
        result[intent] = result.get(intent, 0) + 1
    return result


def answered(questions=None):
    """Сколько из контрольных вопросов получают ответ и каким путём."""
    from algos.plan_router import answer as plan_answer
    rows = []
    for question in (questions if questions is not None else SAMPLE):
        found = plan_answer(question)
        rows.append({"question": question,
                     "intent": found["intent"] if found else "unknown",
                     "steps": found["steps"] if found else 0,
                     "answered": bool(found)})
    return rows


def summary():
    """Полный снимок: покрытие, типы вопросов, контрольные ответы."""
    rows = answered()
    result = {"coverage": coverage(), "intents": intents(),
              "answered": sum(1 for row in rows if row["answered"]),
              "total": len(rows), "rows": rows}
    return result


def write(path=None, snapshot=None):
    """Дописывает снимок в metrics.jsonl; возвращает записанную строку."""
    destination = path or METRICS
    data = snapshot if snapshot is not None else summary()
    os.makedirs(os.path.dirname(destination), exist_ok=True)
    line = json.dumps(data, ensure_ascii=False, sort_keys=True)
    with open(destination, "a", encoding="utf-8") as handle:
        handle.write(line + "\n")
    return line


def missing_russian(limit=40):
    """Понятия с русским именем, но без русского текста: что стоит написать.

    Сортировка — по числу связей: чем больше соседей, тем заметнее понятие в ответах.
    """
    from algos import compose, concepts
    registry = concepts.build()
    rows = []
    for concept in registry.values():
        title = compose.russian_title(concept)
        has_russian_name = compose._is_russian(title)
        if has_russian_name and not concept.get("ru") and concept.get("en"):
            rows.append({"name": concept["name"], "title": title,
                         "aliases": len(concept.get("aliases") or ()),
                         "english": (concept["en"] or "")[:120]})
    rows.sort(key=lambda row: (-row["aliases"], row["name"]))
    return rows[:limit] if limit else rows


def history(path=None, limit=10):
    """Последние снимки из файла метрик."""
    destination = path or METRICS
    result = []
    if os.path.exists(destination):
        with open(destination, encoding="utf-8", errors="replace") as handle:
            lines = [line for line in handle if line.strip()]
        result = [json.loads(line) for line in lines[-limit:]]
    return result
