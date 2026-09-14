# -*- coding: utf-8 -*-
"""Download and ingest math + design datasets into Mirro clusters."""
import json, urllib.request, time
from pathlib import Path

PROC = Path(r"D:\Mirro\data\processed")
PROC.mkdir(exist_ok=True)

TARGETS = [
    ("math", "microsoft/orca-math-word-problems-200k", "data/train-00000-of-00001.parquet"),
    ("design", "shorecode/svg-generation-6.5k-rows", "data/train-00000-of-00001.parquet"),
]

def download(ds, fname):
    url = f"https://huggingface.co/datasets/{ds}/resolve/main/{fname}"
    print(f"  ↓ {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    resp = urllib.request.urlopen(req, timeout=600)
    data = resp.read()
    print(f"    → {len(data)/1e6:.1f} MB")
    return data

def ingest_parquet(data, cluster):
    try:
        import pyarrow.parquet as pq
        import io
        table = pq.read_table(io.BytesIO(data))
        names = table.column_names
        print(f"    columns: {names}")

        converted = 0
        for batch in table.to_batches(max_chunksize=2000):
            batch_dict = batch.to_pylist()
            if cluster == "math":
                for row in batch_dict:
                    q = row.get("question", row.get("instruction", ""))
                    a = row.get("answer", row.get("output", ""))
                    if q and a and len(a) > 20:
                        entry = {"instruction": str(q)[:1000], "input": "", "output": str(a)[:3000]}
                        with open(PROC / "math.jsonl", "a", encoding="utf-8") as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        converted += 1
            elif cluster == "design":
                for row in batch_dict:
                    inst = row.get("instruction", row.get("prompt", ""))
                    out = row.get("output", row.get("svg", ""))
                    if not inst:
                        # SVG generation: query -> svg code
                        inst = row.get("query", row.get("text", ""))
                        out = row.get("answer", row.get("svg_code", ""))
                    if inst and out and len(out) > 20:
                        entry = {"instruction": str(inst)[:1000], "input": "", "output": str(out)[:3000]}
                        with open(PROC / "design.jsonl", "a", encoding="utf-8") as f:
                            f.write(json.dumps(entry, ensure_ascii=False) + "\n")
                        converted += 1

        print(f"    ✅ {converted} в {cluster}")
        return converted
    except Exception as e:
        print(f"    ❌ {e}")
        return 0

total = 0
for cluster, ds, fname in TARGETS:
    print(f"📦 {ds} → {cluster}")
    data = download(ds, fname)
    n = ingest_parquet(data, cluster)
    total += n
    time.sleep(0.5)

print(f"\n{'='*50}")
print(f"  Всего добавлено: {total}")
print(f"\n  Итоговые кластеры:")
for f in sorted(PROC.glob("*.jsonl")):
    cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
    print(f"    {f.stem:12} {cnt:>8}")