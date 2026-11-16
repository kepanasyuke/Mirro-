# -*- coding: utf-8 -*-
"""ru_coverage.py — насколько русский вопрос достаёт до базы понятий.

Меряет три вещи:
  * сколько понятий вообще доступны из русского (есть русский алиас);
  * у скольких есть русский текст ответа (поле `ru`);
  * сколько понятий связаны рёбрами графа определений.

Запуск:
    python tools/ru_coverage.py                 # сводка
    python tools/ru_coverage.py --gaps 40       # ещё и первые 40 понятий без русского имени
    python tools/ru_coverage.py --csv out.csv   # выгрузка по понятиям
"""
import argparse
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)


def _is_cyrillic(text):
    """Есть ли в строке кириллица. Один return: bool."""
    return any("\u0400" <= char <= "\u04ff" for char in text or "")


def collect():
    """Сводка покрытия по реестру понятий. Один return: dict."""
    from algos import concepts

    registry = concepts.build()
    rows = []
    for concept in registry.values():
        aliases = tuple(concept.get("aliases") or ())
        ru_aliases = [alias for alias in aliases if _is_cyrillic(alias)]
        rows.append({
            "id": concept.get("id") or concept.get("name"),
            "name": concept.get("name"),
            "ru_aliases": ru_aliases,
            "has_ru_text": bool(concept.get("ru")),
            "has_en_text": bool(concept.get("en")),
        })
    return rows


def summary(rows):
    """Числа покрытия. Один return: dict."""
    total = len(rows)
    reachable = sum(1 for row in rows if row["ru_aliases"])
    with_ru = sum(1 for row in rows if row["has_ru_text"])
    with_en = sum(1 for row in rows if row["has_en_text"])
    both = sum(1 for row in rows if row["has_ru_text"] and row["has_en_text"])
    return {"concepts": total, "reachable_from_ru": reachable,
            "with_ru_text": with_ru, "with_en_text": with_en, "both": both,
            "ru_share": round(100.0 * reachable / max(total, 1), 1),
            "ru_text_share": round(100.0 * with_ru / max(total, 1), 1)}


def _edges_count():
    """Сколько рёбер в графе понятий. Один return: int."""
    from algos.concept_graph import EDGES

    return sum(len(targets) for targets in EDGES.values())


def main(argv):
    """CLI отчёта. Один return: int."""
    parser = argparse.ArgumentParser(description="Покрытие базы понятий из русского")
    parser.add_argument("--gaps", type=int, default=0, help="сколько понятий без русского имени показать")
    parser.add_argument("--csv", default="", help="выгрузить таблицу в файл")
    args = parser.parse_args(argv)

    rows = collect()
    stats = summary(rows)
    print("понятий всего:            %d" % stats["concepts"])
    print("доступны из русского:     %d (%.1f%%)" % (stats["reachable_from_ru"], stats["ru_share"]))
    print("есть русский текст:       %d (%.1f%%)" % (stats["with_ru_text"], stats["ru_text_share"]))
    print("есть английский текст:    %d" % stats["with_en_text"])
    print("оба языка:                %d" % stats["both"])
    print("рёбер в графе понятий:    %d" % _edges_count())

    if args.gaps:
        missing = [row["name"] for row in rows if not row["ru_aliases"]]
        print("\nбез русского имени (первые %d из %d):" % (min(args.gaps, len(missing)), len(missing)))
        for name in missing[:args.gaps]:
            print("  -", name)

    if args.csv:
        with io.open(args.csv, "w", encoding="utf-8") as handle:
            handle.write("id,name,ru_aliases,has_ru_text,has_en_text\n")
            for row in rows:
                handle.write("%s,%s,%s,%s,%s\n" % (
                    row["id"], row["name"], "|".join(row["ru_aliases"]),
                    int(row["has_ru_text"]), int(row["has_en_text"])))
        print("\nтаблица:", args.csv)
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
