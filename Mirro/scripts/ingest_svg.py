# -*- coding: utf-8 -*-
"""Ingest SVG generation dataset correctly: text -> instruction, target -> svg output."""
import urllib.request, io, json, time
from pathlib import Path
import pyarrow.parquet as pq

PROC = Path(r"D:\Mirro\data\processed")

FILES = [
    "https://huggingface.co/datasets/shorecode/svg-generation-6.5k-rows/resolve/main/data/train-00000-of-00001.parquet",
    "https://huggingface.co/datasets/shorecode/svg-generation-6.5k-rows/resolve/main/data/test-00000-of-00001.parquet",
]

total = 0
for url in FILES:
    print(f"↓ {url.split('/')[-1]}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
    resp = urllib.request.urlopen(req, timeout=300)
    data = resp.read()
    print(f"  {len(data)/1e6:.1f} MB")

    table = pq.read_table(io.BytesIO(data))
    names = table.column_names
    print(f"  columns: {names}, rows: {table.num_rows}")

    n = 0
    for batch in table.to_batches(max_chunksize=2000):
        for row in batch.to_pylist():
            text = row.get("text", "") or ""
            target = row.get("target", "") or ""
            if text and target and len(target) > 30:
                entry = {
                    "instruction": str(text)[:1000],
                    "input": "",
                    "output": str(target)[:3500],
                }
                with open(PROC / "design.jsonl", "a", encoding="utf-8") as f:
                    f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                n += 1
    total += n
    print(f"  +{n} примеров SVG-кода")
    time.sleep(0.5)

print(f"\n✅ Всего добавлено в design: {total}")
print("Итог кластера design:")
cnt = sum(1 for _ in (PROC / "design.jsonl").open(encoding="utf-8") if _.strip())
print(f"  design: {cnt} примеров")