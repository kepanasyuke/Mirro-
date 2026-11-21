# -*- coding: utf-8 -*-
"""Показать, как Мирро пришёл к ответу.

Запуск:
    python tools/explain.py "почему луна"
    python tools/explain.py "чем отличается стек от очереди"
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from algos import explain


def main():
    """Печатает разбор для вопросов из аргументов."""
    questions = sys.argv[1:] or ["что такое стек", "почему луна"]
    for question in questions:
        text = explain.as_text(question)
        print(text if text else "не разобрано: " + question)
        print()
    return 0


if __name__ == "__main__":
    sys.exit(main())
