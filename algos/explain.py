# -*- coding: utf-8 -*-
"""Ход мысли: как именно получен ответ.

Ответ без объяснения проверить нельзя. Здесь для любого вопроса собирается
отчёт: какой тип распознан, по какому слову найдено понятие, откуда взят текст,
какие шаги исполнила машина и что она вызвала на каждом шаге.

Ничего не меняет и ничего не решает заново — только повторяет тот же путь,
что и обычный ответ, и показывает его.
"""
from algos import compose, lookup, plan, plan_machine, plan_router


def _source(concept, intent=""):
    """Откуда взят текст ответа: русский, английский или причина."""
    if not isinstance(concept, dict):
        return "нет"
    if intent == "why":
        from algos import causality
        pieces = causality.for_concept(concept, limit=2)
        languages = {language for language, _ in pieces}
        if "ru" in languages:
            return "причина по-русски"
        if "en" in languages:
            return "причина только по-английски"
        return "причин нет"
    if concept.get("ru"):
        return "русский текст"
    if concept.get("en"):
        return "английский текст"
    return "нет"


def explain(query):
    """Отчёт о пути к ответу: словарь с полями или None, если вопрос не разобран."""
    if not isinstance(query, str) or not query.strip():
        return None
    intent = plan_router.classify(query)
    found = lookup.find_with_learned(query)
    result = None
    if intent != "unknown" and found is not None:
        concept = found["concept"]
        steps = plan_router.plan_for(intent, query)
        executed = plan_machine.run_plan(steps, plan_router.dispatch)
        answer = plan_router.render(intent, executed["values"])
        result = {"query": query, "intent": intent, "via": found.get("via"),
                  "alias": found.get("alias"), "concept": concept.get("name"),
                  "title": compose.russian_title(concept),
                  "source": _source(concept, intent), "steps": executed["steps"],
                  "program": plan_machine.compile_plan(steps)[0],
                  "lines": plan.explain(steps),
                  "answer": answer, "machine_error": executed["error"]}
    return result


def as_text(query):
    """Отчёт в читаемом виде; None, если разобрать не удалось."""
    data = explain(query)
    result = None
    if data is not None:
        lines = ["Вопрос: %s" % data["query"],
                 "Тип: %s (поиск: %s, слово «%s»)" % (data["intent"], data["via"], data["alias"]),
                 "Понятие: %s (%s)" % (data["title"], data["concept"]),
                 "Источник текста: %s" % data["source"],
                 "Шагов машины: %d" % data["steps"],
                 "План:"]
        lines.extend("  " + line for line in data["lines"])
        lines.append("Ответ: %s" % (data["answer"] or "нет"))
        result = "\n".join(lines)
    return result
