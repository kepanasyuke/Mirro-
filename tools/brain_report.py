# -*- coding: utf-8 -*-
"""Отчёт о состоянии Мирро: что знает, сколько отвечает, где пробелы.

Печатает короткую сводку по базе понятий, покрытию русского текста, причинам,
очереди пробелов и контрольным вопросам. Только читает (кроме `--save`,
который дописывает строку в data/metrics.jsonl).

Запуск:
    python tools/brain_report.py
    python tools/brain_report.py --save
"""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)

from algos import self_metrics


def _percent(part, total):
    """Доля в процентах с одним знаком."""
    return "%.1f%%" % (100.0 * part / total) if total else "0%"


def report(snapshot):
    """Текст отчёта по снимку."""
    cover = snapshot["coverage"]
    lines = ["# Мирро: состояние",
             "",
             "Понятий: %d" % cover["concepts"],
             "  с русским текстом: %d (%s)" % (cover["with_ru"], _percent(cover["with_ru"], cover["concepts"])),
             "  только по-английски: %d" % cover["en_only"],
             "  с причинными связями: %d" % cover["causes"],
             "Очередь пробелов: %d" % cover["gaps"],
             "Выучено имён из опыта: %d" % cover["learned"],
             "",
             "Типы вопросов: " + ", ".join("%s=%d" % item for item in sorted(snapshot["intents"].items())),
             "Контрольные вопросы: %d из %d получили ответ" % (snapshot["answered"], snapshot["total"]),
             ""]
    for row in snapshot["rows"]:
        mark = "ok" if row["answered"] else "--"
        lines.append("  [%s] %-34s %s, шагов %d" % (mark, row["question"], row["intent"], row["steps"]))
    return "\n".join(lines)


def main():
    """Печатает отчёт и, если просили, сохраняет снимок."""
    snapshot = self_metrics.summary()
    print(report(snapshot))
    if "--save" in sys.argv:
        self_metrics.write(snapshot=snapshot)
        print("\nснимок записан в data/metrics.jsonl")
    return 0


if __name__ == "__main__":
    sys.exit(main())
