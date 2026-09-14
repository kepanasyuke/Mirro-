#!/usr/bin/env python3
"""Download compact datasets with correct filenames and convert to JSONL."""
import json, urllib.request, io, gzip, sys
from pathlib import Path

RAW = Path(r"D:\Mirro\data\raw")
PROC = Path(r"D:\Mirro\data\processed")
RAW.mkdir(parents=True, exist_ok=True)
PROC.mkdir(parents=True, exist_ok=True)

# Correct filenames from HF API
DATASETS = [
    ("ru", "IlyaGusev/ru_turbo_saiga", "ru_turbo_saiga.jsonl.zst"),
    ("ru", "IlyaGusev/ru_turbo_alpaca", "ru_turbo_alpaca.jsonl.zst"),
    ("ru", "IlyaGusev/ru_sharegpt_cleaned", "ru_sharegpt_cleaned.jsonl"),
    ("code", "iamtarun/python_code_instructions_18k_alpaca", "data/train-00000-of-00001-8b6e212f3e1ece96.parquet"),
    ("code", "TokenBender/code_instructions_122k_alpaca_style", "code_instructions_122k_alpaca_style.json"),
    ("math", "microsoft/orca-math-word-problems-200k", "data/train-00000-of-00001.parquet"),
    ("general", "databricks/databricks-dolly-15k", "databricks-dolly-15k.jsonl"),
    ("general", "tatsu-lab/alpaca", "data/train-00000-of-00001.parquet"),
    ("code", "sahil2801/CodeAlpaca-20k", "codealpaca.json"),
    ("ru", "Den4ikAI/russian_code_qa", "data/train-00000-of-00001.parquet"),
]

def download(ds, fname):
    url = f"https://huggingface.co/datasets/{ds}/resolve/main/{fname}"
    safe = ds.replace("/", "__")
    out_path = RAW / ds.split("/")[0] / safe / fname.split("/")[-1]
    out_path.parent.mkdir(parents=True, exist_ok=True)
    if out_path.exists() and out_path.stat().st_size > 0:
        return out_path
    print(f"  ↓ {url}")
    req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/1.0"})
    try:
        resp = urllib.request.urlopen(req, timeout=180)
        data = resp.read()
        out_path.write_bytes(data)
        print(f"    → {len(data)/1e6:.1f} MB")
        return out_path
    except Exception as e:
        print(f"    ❌ {e}")
        return None

def load_jsonl(path):
    text = path.read_text("utf-8", errors="replace")
    results = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line:
            try:
                results.append(json.loads(line))
            except Exception:
                pass
    return results

def load_json(path):
    try:
        data = json.loads(path.read_text("utf-8", errors="replace"))
        if isinstance(data, list):
            return data
        return []
    except Exception:
        return []

def convert_item(item):
    if not isinstance(item, dict):
        return None
    # Alpaca
    if "instruction" in item:
        return {
            "instruction": str(item.get("instruction", ""))[:1000],
            "input": str(item.get("input", ""))[:500],
            "output": str(item.get("output", item.get("response", "")))[:3000],
        }
    # messages / conversations
    for key in ("messages", "conversations"):
        msgs = item.get(key)
        if isinstance(msgs, list) and msgs:
            user_p, asst_p = [], []
            for m in msgs:
                if isinstance(m, dict):
                    role = str(m.get("role", m.get("from", ""))).lower()
                    content = m.get("content", m.get("value", ""))
                    if role in ("user", "human"):
                        user_p.append(str(content))
                    elif role in ("assistant", "gpt", "bot"):
                        asst_p.append(str(content))
            if user_p and asst_p:
                return {
                    "instruction": "\n".join(user_p)[:1000],
                    "input": "",
                    "output": "\n".join(asst_p)[:3000],
                }
    # question/answer
    if "question" in item and "answer" in item:
        return {
            "instruction": str(item.get("question", ""))[:1000],
            "input": str(item.get("system_prompt", ""))[:500],
            "output": str(item.get("answer", ""))[:3000],
        }
    return None

def try_extract_zst(path):
    """Try to extract .zst file. If zstandard not available, skip."""
    try:
        import zstandard
        dctx = zstandard.ZstdDecompressor()
        decompressed = dctx.decompress(path.read_bytes())
        return decompressed.decode("utf-8")
    except ImportError:
        return None

def try_extract_gz(path):
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(path.read_bytes())) as f:
            return f.read().decode("utf-8")
    except Exception:
        return None

def main():
    for cat, ds, fname in DATASETS:
        path = download(ds, fname)
        if not path:
            continue

        # Decompress if needed
        items = []
        if path.suffix == ".zst":
            text = try_extract_zst(path)
            if text is None:
                print(f"    ⚠ zstandard not available, skip")
                continue
            items = [json.loads(line) for line in text.strip().split("\n") if line.strip()]
        elif path.suffix == ".parquet":
            print(f"    ⚠ parquet format requires pandas, skip")
            continue
        elif path.suffix == ".jsonl" or (path.suffix == ".json" and path.stem.endswith("jsonl")):
            items = load_jsonl(path)
        elif path.suffix == ".json":
            items = load_json(path)
        elif path.suffix == ".gz":
            text = try_extract_gz(path)
            if text:
                items = [json.loads(line) for line in text.strip().split("\n") if line.strip()]

        if not items:
            continue

        converted = [convert_item(i) for i in items if convert_item(i)]
        if converted:
            out_path = PROC / f"{cat}.jsonl"
            with open(out_path, "a", encoding="utf-8") as f:
                for item in converted:
                    f.write(json.dumps(item, ensure_ascii=False) + "\n")
            print(f"    ✅ {len(converted)} → {cat} cluster")

    # Summary
    print("\n" + "=" * 60)
    print("CLUSTER SIZES:")
    for f in sorted(PROC.glob("*.jsonl")):
        cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
        print(f"  {f.stem:12} {cnt:>7}")

if __name__ == "__main__":
    main()