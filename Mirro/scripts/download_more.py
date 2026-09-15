#!/usr/bin/env python3
"""Download verified JSON datasets for Mirro (design + code clusters)."""
import json, urllib.request, sys
from pathlib import Path

PROC = Path(r"D:\Mirro\data\processed")
PROC.mkdir(parents=True, exist_ok=True)

# Verified datasets with correct filenames (from HF API)
TARGETS = [
    ("code", "sahil2801/CodeAlpaca-20k", "code_alpaca_20k.json"),
    ("design", "michaelsyao/design_bench_data", None),  # weird - skip
]

def convert_json(data, cluster):
    if isinstance(data, dict):
        data = [data]
    if not isinstance(data, list):
        return []
    converted = []
    for item in data:
        if not isinstance(item, dict):
            continue
        if "instruction" in item:
            converted.append({
                "instruction": str(item.get("instruction", ""))[:1000],
                "input": str(item.get("input", ""))[:500],
                "output": str(item.get("output", item.get("response", "")))[:3000],
            })
        elif "messages" in item:
            msgs = item["messages"]
            user_p = [m.get("content", "") for m in msgs if isinstance(m, dict) and m.get("role") in ("user", "human")]
            asst_p = [m.get("content", "") for m in msgs if isinstance(m, dict) and m.get("role") in ("assistant", "gpt", "bot")]
            if user_p and asst_p:
                converted.append({"instruction": "\n".join(user_p)[:1000], "input": "", "output": "\n".join(asst_p)[:3000]})
    return converted

def download(ds, fname):
    url = f"https://huggingface.co/datasets/{ds}/resolve/main/{fname}"
    print(f"  ↓ {url}")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
        resp = urllib.request.urlopen(req, timeout=180)
        data = resp.read()
        print(f"    → {len(data)/1e6:.1f} MB")
        return data
    except Exception as e:
        print(f"    ❌ {e}")
        return None

def main():
    total = 0
    # 1. CodeAlpaca - verified
    print("=" * 50)
    print(" 1. CodeAlpaca-20k (код)")
    print("=" * 50)
    data = download("sahil2801/CodeAlpaca-20k", "code_alpaca_20k.json")
    if data:
        items = convert_json(json.loads(data.decode("utf-8", errors="replace")), "code")
        with open(PROC / "code.jsonl", "a", encoding="utf-8") as f:
            for it in items:
                f.write(json.dumps(it, ensure_ascii=False) + "\n")
        total += len(items)
        print(f"  ✅ {len(items)} → code cluster")

    # 2. Try other known-good small JSON datasets for design
    print("\n" + "=" * 50)
    print(" 2. Ещё дизайн-датасеты")
    print("=" * 50)
    more = [
        # Design QA (Alpaca style, JSON)
        ("softengg/design_qa", ["design_qa.jsonl"]),
        ("bentrevett/stackexchange-html", ["data.jsonl"]),
        # Try code review json
        ("AzerChakir/CodeReviewWithSummaryQA", ["data/train.json"]),
    ]
    for ds, files in more:
        for fname in files:
            data = download(ds, fname)
            if data:
                try:
                    items = convert_json(json.loads(data.decode("utf-8", errors="replace")), "design" if "design" in ds else "code")
                    with open(PROC / ("design.jsonl" if "design" in ds else "code.jsonl"), "a", encoding="utf-8") as f:
                        for it in items:
                            f.write(json.dumps(it, ensure_ascii=False) + "\n")
                    total += len(items)
                    print(f"  ✅ {len(items)} from {ds}")
                except Exception as e:
                    print(f"  ⚠ parse: {e}")

    # Summary
    print("\n" + "=" * 50)
    print("PROCESSED CLUSTERS:")
    for f in sorted(PROC.glob("*.jsonl")):
        cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
        print(f"  {f.stem:12} {cnt:>7}")
    print(f"\n  Всего добавлено: {total}")

if __name__ == "__main__":
    main()