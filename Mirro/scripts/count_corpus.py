# -*- coding: utf-8 -*-
"""Точный подсчёт корпуса."""
from pathlib import Path

p = Path(r"D:\Mirro\data\corpus_big")
total = 0
total_bytes = 0
for f in sorted(p.glob("*.jsonl")):
    n = 0
    with open(f, encoding="utf-8", errors="replace") as fh:
        for line in fh:
            if line.strip():
                n += 1
    total += n
    total_bytes += f.stat().st_size
    print(f"  {f.name}: {n:,}")

print(f"ИТОГО: {total:,} примеров, {total_bytes/1e9:.2f} GB")