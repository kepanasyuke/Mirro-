"""Фоновый «бот», который постоянно гоняет QA-набор Mirro.

Каждый цикл: берёт до N кейсов, гоняет их по живому API, пишет сводку в
data/qa_report.jsonl (одинаковый формат с run_qa) и сравнивает с прошлым
прогоном для детекции деградации. Лог цикла — в data/qa_watch.log.

Запуск в фоне:
  python scripts/qa_watch.py --limit 300 --every 600
(300 кейсов на цикл, пауза 600 c между циклами — чтобы не грузить сервер.)

--once:  прогнать один цикл и выйти (удобно для проверки).
"""
import argparse
import json
import sys
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.run_qa import check_case, _server_up, graph_metrics

MIRRO = Path(__file__).resolve().parent.parent
REPORT = MIRRO / "data" / "qa_report.jsonl"
LOG = MIRRO / "data" / "qa_watch.log"


def log(msg):
    line = f"[{time.strftime('%Y-%m-%dT%H:%M:%S')}] {msg}"
    try:
        LOG.parent.mkdir(parents=True, exist_ok=True)
        with open(LOG, "a", encoding="utf-8") as fh:
            fh.write(line + "\n")
    except Exception:
        pass
    print(line, flush=True)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--limit", type=int, default=300)
    ap.add_argument("--every", type=int, default=600, help="пауза между циклами, c")
    ap.add_argument("--once", action="store_true", help="один цикл и выход")
    ap.add_argument("--workers", type=int, default=1,
                    help="параллельных бот-сессий: пул делится на N и гоняется одновременно")
    args = ap.parse_args()

    from tests.qa_cases import CASES as _HAND
    try:
        from tests.qa_generated import CASES as _GEN
    except Exception:
        _GEN = []
    pool = (_HAND + _GEN)[:args.limit if args.limit > 0 else None]
    n = max(1, args.workers)
    log(f"QA-watch запущен: пул {len(pool)} кейсов, {n} параллельных бот-сессий, интервал {args.every}s")

    last_ok = None
    code = 0
    stopped = False
    while not stopped:
        if not _server_up():
            log("сервер недоступен — жду следующего цикла")
            code = 1
            stopped = True if args.once else False
            if not stopped:
                time.sleep(args.every)
        else:
            results = _run_cycle(pool, n)
            if args.once and results is None:
                code = 1
                stopped = True
            else:
                passed = sum(1 for r in results if r["pass"])
                ok_rate = passed / len(results) if results else 0.0
                gm = graph_metrics()
                log(f"цикл ({n} cессий): {passed}/{len(results)} OK ({ok_rate:.0%}) | граф: {gm['edges']} рёбер, {gm['nodes']} узлов, плотность {gm['density']}")
                degraded = _degredation_flag(last_ok, ok_rate)
                if degraded:
                    log(f"  ⚠ падение точности: было {last_ok:.0%}, стало {ok_rate:.0%}")
                _write_report(results, ok_rate, degraded)
                last_ok = ok_rate
                log(f"  сводка: total={len(results)} passed={passed} degraded={bool(degraded)}")
                stopped = True if args.once else False
                if not stopped:
                    time.sleep(args.every)
    return code


def _run_cycle(pool, n):
    """Гоняет пул кейсов на n воркерах. Один return: list результатов или None."""
    chunks = [pool[i::n] for i in range(n)]
    results = []
    ok = True
    try:
        with ThreadPoolExecutor(max_workers=n) as ex:
            for chunk in chunks:
                results.extend(ex.map(check_case, chunk))
    except Exception as e:
        log(f"ошибка параллельного прогона: {e}")
        ok = False
    if not ok:
        results = None
    return results


def _degredation_flag(last_ok, ok_rate):
    """Признак деградации (заметное падение точности). Один return: str."""
    flag = ""
    if last_ok is not None and ok_rate < last_ok - 0.05:
        flag = " ДЕГРАДАЦИЯ"
    return flag


def _write_report(results, ok_rate, degraded):
    """Пишет сводку и провалы в data/. Один return: None."""
    passed = sum(1 for r in results if r["pass"])
    rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "total": len(results),
           "passed": passed, "ok_rate": round(ok_rate, 4),
           "degraded": bool(degraded), "failed": len(results) - passed}
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        with open(REPORT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass
    fails = [{"q": r["question"], "note": r["note"], "answer": r["answer"]}
             for r in results if not r["pass"]]
    if fails:
        try:
            (MIRRO / "data" / "qa_failures.jsonl").open("a", encoding="utf-8").write(
                json.dumps({"ts": rec["ts"], "fails": fails}, ensure_ascii=False) + "\n")
        except Exception:
            pass
    return None


if __name__ == "__main__":
    sys.exit(main())
