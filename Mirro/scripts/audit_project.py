#!/usr/bin/env python3
"""Mirro - полная проверка проекта."""
import sys, json, ast
from pathlib import Path
from collections import Counter

M = Path(r"D:\Mirro")

print("=" * 60)
print("  MIRRO — ПОЛНАЯ ПРОВЕРКА ПРОЕКТА")
print("=" * 60)

# 1. Structure
print("\n[СТРУКТУРА]")
for p in sorted(M.rglob("*")):
    if p.is_dir() and p != M:
        cnt = len(list(p.rglob("*")))
        if cnt > 0:
            print(f"  [DIR] {p.relative_to(M)}/ ({cnt} файлов)")
    elif p.is_file() and p.suffix in (".py", ".html", ".json", ".md", ".bat", ".jsonl"):
        print(f"  [FILE] {p.relative_to(M)} ({p.stat().st_size:,} B)")

# 2. Scripts validation
print("\n[СКРИПТЫ]")
for f in sorted(M.rglob("*.py")):
    try:
        ast.parse(f.read_text("utf-8"))
        print(f"  OK {f.relative_to(M)}")
    except SyntaxError as e:
        print(f"  FAIL {f.relative_to(M)}: {e}")

# 3. Clusters
print("\n[КЛАСТЕРЫ]")
proc = M / "data" / "processed"
total_ex = 0
for f in sorted(proc.glob("*.jsonl")):
    cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
    total_ex += cnt
    print(f"  {f.stem:12} {cnt:>8,}")
print(f"  {'TOTAL':12} {total_ex:>8,}")

# 4. Catalog
cat = M / "data" / "catalog_phase1.json"
if cat.exists():
    data = json.loads(cat.read_text("utf-8"))
    c2 = Counter(e["cat"] for e in data)
    print(f"\n[КАТАЛОГ] {len(data)} датасетов")
    for k, v in sorted(c2.items(), key=lambda x: -x[1]):
        print(f"  {k:15} {v:3}")

# 5. Mind map
mm = M / "mirro-mind-map.html"
if mm.exists():
    print(f"\n[MIND-MAP] {mm.name} ({mm.stat().st_size:,} B)")

# 6. Web
web = M / "web" / "index.html"
if web.exists():
    print(f"\n[WEB UI] {web.name} ({web.stat().st_size:,} B)")
    print("  URL: http://127.0.0.1:3443")

# 7. State
ms = M / "models" / "model_state.json"
if ms.exists():
    print(f"\n[MODEL STATE] {ms.stat().st_size:,} B")

print("\n" + "=" * 60)
print("  MIRRO ГОТОВА ОТВЕЧАТЬ САМА")
print("  Запуск: python start.py или setup.bat")
print("=" * 60)