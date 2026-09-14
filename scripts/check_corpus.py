# -*- coding: utf-8 -*-
"""Check quality of generated corpus (sample)."""
import json, random
from pathlib import Path

files = list(Path(r"D:\Mirro\data\corpus_big").glob("*.jsonl"))
print("Файлов:", len(files))

for f in random.sample(files, min(4, len(files))):
    lines = f.read_text("utf-8", errors="replace").strip().split("\n")
    print(f"--- {f.name} ({len(lines)} строк) ---")
    for _ in range(3):
        ex = json.loads(random.choice(lines))
        q = ex["instruction"][:70]
        a = ex["output"][:70]
        print(f"  Q: {q}")
        print(f"  A: {a}")
        print()