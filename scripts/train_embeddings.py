# -*- coding: utf-8 -*-
"""Обучение PPMI-эмбеддингов на корпусе Mirro.

    python scripts/train_embeddings.py --limit 50000
    python scripts/train_embeddings.py --file data/processed/ru.jsonl --limit 200000

Результат — models/embeddings.json, который умеет читать algos/embeddings.py.
Никаких внешних библиотек: только json и чистый Python.
"""
import argparse
import json
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from algos import embeddings


def read_texts(path, limit):
    """Читает тексты из jsonl (поля instruction/output). Один return: list."""
    texts = []
    with path.open("r", encoding="utf-8", errors="ignore") as handle:
        for line in handle:
            if len(texts) >= limit:
                break
            try:
                record = json.loads(line)
            except ValueError:
                record = {}
            if isinstance(record, dict):
                parts = [record.get("instruction") or "", record.get("output") or ""]
                text = " ".join(part for part in parts if part)
                if text.strip():
                    texts.append(text)
    return texts


def main():
    parser = argparse.ArgumentParser(description="PPMI-эмбеддинги для Mirro")
    parser.add_argument("--file", default=str(ROOT / "data" / "processed" / "ru.jsonl"))
    parser.add_argument("--limit", type=int, default=50000)
    parser.add_argument("--window", type=int, default=2)
    parser.add_argument("--vocab", type=int, default=3000)
    parser.add_argument("--out", default=str(ROOT / "models" / "embeddings.json"))
    args = parser.parse_args()

    path = Path(args.file)
    if not path.exists():
        print(f"нет файла {path}")
        return 1
    started = time.time()
    texts = read_texts(path, args.limit)
    print(f"прочитано текстов: {len(texts)} за {time.time() - started:.1f}с")
    model = embeddings.train_from_texts(texts, window=args.window,
                                        max_vocab=args.vocab, min_count=2)
    print(f"слов в модели: {len(model['vectors'])}")
    saved = embeddings.save(model, Path(args.out))
    print(f"сохранено в {args.out}: {saved}, всего {time.time() - started:.1f}с")
    for first, second in (("кошка", "собака"), ("кошка", "алгоритм")):
        print(f"  близость {first}~{second}: {embeddings.similarity(model, first, second):.3f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
