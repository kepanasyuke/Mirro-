# -*- coding: utf-8 -*-
"""Ответ на русский вопрос из единого реестра понятий.

Работает без внешних моделей: берёт русский текст понятия, если он есть;
если есть только английский — отвечает по-русски рамкой и помечает пробел.
Пробелы (у понятия нет русского описания) пишутся в `data/gap_queue.jsonl`,
чтобы русское имя появлялось из опыта повторных вопросов, а не из перевода.

Самостоятельность: ни одного вызова провайдера, только локальные базы.
"""
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
GAPS = os.path.join(ROOT, "data", "gap_queue.jsonl")
MIN_QUERY = 6
ENOUGH = 320


def _log_gap(query, concept):
    """Дописывает пробел в очередь; сбой записи не мешает ответу.

    Переменная окружения `NEURO_NO_GAP` отключает запись — так тесты не мусорят.
    """
    ok = False
    if not os.environ.get("NEURO_NO_GAP"):
        try:
            os.makedirs(os.path.dirname(GAPS), exist_ok=True)
            with open(GAPS, "a", encoding="utf-8") as handle:
                handle.write(json.dumps({"query": query.strip(), "concept": concept},
                                        ensure_ascii=False) + "\n")
            ok = True
        except OSError:
            ok = False
    return ok


def _first_sentence(text):
    """Первое предложение текста, обрезанное по длине."""
    cut = (text or "").strip().split(". ")
    first = cut[0] if cut else ""
    result = first if len(first) <= ENOUGH else first[:ENOUGH].rstrip() + "…"
    return result


def associations(concept_id):
    """Соседи понятия из графа определений (`algos/concept_graph.py`), если он есть."""
    result = ()
    try:
        from algos.concept_graph import neighbours
        result = tuple(neighbours(concept_id, depth=1)[:3])
    except Exception:
        result = ()
    return result


def russian_answer(concept, links=None):
    """Ответ по-русски: своё описание, иначе русская рамка вокруг английского.

    `links` — готовые связи из плана; если не переданы, берутся из графа напрямую.
    """
    result = concept.get("ru") or ""
    related = list(links) if links is not None else associations(concept.get("id") or concept.get("name") or "")
    if not result and concept.get("en"):
        from algos import compose
        result = compose.compose(concept, related, _first_sentence(concept["en"]))
    elif result and related:
        # в русскую рамку пускаем только русские связи: иначе ответ
        # заканчивается английскими темами («Связано с: trust, duty»)
        from algos import compose
        related_text = compose.related_text(related, limit=3)
        if related_text:
            result = result + " Связано с: " + related_text + "."
    return result[:1].upper() + result[1:] if result else result


def try_concept(query):
    """Ответ из реестра понятий или None, если понятие не найдено.

    Возвращает (ответ, понятие) через словарь, чтобы вызывающий видел источник.
    """
    from algos import lookup
    result = None
    if isinstance(query, str) and len(query.strip()) >= MIN_QUERY:
        found = lookup.find_with_learned(query)
        if found is not None:
            concept = found["concept"]
            text = russian_answer(concept)
            if text:
                result = {"answer": text, "concept": concept["name"],
                          "alias": found["alias"], "has_ru": bool(concept["ru"])}
                if not concept["ru"]:
                    _log_gap(query, concept["name"])
    return result


def answer(query):
    """Только текст ответа или None — удобно вставлять в конвейер."""
    found = try_concept(query)
    return found["answer"] if found else None


def _plan_operations(operation, arguments):
    """Операции плана: понятие по запросу и его связи из графа."""
    from algos import concepts
    from algos import lookup
    from algos.concept_graph import neighbours
    result = None
    if operation == "concept":
        query = arguments[0] if arguments else None
        found = lookup.find_with_learned(query) if isinstance(query, str) else None
        result = found["concept"] if found else None
    if operation == "neighbours":
        value = arguments[0] if arguments else None
        name = value.get("name") if isinstance(value, dict) else value
        result = list(neighbours(name, depth=1)[:3]) if isinstance(name, str) else []
    return result


def plan_steps(query):
    """План ответа: найти понятие, взять его связи, отрендерить текст."""
    return [("concept", "concept", [query]), ("links", "neighbours", ["=concept"])]


def try_plan(query):
    """Ответ, собранный планом и исполненный машиной; None, если понятия нет."""
    from algos import plan_machine
    result = None
    if isinstance(query, str) and len(query.strip()) >= MIN_QUERY:
        executed = plan_machine.run_plan(plan_steps(query), _plan_operations)
        concept = executed["values"].get("concept")
        if isinstance(concept, dict):
            links = [item for item in executed["values"].get("links") or () if isinstance(item, str)]
            text = russian_answer(concept, links)
            if text:
                result = {"answer": text, "concept": concept.get("name"), "alias": "",
                          "has_ru": bool(concept.get("ru")), "steps": executed["steps"]}
                if not concept.get("ru"):
                    _log_gap(query, concept.get("name") or "")
    return result


def answer_by_plan(query):
    """Только текст ответа, собранного планом на машине."""
    found = try_plan(query)
    return found["answer"] if found else None
