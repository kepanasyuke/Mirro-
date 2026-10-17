# -*- coding: utf-8 -*-
"""
Mirro Trainer Bot — пакетная тренировка перцептрона на реальных примерах.
==========================================================================
Прогоняет выборку примеров базы, для каждого вопроса генерирует ответ текущей
моделью, сравнивает с эталоном и обучает перцептрон (лайк/дизлайк). В конце
сохраняет модель в model_state.json и печатает сводку по кластерам.

Запуск (строит/грузит индекс, тянет память — это ручной инструмент):
  python scripts/trainer_bot.py --cycles 500 --clusters ru,math --save
  python scripts/trainer_bot.py --cycles 200 --only-clean   # без сохранения

Опции:
  --cycles N          сколько примеров прогонять (по умолчанию 400)
  --clusters list     фильтр по кластерам, например ru,math (пусто = все)
  --save              записать обновлённую модель в models/model_state.json
  --threshold F       порог покрытия эталона для лайка (по умолчанию 0.3)
  --quiet             не печатать каждый пример
"""
import argparse
import json
import random
import sys
import time
from datetime import datetime as dt
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))


def run(cycles, clusters_filter, save, threshold, quiet):
    from scripts.algorithms import algo

    # Выборка примеров
    sample = algo.examples
    if clusters_filter:
        want = set(clusters_filter)
        sample = [e for e in sample if e[2] in want]
    if len(sample) > cycles:
        sample = random.sample(sample, cycles)
    sample = sample[:cycles]

    t0 = time.time()
    trained = 0
    good = 0
    by_cluster = {}
    for inst, out, cl in sample:
        if len(inst) < 8:
            continue
        ans = algo.compose_answer(inst, top_n=4)
        if not ans:
            continue
        ref_words = set(algo.tokenize(out))
        ans_words = set(algo.tokenize(ans))
        if not ref_words:
            continue
        coverage = len(ans_words & ref_words) / len(ref_words)
        label = 1 if coverage > threshold else -1
        if label == 1:
            good += 1
        algo.perceptron_train(inst, ans, label)
        algo.perceptron_trained = True
        trained += 1
        c = by_cluster.setdefault(cl, [0, 0])
        c[0] += 1
        if label == 1:
            c[1] += 1
        if not quiet and trained % 20 == 0:
            print(f"  ...{trained}/{len(sample)} обучено, точность {good/trained*100:.1f}%")

    elapsed = time.time() - t0
    acc = (good / trained * 100) if trained else 0.0
    print(f"\n[обучено] {trained} примеров за {elapsed:.1f}с")
    print(f"[точность] {good}/{trained if trained else 0} = {acc:.1f}% (порог покрытия {threshold})")
    print("[по кластерам]")
    for cl, (tot, hit) in sorted(by_cluster.items(), key=lambda x: -x[1][0]):
        print(f"    {cl:12} {tot:6d} примеров, хороших {hit:5d} ({hit/max(tot,1)*100:.0f}%)")

    if save:
        path = ROOT / "models" / "model_state.json"
        try:
            path.write_text(json.dumps({
                "perceptron_weights": algo.perceptron_weights,
                "perceptron_bias": algo.perceptron_bias,
                "perceptron_trained": algo.perceptron_trained,
                "trainer_cycles": trained,
                "trainer_accuracy": round(acc, 2),
                "trainer_clusters": {k: v[0] for k, v in by_cluster.items()},
                "updated": dt.utcnow().isoformat(),
            }, ensure_ascii=False, indent=2), "utf-8")
            print(f"[сохранено] {path}")
        except Exception as e:
            print(f"[ошибка сохранить модель] {e}")
    return trained


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Mirro Trainer Bot — тренировка перцептрона")
    ap.add_argument("--cycles", type=int, default=400, help="число примеров")
    ap.add_argument("--clusters", default="", help="фильтр кластеров: ru,math (пусто = все)")
    ap.add_argument("--save", action="store_true", help="сохранить модель")
    ap.add_argument("--threshold", type=float, default=0.3, help="порог лайка")
    ap.add_argument("--quiet", action="store_true", help="без детального вывода")
    args = ap.parse_args()
    clusters = [c.strip() for c in args.clusters.split(",") if c.strip()]
    print("MIRRO TRAINER BOT")
    sys.exit(0 if run(args.cycles, clusters, args.save, args.threshold, args.quiet) else 1)