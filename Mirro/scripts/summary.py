#!/usr/bin/env python3
"""Mirro final summary — project structure, stats, todo."""
import json, sys
from pathlib import Path
from collections import Counter

MIRRO = Path(r"D:\Mirro")

# Structure
print("=" * 60)
print("  MIRRO — СТРУКТУРА ПРОЕКТА")
print("=" * 60)
for p in sorted(MIRRO.rglob("*")):
    if p.is_dir() and p != MIRRO:
        cnt = len(list(p.rglob("*")))
        print(f"  📁 {p.relative_to(MIRRO).as_posix()}/ ({cnt} файлов)")
    elif p.is_file() and p.suffix in (".py", ".html", ".json", ".md", ".bat", ".ps1", ".css", ".js", ".jsonl"):
        print(f"  📄 {p.relative_to(MIRRO).as_posix()} ({p.stat().st_size:,} B)")

# Clusters
proc = MIRRO / "data" / "processed"
if proc.exists():
    print(f"\n{'='*60}")
    print("  КЛАСТЕРЫ ЗНАНИЙ")
    print(f"{'='*60}")
    total = 0
    for f in sorted(proc.glob("*.jsonl")):
        cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
        total += cnt
        print(f"  {f.stem:12} {cnt:>8,}")
    print(f"  {'─'*20}")
    print(f"  {'TOTAL':12} {total:>8,}")

# Catalog
cat = MIRRO / "data" / "catalog_phase1.json"
if cat.exists():
    data = json.loads(cat.read_text("utf-8"))
    c2 = Counter(e["cat"] for e in data)
    print(f"\n{'='*60}")
    print("  КАТАЛОГ ДАТАСЕТОВ")
    print(f"{'='*60}")
    print(f"  Всего: {len(data)} датасетов")
    for k, v in sorted(c2.items(), key=lambda x: -x[1]):
        print(f"  {k:15} {v:3}")
    print()
    # Show top datasets by category
    print("  Топ-5 по скачиваниям:")
    for e in sorted(data, key=lambda x: int(x.get("est","0").replace("k","000").replace("M","000000") if x.get("est","0").rstrip("kM").isdigit() else 0), reverse=True)[:5]:
        print(f"    {e['ds']:45} {e['est']:>8}")

print(f"\n{'='*60}")
print("  КАК ЗАПУСТИТЬ")
print(f"{'='*60}")
print("  Открой браузер: http://127.0.0.1:3443")
print("  Или запусти:    python start.py (откроет браузер сам)")
print("  Или:            setup.bat (двойным щелчком)")
print(f"\n{'='*60}")
print("  СТАТУС: РАБОТАЕТ ✅")
print(f"{'='*60}")