# -*- coding: utf-8 -*-
"""
Mirro Corpus Extend — безопасная достройка большого корпуса.
=================================================================
Не перезаписывает существующие сегменты: определяет текущее число сегментов
в corpus_big/ и дописывает новые (продолжая нумерацию), пока не будет
достигнута цель по количеству примеров. Использует генераторы из gen_corpus.

Примеры:
  python scripts/extend_corpus.py --increment 1 --rag        # +1 млн и пересборка RAG
  python scripts/extend_corpus.py --million 12               # дотянуть до 12 млн
  python scripts/extend_corpus.py --increment 0.2            # +200 тыс., без RAG

Внимание: пересборка RAG (--rag) читает ВСЕ сегменты и может занять
десятки минут и гигабайты RAM — запускайте, когда ПК свободен.
"""
import argparse
import json
import random
import sys
import time
from collections import Counter
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

from scripts import gen_corpus  # noqa: E402  (используем его генераторы)
from scripts.gen_corpus import gen_math, gen_from_base, load_base_examples, OUT_DIR  # noqa: E402

PER_FILE = 200_000  # как в gen_corpus


def current_count():
    total = 0
    for f in sorted(OUT_DIR.glob("corpus-*.jsonl")):
        with open(f, encoding="utf-8", errors="replace") as fh:
            for _ in fh:
                total += 1
    return total


def next_segment_index():
    ns = [int(p.stem.split("-")[1]) for p in OUT_DIR.glob("corpus-*.jsonl")]
    return max(ns) + 1 if ns else 0


def extend(extra_lines, seed):
    base = load_base_examples()
    rng = random.Random(seed)
    seg_idx = next_segment_index()
    buf = []
    written = 0

    def flush():
        if not buf:
            return
        fname = OUT_DIR / f"corpus-{seg_idx:06d}.jsonl"
        with open(fname, "a", encoding="utf-8") as f:
            for entry in buf:
                f.write(json.dumps(entry, ensure_ascii=False) + "\n")
        buf.clear()

    t0 = time.time()
    while written < extra_lines:
        roll = rng.random()
        if roll < 0.60 and base:
            entry = gen_from_base(base, rng)
        elif roll < 0.85:
            entry = gen_math(rng)
        else:
            entry = gen_from_base(base, rng) if base else gen_math(rng)
        if entry is None:
            continue
        buf.append(entry)
        written += 1
        if written % PER_FILE == 0 or written == extra_lines:
            flush()
            seg_idx += 1
            speed = written / max(time.time() - t0, 0.001)
            print(f"  ...{written/1e6:.2f}M добавлено, {speed:.0f}/с, файлы до corpus-{seg_idx-1:06d}.jsonl")

    print(f"\n[готово] добавлено {written} примеров за {(time.time()-t0)/60:.1f} мин")
    print(f"[итого в корпусе] {current_count()} примеров")


def rebuild_rag():
    print("\n[RAG] пересборка двухуровневого индекса...")
    from scripts.rag import rag
    rag.rebuild_all()
    print("[RAG] готово")


def main():
    ap = argparse.ArgumentParser(description="Mirro Corpus Extend — достройка корпуса")
    grp = ap.add_mutually_exclusive_group(required=True)
    grp.add_argument("--increment", type=float, help="добавить N млн примеров")
    grp.add_argument("--million", type=float, help="дотянуть до N млн примеров")
    ap.add_argument("--rag", action="store_true", help="пересобрать RAG-индекс после генерации")
    ap.add_argument("--seed", type=int, default=7, help="seed генератора")
    args = ap.parse_args()

    cur = current_count()
    print(f"Текущий корпус: {cur} примеров")
    if args.million is not None:
        extra = int(args.million * 1_000_000) - cur
        if extra <= 0:
            print("Уже достигнута цель — ничего не делаю.")
            return
    else:
        extra = int(args.increment * 1_000_000)

    print(f"Достраиваю: +{extra} примеров (seed={args.seed})")
    extend(extra, args.seed)
    if args.rag:
        rebuild_rag()
    else:
        print("\nСовет: запустите с --rag, когда целевой объём корпуса готов "
              "(readbuild_all() прочитает всё с нуля).")


if __name__ == "__main__":
    main()