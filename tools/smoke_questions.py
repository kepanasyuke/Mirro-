# -*- coding: utf-8 -*-
"""Дымовой прогон живого конвейера: вопросы, на которые Мирро обязан ответить.

Проверяет не «нет исключения», а что вопрос попал к тому, кто умеет на него
отвечать: определение — определением, сравнение — сравнением, подсчёт —
подсчётом. Ловит тихую деградацию: когда из-за сломанного импорта или
сдвинутой ветки конвейер скатывается в общий ответ на любое слово.

Запуск:  python tools/smoke_questions.py
Код возврата 1, если хоть один вопрос отвечен не тем путём.
"""
import os
import sys

_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if _ROOT not in sys.path:
    sys.path.insert(0, _ROOT)

CASES = (
    ("что такое стек", ("definition", "concept", "router")),
    ("что такое граф", ("definition", "concept", "router")),
    ("что такое музыка", ("definition", "concept", "router")),
    ("как работает стек", ("definition", "concept", "router")),
    ("чем отличается стек от очереди", ("concept_special",)),
    ("чем отличается список от массива", ("concept_special",)),
    ("с чем связана музыка", ("concept_special",)),
    ("какие связи у массива", ("concept_special",)),
    ("какие связи у графа", ("concept_special",)),
    ("почему небо синее", ("concept_special",)),
    ("сколько связей у графа", ("concept_special",)),
    ("сколько всего понятий", ("concept_special",)),
    ("сколько тем про математику", ("concept_special",)),
    ("какие связи у бинарного поиска", ("concept_special",)),
    ("что такое двоичный поиск", ("definition", "concept", "router")),
    ("что такое хеш таблица", ("definition", "concept", "router")),
    ("какие связи у сна", ("concept_special",)),
    ("what is entropy?", ("concept",)),
    ("what is plover?", ("concept",)),
    ("what is quark?", ("english",)),
    ("привет", ("greeting",)),
    ("hello!", ("greeting",)),
)

# Ответы, которые означают «конвейер не понял вопрос»: общая заглушка или
# рассуждение о словах вместо ответа по существу.
BAD_STARTS = ("Тройственное рассуждение", "I understood your question")


def check(question, expected):
    """Стратегия ответа и текст; пустая стратегия — провал."""
    from core.mirro_core import _try_direct_handlers

    found = _try_direct_handlers(question) or {}
    strategy = found.get("strategy") or ""
    content = (found.get("content") or "").strip()
    stub = content.startswith(BAD_STARTS)
    # «I'm mainly trained on Russian» — законный отказ на английское слово,
    # которого в базе нет; для остальных веток это заглушка вместо ответа
    ok = strategy in expected and (not stub or strategy == "english")
    return ok, strategy, content


def main():
    """Прогон по списку вопросов. Один return: int."""
    failures = 0
    for question, expected in CASES:
        ok, strategy, content = check(question, expected)
        mark = "ok  " if ok else "FAIL"
        if not ok:
            failures += 1
        print("%s %-36s %-16s %s" % (mark, question, strategy or "-",
                                     content[:60].replace("\n", " ")))
    print("\nитог: провалов %s из %s" % (failures, len(CASES)))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
