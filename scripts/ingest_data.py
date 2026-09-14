#!/usr/bin/env python3
"""Mirro Data Ingestion — convert raw datasets → processed knowledge clusters."""
import json, os, gzip, io
from pathlib import Path
from collections import defaultdict

RAW = Path(r"D:\Mirro\data\raw")
PROC = Path(r"D:\Mirro\data\processed")
PROC.mkdir(exist_ok=True)

# Map dataset keywords to Mirro knowledge clusters
DS_CLUSTER_MAP = defaultdict(lambda: "general", {
    # ru
    "ru_turbo_saiga": "ru", "ru_turbo_alpaca": "ru", "ru_sharegpt_cleaned": "ru",
    "russian_instructions": "ru", "russian_code_qa": "ru", "russian_dpo_qa": "ru",
    "ru_paraphrase": "ru", "russian_super_glue": "ru", "multiquora": "ru",
    "russian-easy-instructions": "ru",
    # code
    "python_code_instructions": "code", "code_instructions": "code", "CodeAlpaca": "code",
    "code_contests": "code", "taco": "code", "evol_instruct": "code",
    "LimitlessCode": "code", "starcoder": "code", "github-code": "code",
    "WizardCoder": "code",
    # math
    "orca-math": "math", "MATH-500": "math", "gsm8k": "math", "competition_math": "math",
    "arithmetic": "math", "bigbench": "math",
    # design
    "WebSight": "design", "InfoVQA": "design", "MMMU": "design", "idefics": "design",
    "design-bench": "design", "svg": "design", "canvas2svg": "design",
    "laion-coco": "design",
    # knowledge
    "wikipedia": "knowledge", "wikinews": "knowledge", "wikibooks": "knowledge",
    "ai-arxiv": "knowledge", "physics": "knowledge", "biology": "knowledge",
    "chemistry": "knowledge", "astronomy": "knowledge", "history": "knowledge",
    "law": "knowledge", "economics": "knowledge", "geography": "knowledge",
    "psychology": "knowledge", "sociology": "knowledge", "med_qa": "knowledge",
    "scirepe": "knowledge",
})


def detect_cluster(dataset_id: str) -> str:
    dataset_lower = dataset_id.lower()
    for key, cluster in DS_CLUSTER_MAP.items():
        if key in dataset_lower:
            return cluster
    return "general"


def convert_item(item: dict) -> dict:
    """Convert any dataset item to unified {instruction, input, output}."""
    # Alpaca format
    if "instruction" in item:
        return {
            "instruction": (item.get("instruction") or "")[:1000],
            "input": (item.get("input") or "")[:1000],
            "output": (item.get("output") or item.get("response") or "")[:4000],
        }
    # ShareGPT / Saiga / messages format
    msgs = item.get("messages") or item.get("conversations") or []
    if msgs:
        user_parts, asst_parts = [], []
        for m in msgs:
            role = m.get("role", m.get("from", "")).lower()
            content = m.get("content", m.get("value", ""))
            if role in ("user", "human"):
                user_parts.append(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False))
            elif role in ("assistant", "gpt", "bot"):
                asst_parts.append(content if isinstance(content, str) else json.dumps(content, ensure_ascii=False))
        if user_parts and asst_parts:
            return {
                "instruction": "\n".join(user_parts)[:1000],
                "input": "",
                "output": "\n".join(asst_parts)[:4000],
            }
    # Camel format (role-playing)
    if item.get("user") and item.get("assistant"):
        return {
            "instruction": str(item["user"])[:1000],
            "input": str(item.get("system", ""))[:1000],
            "output": str(item["assistant"])[:4000],
        }
    # Question/Answer
    if "question" in item and "answer" in item:
        return {
            "instruction": str(item["question"])[:1000],
            "input": str(item.get("system_prompt", item.get("context", "")))[:1000],
            "output": str(item["answer"])[:4000],
        }
    # Wikipedia abstract
    if "title" in item and ("abstract" in item or "text" in item):
        text = item.get("abstract") or item.get("text") or ""
        return {
            "instruction": f"Расскажи про: {item['title']}",
            "input": "",
            "output": str(text)[:4000],
        }
    # Just text
    if "text" in item and isinstance(item["text"], str) and len(item["text"]) > 100:
        return {
            "instruction": "Продолжи текст",
            "input": "",
            "output": item["text"][:4000],
        }
    return None


def scan_raw_data():
    """Scan raw data directory and convert everything."""
    cluster_buffers = defaultdict(list)
    total_input = 0
    total_conv = 0

    for dataset_dir in RAW.rglob("*"):
        if not dataset_dir.is_file():
            continue
        if dataset_dir.suffix not in (".json", ".jsonl", ".parquet"):
            continue
        if dataset_dir.stat().st_size == 0:
            continue

        rel_path = dataset_dir.relative_to(RAW)
        dataset_id = str(rel_path.parent).replace("__", "/")
        cluster = detect_cluster(str(rel_path))
        total_input += 1

        try:
            items = []
            data = dataset_dir.read_bytes()
            if dataset_dir.suffix == ".gz":
                with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
                    data = f.read()

            if dataset_dir.suffix == ".jsonl":
                for line in data.decode("utf-8", errors="replace").split("\n"):
                    if line.strip():
                        try: items.append(json.loads(line))
                        except: pass
            elif dataset_dir.suffix == ".json":
                try:
                    parsed = json.loads(data.decode("utf-8", errors="replace"))
                    if isinstance(parsed, list):
                        items = parsed
                    elif isinstance(parsed, dict):
                        items = [parsed]
                except: pass
            elif dataset_dir.suffix == ".parquet":
                continue  # skip parquet (needs pandas)

            for item in items:
                conv = convert_item(item)
                if conv:
                    cluster_buffers[cluster].append(conv)
                    total_conv += 1

        except Exception as e:
            pass

    # Write per-cluster files
    for cluster, examples in cluster_buffers.items():
        out_path = PROC / f"{cluster}.jsonl"
        mode = "a" if out_path.exists() else "w"
        with open(out_path, "a", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(f"  {cluster:12} → {len(examples):>6} examples  ({out_path})")

    print(f"\n  Всего: {total_input} файлов прочитано, {total_conv} примеров сохранено")


if __name__ == "__main__":
    print("🔬 Mirro Data Ingestion\n")
    scan_raw_data()
    print("\n✅ Готово")