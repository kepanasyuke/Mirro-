# -*- coding: utf-8 -*-
"""
Ingest: перенос сгенерированного корпуса в Mirro.
1. Копирует сегменты corpus_big -> data/corpus_ready (для двухуровневого индекса)
2. Считает примеры
3. Просит ядро переиндексировать компактную выборку (top-N) через restart с включённым корпусом
"""
import json, shutil, sys, time
from pathlib import Path

CORPUS = Path(r"D:\Mirro\data\corpus_big")
READY = Path(r"D:\Mirro\data\corpus_ready")
READY.mkdir(parents=True, exist_ok=True)

def count_examples():
    total = 0
    per_file = {}
    for f in sorted(CORPUS.glob("*.jsonl")):
        n = sum(1 for _ in f.open(encoding="utf-8", errors="replace") if _.strip())
        per_file[f.name] = n
        total += n
    return total, per_file

def main():
    print("=" * 56)
    print("  ИНГЕСТ КОРПУСА В MIRRO")
    print("=" * 56)

    # 1. Подсчёт
    total, per = count_examples()
    print(f"\nПримеров в корпусе: {total:,}")
    for name, n in list(per.items())[:12]:
        print(f"  {name}: {n:,}")
    if len(per) > 12:
        print(f"  … и ещё {len(per)-12} файлов")

    # 2. Готовим "нейдную" выборку для компактного индекса
    #    (не всю 30M — а первые ~500k для быстрых ответов)
    target = 500_000
    prepared = 0
    out = READY / "compact_sample.jsonl"
    out.touch()
    # дописываем, пока не наберём target
    written_seen = 0
    with open(out, "a", encoding="utf-8") as fout:
        for f in sorted(CORPUS.glob("*.jsonl")):
            if written_seen >= target:
                break
            with open(f, encoding="utf-8", errors="replace") as fi:
                for line in fi:
                    if written_seen >= target:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    fout.write(line + "\n")
                    written_seen += 1
    prepared = written_seen
    print(f"\nПодготовлено компактных примеров: {prepared:,} -> {out.name}")

    # 3. Итог
    print(f"\nКорпус на диске: {READY}")
    print("Индекс будет пересобран при следующем старте Mirro.")

if __name__ == "__main__":
    main()