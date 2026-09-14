#!/usr/bin/env python3
"""Download SVG icons dataset (JSONL) into design cluster."""
import json, urllib.request
from pathlib import Path

PROC = Path(r"D:\Mirro\data\processed")
PROC.mkdir(parents=True, exist_ok=True)

URLS = [
    ("design", "https://huggingface.co/datasets/TuneIt/SVG-Icons-Generation/resolve/main/data.jsonl", "svg_icons"),
    ("design", "https://huggingface.co/datasets/vinoku89/svg-code-generation/resolve/main/README.md", None),
]

def fetch(url):
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"})
    with urllib.request.urlopen(req, timeout=60) as resp:
        return resp.read()

def convert_line(line, cluster):
    try:
        item = json.loads(line)
    except Exception:
        return None
    if not isinstance(item, dict):
        return None
    # SVG generation: usually prompt/instruction + svg output
    if "instruction" in item:
        return {
            "instruction": str(item.get("instruction", ""))[:1000],
            "input": str(item.get("input", ""))[:500],
            "output": str(item.get("output", item.get("response", "")))[:3000],
        }
    if "prompt" in item and "svg" in item:
        return {
            "instruction": "Создай SVG: " + str(item.get("prompt", ""))[:500],
            "input": "",
            "output": str(item.get("svg", ""))[:3000],
        }
    if "query" in item and "answer" in item:
        return {
            "instruction": str(item.get("query", ""))[:1000],
            "input": "",
            "output": str(item.get("answer", ""))[:3000],
        }
    return None

def main():
    for cluster, url, label in URLS:
        if url is None or label is None:
            continue
        print(f"↓ {label}: {url}")
        try:
            data = fetch(url)
            print(f"  → {len(data)/1024:.0f} KB")
        except Exception as e:
            print(f"  ❌ {e}")
            return

        text = data.decode("utf-8", errors="replace")
        converted = []
        for line in text.strip().split("\n"):
            c = convert_line(line, cluster)
            if c and c.get("instruction") and c.get("output"):
                converted.append(c)

        # Print a sample
        if converted:
            ex = converted[0]
            print(f"  Пример: {ex['instruction'][:80]}")
            print(f"  Ответ: {ex['output'][:60]}...")

        out_path = PROC / f"{cluster}.jsonl"
        with open(out_path, "a", encoding="utf-8") as f:
            for c in converted:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        print(f"  ✅ +{len(converted)} в {cluster}")

    print("\nИтого:")
    for f in sorted(PROC.glob("*.jsonl")):
        cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
        print(f"  {f.stem:12} {cnt:>7}")

if __name__ == "__main__":
    main()