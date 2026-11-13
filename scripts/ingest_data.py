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
    cluster = "general"
    for key, c in DS_CLUSTER_MAP.items():
        if key in dataset_lower:
            cluster = c
            break
    return cluster


def convert_item(item: dict) -> dict:
    """Convert any dataset item to unified {instruction, input, output}."""
    conv = None
    if "instruction" in item:
        # Alpaca format
        conv = {
            "instruction": (item.get("instruction") or "")[:1000],
            "input": (item.get("input") or "")[:1000],
            "output": (item.get("output") or item.get("response") or "")[:4000],
        }
    elif item.get("messages") or item.get("conversations"):
        conv = _convert_messages(item)
    elif item.get("user") and item.get("assistant"):
        # Camel format (role-playing)
        conv = {
            "instruction": str(item["user"])[:1000],
            "input": str(item.get("system", ""))[:1000],
            "output": str(item["assistant"])[:4000],
        }
    elif "question" in item and "answer" in item:
        # Question/Answer
        conv = {
            "instruction": str(item["question"])[:1000],
            "input": str(item.get("system_prompt", item.get("context", "")))[:1000],
            "output": str(item["answer"])[:4000],
        }
    elif "title" in item and ("abstract" in item or "text" in item):
        # Wikipedia abstract
        text = item.get("abstract") or item.get("text") or ""
        conv = {
            "instruction": f"Расскажи про: {item['title']}",
            "input": "",
            "output": str(text)[:4000],
        }
    elif "text" in item and isinstance(item["text"], str) and len(item["text"]) > 100:
        # Just text
        conv = {
            "instruction": "Продолжи текст",
            "input": "",
            "output": item["text"][:4000],
        }
    return conv


def _convert_messages(item):
    """ShareGPT/Saiga: messages или conversations → пара user/assistant.
    Один return: dict|None."""
    conv = None
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
            conv = {
                "instruction": "\n".join(user_parts)[:1000],
                "input": "",
                "output": "\n".join(asst_parts)[:4000],
            }
    return conv


def scan_raw_data():
    """Scan raw data directory and convert everything."""
    cluster_buffers = defaultdict(list)
    total_input = 0
    total_conv = 0

    for dataset_dir in RAW.rglob("*"):
        is_usable_file = (
            dataset_dir.is_file()
            and dataset_dir.suffix in (".json", ".jsonl", ".parquet", ".gz")
            and dataset_dir.stat().st_size > 0
        )
        if is_usable_file:
            rel_path = dataset_dir.relative_to(RAW)
            cluster = detect_cluster(str(rel_path))
            total_input += 1
            added = _extract_items(dataset_dir)
            for item in added:
                conv = convert_item(item)
                if conv:
                    cluster_buffers[cluster].append(conv)
                    total_conv += 1

    # Write per-cluster files
    for cluster, examples in cluster_buffers.items():
        out_path = PROC / f"{cluster}.jsonl"
        with open(out_path, "a", encoding="utf-8") as f:
            for ex in examples:
                f.write(json.dumps(ex, ensure_ascii=False) + "\n")
        print(f"  {cluster:12} → {len(examples):>6} examples  ({out_path})")

    print(f"\n  Всего: {total_input} файлов прочитано, {total_conv} примеров сохранено")


def _extract_items(dataset_dir):
    """Извлекает список записей из одного файла (json/jsonl/gz/parquet).
    Один return: list."""
    items = []
    try:
        data = dataset_dir.read_bytes()
        suffix = dataset_dir.suffix
        # .gz — сначала распаковываем, затем определяем формат по настоящему имени
        if suffix == ".gz":
            with gzip.GzipFile(fileobj=io.BytesIO(data)) as f:
                data = f.read()
            suffix = Path(dataset_dir.stem).suffix  # "xx.jsonl.gz" -> ".jsonl"

        if suffix == ".jsonl":
            for line in data.decode("utf-8", errors="replace").split("\n"):
                if line.strip():
                    try:
                        items.append(json.loads(line))
                    except Exception:
                        pass
        elif suffix == ".json":
            try:
                parsed = json.loads(data.decode("utf-8", errors="replace"))
                if isinstance(parsed, list):
                    items = parsed
                elif isinstance(parsed, dict):
                    items = [parsed]
            except Exception:
                pass
        elif suffix == ".parquet":
            pass  # skip parquet (needs pandas)
    except Exception:
        items = []
    return items


if __name__ == "__main__":
    print("🔬 Mirro Data Ingestion\n")
    scan_raw_data()
    print("\n✅ Готово")