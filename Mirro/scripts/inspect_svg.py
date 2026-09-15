# -*- coding: utf-8 -*-
"""Inspect SVG dataset format and ingest correctly."""
import urllib.request, io, json
from pathlib import Path
import pyarrow.parquet as pq

url = "https://huggingface.co/datasets/shorecode/svg-generation-6.5k-rows/resolve/main/data/test-00000-of-00001.parquet"
print("Достаю ТЕСТОВЫЙ файл (маленький)...")
req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
resp = urllib.request.urlopen(req, timeout=120)
data = resp.read()
print(f"  {len(data)/1e6:.1f} MB")

table = pq.read_table(io.BytesIO(data))
names = table.column_names
print(f"  Колонки: {names}")
print(f"  Строк: {table.num_rows}")

rows = table.slice(0, 3).to_pylist()
for i, r in enumerate(rows):
    print(f"\n  Строка {i}:")
    for k in names:
        v = r[k]
        vs = str(v)[:100] if v is not None else "None"
        print(f"    {k}: {vs!r}")
    print(f"    text length: {len(str(r.get('text','')))}")
    print(f"    target length: {len(str(r.get('target','')))}")