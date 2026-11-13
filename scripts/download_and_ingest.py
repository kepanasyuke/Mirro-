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
    path = None
    if out_path.exists() and out_path.stat().st_size > 0:
        path = out_path
    else:
        print(f"  ↓ {url}")
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) Mirro/1.0"})
        try:
            resp = urllib.request.urlopen(req, timeout=180)
            data = resp.read()
            out_path.write_bytes(data)
            print(f"    → {len(data)/1e6:.1f} MB")
            path = out_path
        except Exception as e:
            print(f"    ❌ {e}")
            path = None
    return path

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
    data_list = []
    try:
        data = json.loads(path.read_text("utf-8", errors="replace"))
        if isinstance(data, list):
            data_list = data
    except Exception:
        data_list = []
    return data_list

def convert_item(item):
    conv = None
    if isinstance(item, dict):
        # Alpaca
        if "instruction" in item:
            conv = {
                "instruction": str(item.get("instruction", ""))[:1000],
                "input": str(item.get("input", ""))[:500],
                "output": str(item.get("output", item.get("response", "")))[:3000],
            }
        # messages / conversations
        elif item.get("messages") or item.get("conversations"):
            conv = _convert_messages(item)
        # question/answer
        elif "question" in item and "answer" in item:
            conv = {
                "instruction": str(item.get("question", ""))[:1000],
                "input": str(item.get("system_prompt", ""))[:500],
                "output": str(item.get("answer", ""))[:3000],
            }
    return conv


def _convert_messages(item):
    """Преобразует messages/conversations в пару user/assistant. Один return:
    dict или None (нет обоих ролей)."""
    conv = None
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
                conv = {
                    "instruction": "\n".join(user_p)[:1000],
                    "input": "",
                    "output": "\n".join(asst_p)[:3000],
                }
                break
    return conv

def try_extract_zst(path):
    """Try to extract .zst file. If zstandard not available, skip."""
    text = None
    try:
        import zstandard
        dctx = zstandard.ZstdDecompressor()
        decompressed = dctx.decompress(path.read_bytes())
        text = decompressed.decode("utf-8")
    except ImportError:
        text = None
    return text

def try_extract_gz(path):
    text = None
    try:
        with gzip.GzipFile(fileobj=io.BytesIO(path.read_bytes())) as f:
            text = f.read().decode("utf-8")
    except Exception:
        text = None
    return text

def main():
    for cat, ds, fname in DATASETS:
        path = download(ds, fname)
        if path:
            _process_one(cat, path)


def _process_one(cat, path):
    """Обрабатывает один скачанный файл: распаковка и запись в процесс.
    Один return: None."""
    items = []
    if path.suffix == ".zst":
        text = try_extract_zst(path)
        if text is not None:
            items = [json.loads(line) for line in text.strip().split("\n") if line.strip()]
        else:
            print(f"    ⚠ zstandard not available, skip")
    elif path.suffix == ".parquet":
        print(f"    ⚠ parquet format requires pandas, skip")
    elif path.suffix == ".jsonl" or (path.suffix == ".json" and path.stem.endswith("jsonl")):
        items = load_jsonl(path)
    elif path.suffix == ".json":
        items = load_json(path)
    elif path.suffix == ".gz":
        text = try_extract_gz(path)
        if text:
            items = [json.loads(line) for line in text.strip().split("\n") if line.strip()]

    if items:
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