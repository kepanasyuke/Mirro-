# -*- coding: utf-8 -*-
"""Консолидация самообученного корпуса Mirro (задача 4).

Сжимает и сводит data/self_learned/*.jsonl:
  * дедуплицирует пары по (префикс вопроса → начало ответа);
  * отбрасывает слишком короткие/пустые пары;
  * считает статистику «до/после» и пишет сводку.

Без внешних библиотек, один return на функцию, атомарно (по LINTER.md).
Запуск:  python scripts/consolidate_knowledge.py [--apply]
(без --apply — сухой прогон; результат в data/self_learned_summary.json)
"""
import argparse, json, re
from pathlib import Path

MIRRO = Path(__file__).resolve().parent.parent
SELF = MIRRO / "data" / "self_learned"
SUMMARY = MIRRO / "data" / "self_learned_summary.json"

_RE = re.compile(r"\s+")


def norm_key(instruction, output):
    """Ключ дедупа: слева вопрос (первые 40), справа ответ (первые 60).
    Один return: str."""
    return (instruction[:40] + "::" + output[:60]).lower()


def consolide_file(path):
    """Консолидирует один JSONL: дедуп, отброс мусора. Возвращает (kept, dropped).
    Один return: tuple."""
    kept = 0
    dropped = 0
    seen = set()
    out = []
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            for line in fh:
                line = line.strip().lstrip("\uFEFF")
                if not line:
                    continue
                try:
                    rec = json.loads(line)
                except Exception:
                    dropped += 1
                    continue
                inst = str(rec.get("instruction", "") or "").strip()
                outp = str(rec.get("output", "") or "").strip()
                if len(inst) < 3 or len(outp) < 3:
                    dropped += 1
                    continue
                key = norm_key(inst, outp)
                if key in seen:
                    dropped += 1
                    continue
                seen.add(key)
                out.append(rec)
                kept += 1
    except OSError:
        return 0, 0
    return out, kept, dropped


def main():
    ap = argparse.ArgumentParser(description="Консолидация самообученного корпуса")
    ap.add_argument("--apply", action="store_true", help="реально перезаписать")
    args = ap.parse_args()

    total_before = 0
    total_after = 0
    for path in sorted(SELF.glob("*.jsonl")):
        try:
            total_before += sum(1 for _ in open(path, encoding="utf-8", errors="ignore"))
        except OSError:
            pass

    kept_all = 0
    dropped_all = 0
    for path in sorted(SELF.glob("*.jsonl")):
        out, kept, dropped = consolide_file(path)
        kept_all += kept
        dropped_all += dropped
        if args.apply and out:
            try:
                with open(path, "w", encoding="utf-8") as fh:
                    for rec in out:
                        fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
            except OSError:
                pass

    total_after = kept_all
    summary = {"before": total_before, "after": total_after,
               "dropped": total_before - total_after, "applied": bool(args.apply)}
    try:
        SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), "utf-8")
    except OSError:
        pass
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())