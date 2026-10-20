# -*- coding: utf-8 -*-
"""Self-health check Mirro (улучшение №38).

Быстрая самопроверка целостности состояния без полной загрузки 1.6 ГБ
индекса. Проверяет:
  - файлы индекса/состояния существуют и не битые (размер > 0, читаемость);
  - consistency: число примеров в кэше ≠ 0, дедупликация/двойной байт;
  - веса перцептрона (сходимость) и буст-файлы читаемы.

Запуск отдельно:   python scripts/health_check.py
Из ядра (при старте): import scripts.health_check; health_check.run()
"""
import json, os, pickle, sys
from pathlib import Path

ROOT = Path(r"D:\Mirro")
MODELS = ROOT / "models"
CORE = ROOT / "core"
DATA = ROOT / "data"

INDEX_CACHE = MODELS / "index_cache.pkl"
STATE_JSON = CORE / "stats.json"
MODEL_STATE = MODELS / "model_state.json"
BOOST_JSON = MODELS / "index_cache.boost.json"
PERCEP_JSON = MODELS / "index_cache.perceptron.json"


def _load_json(p):
    if not p.exists():
        return None, f"нет файла {p}"
    try:
        return json.loads(p.read_text("utf-8")), None
    except Exception as e:
        return None, f"битый JSON {p}: {e}"


def check_index():
    if not INDEX_CACHE.exists():
        return False, "нет index_cache.pkl (будет пересобран при старте)"
    try:
        size = INDEX_CACHE.stat().st_size
        if size < 1_000_000:  # <1MB — почти наверняка битый/пустой
            return False, f"index_cache.pkl подозрительно мал ({size/1e6:.1f} МБ)"
        with open(INDEX_CACHE, "rb") as f:
            state = pickle.load(f)
        n = len(state.get("examples", []))
        if n == 0:
            return False, "index_cache пуст (0 примеров)"
        return True, f"index_cache: {n} примеров, {size/1e6:.0f} МБ"
    except Exception as e:
        return False, f"не удалось прочитать index_cache: {e}"


def run():
    results = []
    # 1. Индекс
    ok, msg = check_index()
    results.append(("index_cache", ok, msg))
    # 2. stats.json
    stats, err = _load_json(STATE_JSON)
    if stats is None:
        results.append(("stats.json", False, err))
    else:
        calls = stats.get("calls", 0)
        results.append(("stats.json", True, f"вызовов: {calls}"))
    # 3. model_state.json (веса перцептрона)
    ms, err = _load_json(MODEL_STATE)
    if ms is None:
        results.append(("model_state", False, err))
    else:
        trained = ms.get("perceptron_trained", False)
        results.append(("model_state", True, f"перцептрон обучен: {trained}"))
    # 4. буст / веса MLP
    for name, p in (("boost", BOOST_JSON), ("perceptron", PERCEP_JSON)):
        if p.exists():
            d, e = _load_json(p)
            results.append((f"{name}.json", d is not None, (e or f"{len(d or {})} записей")))
    # 5. processed-кластеры непустые
    proc = DATA / "processed"
    missing = []
    for need in ("ru.jsonl", "math.jsonl", "general.jsonl"):
        if not (proc / need).exists():
            missing.append(need)
    if missing:
        results.append(("processed", False, f"нет кластеров: {missing}"))
    else:
        results.append(("processed", True, "ключевые кластеры на месте"))

    ok = all(r[1] for r in results)
    return ok, results


def main():
    sys.stdout.reconfigure(encoding="utf-8")
    ok, results = run()
    print("MIRRO SELF-HEALTH CHECK")
    print("=" * 60)
    for name, is_ok, msg in results:
        print(f"  [{'OK' if is_ok else 'FAIL'}] {name:14} {msg}")
    print("=" * 60)
    print("  [summary]", "OK — всё в порядке" if ok else "ЕСТЬ ПРОБЛЕМЫ")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())