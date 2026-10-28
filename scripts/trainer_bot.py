# -*- coding: utf-8 -*-
"""
Mirro Trainer Bot — пакетная тренировка перцептрона на реальных примерах.
==========================================================================
Прогоняет выборку примеров базы, для каждого вопроса генерирует ответ текущей
моделью, сравнивает с эталоном и обучает перцептрон (лайк/дизлайк). В конце
сохраняет модель в model_state.json и печатает сводку по кластерам.

Структура: малые функции с единственным return (по соглашению проекта).

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

MODEL_STATE_PATH = ROOT / "models" / "model_state.json"


def _load_algo():
    """Подключает алгоритмы Mirro. Единственный return: экземпляр algo."""
    from scripts.algorithms import algo
    return algo


def _build_sample(algo, clusters_filter, cycles):
    """Выборка примеров с фильтром по кластерам и лимитом. Return: list."""
    sample = algo.examples
    if clusters_filter:
        want = set(clusters_filter)
        sample = [e for e in sample if e[2] in want]
    if len(sample) > cycles:
        sample = random.sample(sample, cycles)
    return sample[:cycles]


def _coverage(algo, inst, ans, out):
    """Какая доля слов эталона покрыта ответом. Один return: float (0..1) или None."""
    ref_words = set(algo.tokenize(out))
    ans_words = set(algo.tokenize(ans))
    cover = len(ans_words & ref_words) / len(ref_words) if ref_words else None
    return cover


def _label_for(coverage, threshold):
    """Метка обучения по покрытию. Return: int (1 или -1)."""
    return 1 if coverage > threshold else -1


def _train_one(algo, inst, ans, label):
    """Обучение перцептрона на одной паре. Return: bool (обучено)."""
    algo.perceptron_train(inst, ans, label)
    algo.perceptron_trained = True
    return True


def _answer_for(algo, inst):
    """Пытается получить ответ текущей моделью. Return: str или None."""
    return algo.compose_answer(inst, top_n=4)


def _new_cluster_stats():
    """Счётчик по кластерам. Return: dict кластер -> [всего, хороших]."""
    return {}


def _record_cluster(by_cluster, cluster, label, good_counter):
    """Фиксирует исход примера в статистике по кластерам. Один return: None."""
    c = by_cluster.setdefault(cluster, [0, 0])
    c[0] += 1
    if label == 1:
        c[1] += 1
        good_counter.append(True)
    return None


def _is_learnable(inst, ans):
    """Пропускаем ли пример (длина вопроса и наличие ответа). Return: bool."""
    return bool(inst and len(inst) >= 8 and ans)


def _maybe_progress(quiet, trained, sample_len, good):
    """Периодический вывод прогресса. Один return: None."""
    emit = (not quiet) and (trained % 20 == 0)
    if emit:
        pct = good * 100.0 / trained if trained else 0.0
        print(f"  ...{trained}/{sample_len} обучено, точность {pct:.1f}%")
    return None


def _print_summary(trained, good, elapsed, threshold, by_cluster):
    """Печать итоговой сводки. Return: None."""
    acc = (good * 100.0 / trained) if trained else 0.0
    print(f"\n[обучено] {trained} примеров за {elapsed:.1f}с")
    print(f"[точность] {good}/{trained} = {acc:.1f}% (порог покрытия {threshold})")
    print("[по кластерам]")
    for cl, (tot, hit) in sorted(by_cluster.items(), key=lambda x: -x[1][0]):
        pct = hit * 100.0 / max(tot, 1)
        print(f"    {cl:12} {tot:6d} примеров, хороших {hit:5d} ({pct:.0f}%)")
    return acc


def _save_model(algo, trained, acc, by_cluster):
    """Сохраняет модель в model_state.json. Один return: bool (успех)."""
    payload = {
        "perceptron_weights": algo.perceptron_weights,
        "perceptron_bias": algo.perceptron_bias,
        "perceptron_trained": algo.perceptron_trained,
        "trainer_cycles": trained,
        "trainer_accuracy": round(acc, 2),
        "trainer_clusters": {k: v[0] for k, v in by_cluster.items()},
        "updated": dt.utcnow().isoformat(),
    }
    try:
        MODEL_STATE_PATH.write_text(json.dumps(payload, ensure_ascii=False, indent=2), "utf-8")
        print(f"[сохранено] {MODEL_STATE_PATH}")
        ok = True
    except Exception as e:
        print(f"[ошибка сохранить модель] {e}")
        ok = False
    return ok


def run(cycles, clusters_filter, save, threshold, quiet):
    """Главный цикл тренировки. Единственный return: число обученных."""
    algo = _load_algo()
    sample = _build_sample(algo, clusters_filter, cycles)
    result = 0

    if sample:
        t0 = time.time()
        trained = 0
        good = 0
        good_events = []
        by_cluster = _new_cluster_stats()

        for inst, out, cl in sample:
            ans = _answer_for(algo, inst)
            if not _is_learnable(inst, ans):
                continue
            cov = _coverage(algo, inst, ans, out)
            if cov is None:
                continue
            label = _label_for(cov, threshold)
            _train_one(algo, inst, ans, label)
            _record_cluster(by_cluster, cl, label, good_events)
            good = len(good_events)
            trained += 1
            _maybe_progress(quiet, trained, len(sample), good)

        elapsed = time.time() - t0
        acc = _print_summary(trained, good, elapsed, threshold, by_cluster)
        if save:
            _save_model(algo, trained, acc, by_cluster)
        result = trained

    return result


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description="Mirro Trainer Bot — тренировка перцептрона")
    ap.add_argument("--cycles", type=int, default=400, help="число примеров")
    ap.add_argument("--clusters", default="", help="фильтр кластеров: ru,math (пусто = все)")
    ap.add_argument("--save", action="store_true", help="сохранить модель")
    ap.add_argument("--threshold", type=float, default=0.3, help="порог лайка")
    ap.add_argument("--quiet", action="store_true", help="без детального вывода")
    args = ap.parse_args()
    clusters = [c.strip() for c in args.clusters.split(",") if c.strip()]
    print("MIRRO TRAINER BOT (single-return structure)")
    sys.exit(0 if run(args.cycles, clusters, args.save, args.threshold, args.quiet) else 1)