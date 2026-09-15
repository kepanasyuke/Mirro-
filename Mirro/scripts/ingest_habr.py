#!/usr/bin/env python3
"""Download Habr Q&A dataset, save to disk, check format, ingest."""
import json, urllib.request, zstandard, sys, os
from pathlib import Path

URL = "https://huggingface.co/datasets/its5Q/habr_qna/resolve/main/questions.jsonl.zst"
RAW = Path(r"D:\Mirro\data\raw\ru\its5Q__habr_qna")
OUT = RAW / "questions.jsonl.zst"
PROC = Path(r"D:\Mirro\data\processed")
PROC.mkdir(parents=True, exist_ok=True)
RAW.mkdir(parents=True, exist_ok=True)

# Step 1: Download if not exists
if not OUT.exists() or OUT.stat().st_size == 0:
    print(f"Downloading Habr Q&A (500 MB)...")
    req = urllib.request.Request(URL, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=600) as resp:
        with open(OUT, "wb") as f:
            size = 0
            while True:
                chunk = resp.read(1024 * 1024)
                if not chunk:
                    break
                f.write(chunk)
                size += len(chunk)
                if size % (50 * 1024 * 1024) == 0:
                    print(f"  Downloaded {size/1e6:.0f} MB...")
    print(f"  Saved: {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")
else:
    print(f"Already have: {OUT} ({OUT.stat().st_size/1e6:.1f} MB)")

# Step 2: Check format (first line only)
print("\nChecking format...")
dctx = zstandard.ZstdDecompressor()
with open(OUT, "rb") as f:
    reader = dctx.stream_reader(f)
    first_line = b""
    while True:
        byte = reader.read(1)
        if not byte or byte == b"\n":
            break
        first_line += byte
item = json.loads(first_line.decode("utf-8", errors="replace"))
print(f"Keys: {list(item.keys())}")
for k, v in item.items():
    val = str(v)[:120]
    print(f"  {k}: {val}")

# Step 3: Stream convert
if "question" not in item and "title" not in item:
    # Try to find text fields
    for k in item:
        if isinstance(item[k], str):
            print(f"  Text field: {k} -> {item[k][:80]}")
    # Use generic: first long string is question, second is answer
    string_fields = [(k, str(v)) for k, v in item.items() if isinstance(v, str) and len(str(v)) > 20]
    if len(string_fields) >= 2:
        print(f"  Using fields: '{string_fields[0][0]}' as question, '{string_fields[1][0]}' as answer")
        q_field = string_fields[0][0]
        a_field = string_fields[1][0]
    else:
        print("  Unknown format, skipping")
        sys.exit(1)
else:
    q_field = "question" if "question" in item else "title"
    a_field = "answer" if "answer" in item else "text"

# Stream-convert
print(f"\nStream converting from Habr Q&A (q_field={q_field}, a_field={a_field})...")
converted = 0
with open(OUT, "rb") as f:
    reader = dctx.stream_reader(f)
    buf = b""
    while True:
        byte = reader.read(1)
        if not byte:
            break
        buf += byte
        if byte == b"\n":
            line = buf.decode("utf-8", errors="replace").strip()
            buf = b""
            if not line:
                continue
            try:
                item = json.loads(line)
                q = str(item.get(q_field, ""))
                a = str(item.get(a_field, ""))
                if q and a and len(a) > 30:
                    entry = {"instruction": q[:1000], "input": "", "output": a[:3000]}
                    with open(PROC / "ru.jsonl", "a", encoding="utf-8") as fout:
                        fout.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    converted += 1
                    if converted % 10000 == 0:
                        print(f"  {converted}...")
            except Exception:
                pass

print(f"\n✅ Habr Q&A: +{converted} в ru")

# Summary
print("\nИтого:")
for f in sorted(PROC.glob("*.jsonl")):
    cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
    print(f"  {f.stem:12} {cnt:>7}")