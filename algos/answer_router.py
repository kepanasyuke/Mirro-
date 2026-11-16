# -*- coding: utf-8 -*-
"""Ранжирование ответов по уверенности.

Сейчас в Mirro ответ выбирает порядок обработчиков: кто первый в списке,
тот и отвечает. Здесь наоборот — каждый источник предлагает ответ со
своей уверенностью, а выбирается лучший. Источники берутся только свои:
русское описание понятия (`ru_bridge`), связи понятий (`related`) и реестр
понятий (`concepts` + `neuro_answer`).

Уверенность объяснимая: база за найденную тему, надбавки за русский текст,
за упоминание самого понятия в ответе и за достаточную длину. Никаких
скрытых весов — всё в одном месте, чтобы можно было спорить с числами.

Запуск проверки:  python algos/answer_router.py "что такое память"
"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.ru_bridge import bridge, find_topic, related, ru_definition, _ru_label


def _has_russian(text):
    """Ответ по-русски. Один return: bool."""
    return any("\u0400" <= char <= "\u04ff" for char in text or "")


def _score_definition(query, found):
    """Уверенность ответа-определения. Один return: float."""
    topic = found.get("topic")
    text = found.get("content") or ""
    score = 0.55
    if ru_definition(topic):
        score += 0.25
    label = _ru_label(topic).lower()
    if label and label in text.lower():
        score += 0.10
    if len(text) >= 120:
        score += 0.05
    if not _has_russian(text):
        score -= 0.30
    return round(min(score, 0.99), 2)


def _score_relation(found):
    """Уверенность ответа про связи. Один return: float."""
    text = found.get("content") or ""
    score = 0.50
    if "—" in text and text.count("»:") >= 2:
        score += 0.10
    if len(text) >= 120:
        score += 0.05
    if not _has_russian(text):
        score -= 0.30
    return round(min(score, 0.99), 2)


_LINK_WORDS = ("связан", "связ", "отлича", "разниц", "общего", "похож", "сходств")


def _wants_links(query):
    """Спрашивают про связи, а не про определение. Один return: bool."""
    low = (query or "").lower()
    return any(word in low for word in _LINK_WORDS)


def candidates(query):
    """Все кандидаты на ответ с уверенностью. Один return: list."""
    found = []
    definition = bridge(query)
    if definition and definition.get("content"):
        found.append({"content": definition["content"], "source": "definition",
                      "confidence": _score_definition(query, definition),
                      "topic": definition.get("topic")})
    links = related(query)
    if links and links.get("content"):
        found.append({"content": links["content"], "source": "relations",
                      "confidence": _score_relation(links),
                      "topic": links.get("topic")})
    if _wants_links(query):
        for item in found:
            bonus = 0.25 if item["source"] == "relations" else -0.40
            item["confidence"] = round(min(0.99, max(0.0, item["confidence"] + bonus)), 2)
    found.sort(key=lambda item: (-item["confidence"], item["source"]))
    return found


def choose(query, threshold=0.45):
    """Лучший ответ или None, если всё ниже порога. Один return: dict/None."""
    found = candidates(query)
    best = found[0] if found else None
    return best if best and best["confidence"] >= threshold else None


def main(argv):
    """Проверка из командной строки. Один return: int."""
    query = " ".join(argv) or "что такое память"
    print("вопрос:", query, "| тема:", find_topic(query))
    for item in candidates(query):
        print("  %.2f  %-10s %s" % (item["confidence"], item["source"],
                                    item["content"][:90].replace("\n", " ")))
    best = choose(query)
    print("выбрано:", (best or {}).get("source"), (best or {}).get("confidence"))
    return 0 if best else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
