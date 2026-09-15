#!/usr/bin/env python3
"""Stream decompress Habr Q&A .zst to .jsonl, then ingest into ru cluster."""
import json, zstandard, time
from pathlib import Path

ZST = Path(r"D:\Mirro\data\raw\ru\its5Q__habr_qna\questions.jsonl.zst")
JSONL_TMP = Path(r"D:\Mirro\data\raw\ru\its5Q__habr_qna\questions_temp.jsonl")
PROC = Path(r"D:\Mirro\data\processed")

if not ZST.exists():
    print("File not found, download first")
    exit(1)

# Step 1: decompress to temp file
if not JSONL_TMP.exists() or JSONL_TMP.stat().st_size == 0:
    print(f"Decompressing .zst ({ZST.stat().st_size/1e6:.1f} MB)...")
    t0 = time.time()
    dctx = zstandard.ZstdDecompressor()
    with open(ZST, "rb") as fin:
        with open(JSONL_TMP, "wb") as fout:
            dctx.copy_stream(fin, fout)
    elapsed = time.time() - t0
    print(f"  Done in {elapsed:.1f}s, size: {JSONL_TMP.stat().st_size/1e6:.1f} MB")
else:
    print(f"Already decompressed: {JSONL_TMP.stat().st_size/1e6:.1f} MB")

# Step 2: Check first line
print("\nChecking format...")
with open(JSONL_TMP, "r", encoding="utf-8", errors="replace") as f:
    first = f.readline().strip()
item = json.loads(first)
print(f"Keys: {list(item.keys())}")
for k, v in item.items():
    if isinstance(v, str) and len(v) < 120:
        print(f"  {k}: {v}")
    elif isinstance(v, str):
        print(f"  {k}: {v[:80]}...")

# Map fields
# Habr Q&A format: title + description = question, answers = list of answer objects
if "answers" in item and isinstance(item.get("answers"), list):
    q_field = "description"
    a_field = "answers"
    print(f"Using: q={q_field}, a={a_field} (list)")
elif "question" in item or "title" in item:
    q_field = "question" if "question" in item else "title"
    a_field = "answer" if "answer" in item else "text" if "text" in item else None
    print(f"Using: q={q_field}, a={a_field}")
else:
    str_fields = [(k, str(v)) for k, v in item.items() if isinstance(v, str) and len(str(v)) > 30]
    if len(str_fields) >= 2:
        q_field = str_fields[0][0]
        a_field = str_fields[1][0]
        print(f"Using generic: q={q_field}, a={a_field}")
    else:
        print("Unknown format")
        exit(1)

# Step 3: Stream convert
print(f"\nConverting...")
total = 0
converted = 0
t0 = time.time()
with open(JSONL_TMP, "r", encoding="utf-8", errors="replace") as fin:
    with open(PROC / "ru.jsonl", "a", encoding="utf-8") as fout:
        for i, line in enumerate(fin, 1):
            total += 1
            line = line.strip()
            if not line:
                continue
            try:
                item = json.loads(line)
                q = str(item.get(q_field, ""))
                if not q or len(q) < 10:
                    continue

                # Handle answers: list -> take first answer text
                if a_field == "answers":
                    answer_list = item.get("answers", [])
                    a = ""
                    if answer_list and isinstance(answer_list, list):
                        first_answer = answer_list[0]
                        if isinstance(first_answer, dict):
                            a = first_answer.get("body", first_answer.get("text", first_answer.get("answer", "")))
                        elif isinstance(first_answer, str):
                            a = first_answer
                else:
                    a = str(item.get(a_field, ""))

                if a and len(a) > 30:
                    entry = {"instruction": q[:1000], "input": "", "output": a[:3000]}
                    fout.write(json.dumps(entry, ensure_ascii=False) + "\n")
                    converted += 1
            except Exception:
                pass
            if total % 100000 == 0:
                elapsed = time.time() - t0
                print(f"  {total:,} lines read, {converted:,} converted ({elapsed:.1f}s)")

elapsed = time.time() - t0
print(f"\n✅ Habr Q&A: {converted:,} добавлено в ru из {total:,} строк (за {elapsed:.1f}s)")

# Clean temp
JSONL_TMP.unlink(missing_ok=True)
print("Temp file removed")

# Summary
print("\nИтого кластеры:")
for f in sorted(PROC.glob("*.jsonl")):
    cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
    print(f"  {f.stem:12} {cnt:>7}")