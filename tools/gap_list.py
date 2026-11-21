# -*- coding: utf-8 -*-
"""Список понятий, которым нужен русский текст: имя есть, описания нет.

Печатает markdown-таблицу: русское имя, английское начало описания, число связей.
По ней видно, что писать, а не «надо бы пополнить базу».

Запуск:
    python tools/gap_list.py
    python tools/gap_list.py --limit 100 > gaps.md
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from algos import self_metrics


def main():
    """Печатает таблицу и короткую сводку."""
    limit = 40
    args = sys.argv[1:]
    if "--limit" in args:
        index = args.index("--limit")
        if index + 1 < len(args) and args[index + 1].isdigit():
            limit = int(args[index + 1])
    rows = self_metrics.missing_russian(limit)
    total = len(self_metrics.missing_russian(0))
    print("# Понятия без русского текста")
    print()
    print("всего таких: %d, показано: %d" % (total, len(rows)))
    print()
    print("| русское имя | английское описание | связей |")
    print("|---|---|---|")
    for row in rows:
        print("| %s | %s | %d |" % (row["title"], row["english"].replace("|", "/"), row["aliases"]))
    return 0


if __name__ == "__main__":
    sys.exit(main())
