# -*- coding: utf-8 -*-
"""ru_eval.py — проверка маршрута «русский вопрос -> понятие -> ответ».

Меряет не красоту формулировки, а три вещи:
  * находит ли система нужное понятие;
  * даёт ли непустой ответ там, где он должен быть;
  * молчит ли там, где понятия нет (иначе это выдумка).

Запуск:
    python tools/ru_eval.py             # сводка
    python tools/ru_eval.py --verbose   # ещё и каждый вопрос
"""
import argparse
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)

from algos import concepts
from algos.neuro_answer import answer
from algos.ru_bridge import bridge
from tests.ru_eval_set import CASES


def resolve(query):
    """Тема по вопросу: сначала мост, затем реестр. Один return: str/None."""
    found = bridge(query)
    topic = (found or {}).get("topic")
    if topic is None:
        hit = concepts.find(query)
        topic = (hit or {}).get("concept", {}).get("name")
    return topic


def reply(query):
    """Непустой ответ по вопросу или None. Один return: str/None."""
    found = bridge(query)
    text = (found or {}).get("content") or answer(query)
    return text if text and text.strip() else None


def _is_russian(text):
    """Ответ по-русски (есть кириллица). Один return: bool."""
    return any("\u0400" <= char <= "\u04ff" for char in text or "")


def check(case):
    """Результат по одному вопросу. Один return: dict."""
    query, expected, must_answer = case
    topic = resolve(query)
    text = reply(query)
    right_topic = topic == expected if expected else topic is None
    has_text = bool(text) and _is_russian(text)
    ok = right_topic and (has_text if must_answer else not text or right_topic)
    return {"query": query, "expected": expected, "topic": topic,
            "answered": bool(text), "russian": _is_russian(text or ""), "ok": ok}


def main(argv):
    """Точка входа. Один return: int."""
    parser = argparse.ArgumentParser(description="Оценка русских вопросов")
    parser.add_argument("--verbose", action="store_true")
    args = parser.parse_args(argv)

    results = [check(case) for case in CASES]
    passed = sum(1 for item in results if item["ok"])
    asked = [item for item in results if item["expected"]]
    answered = [item for item in asked if item["answered"]]
    negative = [item for item in results if not item["expected"]]
    silent = [item for item in negative if not item["answered"]]

    print("вопросов:            %d" % len(results))
    print("прошли:              %d (%.0f%%)" % (passed, 100.0 * passed / len(results)))
    print("с ожидаемой темой:   %d, из них с ответом %d" % (len(asked), len(answered)))
    print("без ожидаемой темы:  %d, из них молчат %d" % (len(negative), len(silent)))

    wrong = [item for item in results if not item["ok"]]
    if wrong:
        print("\nпровалы:")
        for item in wrong:
            print("  %-45s ожидалось %-14s найдено %-14s ответ=%s"
                  % (item["query"], item["expected"], item["topic"],
                     "да" if item["answered"] else "нет"))
    if args.verbose:
        print("\nвсе вопросы:")
        for item in results:
            print("  %-45s %-14s %s" % (item["query"], item["topic"],
                                        "OK" if item["ok"] else "провал"))
    return 0 if passed == len(results) else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
