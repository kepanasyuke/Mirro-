# -*- coding: utf-8 -*-
"""Фоновый «бот», который постоянно гоняет QA-набор Mirro.

Каждый цикл: берёт до N кейсов, гоняет их по живому API, пишет сводку в
data/qa_report.jsonl (одинаковый формат с run_qa) и сравнивает с прошлым
прогоном для детекции деградации. Лог цикла — в data/qa_watch.log.

Запуск в фоне:
  python scripts/qa_watch.py --limit 300 --every 600
(300 кейсов на цикл, пауза 600 c между циклами — чтобы не грузить сервер.)

--once:  прогнать один цикл и выйти (удобно для проверки).
"""
import argparse, json, sys, time
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from scripts.run_qa import ask, check_case, _server_up

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
    args = ap.parse_args()

    from tests.qa_cases import CASES as _HAND
    try:
        from tests.qa_generated import CASES as _GEN
    except Exception:
        _GEN = []
    pool = (_HAND + _GEN)[:args.limit if args.limit > 0 else None]
    log(f"QA-watch запущен: пул {len(pool)} кейсов, интервал {args.every}s")

    last_ok = None
    while True:
        if not _server_up():
            log("сервер недоступен — жду следующего цикла")
            if args.once:
                return 1
            time.sleep(args.every)
            continue
        results = [check_case(c) for c in pool]
        passed = sum(1 for r in results if r["pass"])
        ok_rate = passed / len(results) if results else 0.0
        log(f"цикл: {passed}/{len(results)} OK ({ok_rate:.0%})")
        # деградация: заметное падение точности относительно прошлого цикла
        degraded = ""
        if last_ok is not None and ok_rate < last_ok - 0.05:
            degraded = " ДЕГРАДАЦИЯ"
            log(f"  ⚠ падение точности: было {last_ok:.0%}, стало {ok_rate:.0%}")
        # сводка (без полных ответов, чтобы отчёт не раздулся)
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"), "total": len(results),
               "passed": passed, "ok_rate": round(ok_rate, 4),
               "degraded": bool(degraded), "failed": len(results) - passed}
        try:
            REPORT.parent.mkdir(parents=True, exist_ok=True)
            with open(REPORT, "a", encoding="utf-8") as fh:
                fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
        except Exception:
            pass
        # детальная выгрузка провалов в отдельный файл для диагностики
        fails = [{"q": r["question"], "note": r["note"], "answer": r["answer"]}
                 for r in results if not r["pass"]]
        if fails:
            try:
                (MIRRO / "data" / "qa_failures.jsonl").open("a", encoding="utf-8").write(
                    json.dumps({"ts": rec["ts"], "fails": fails}, ensure_ascii=False) + "\n")
            except Exception:
                pass
        last_ok = ok_rate
        log(f"  сводка: total={rec['total']} passed={rec['passed']} degraded={rec['degraded']}")
        if args.once:
            return 0
        time.sleep(args.every)


if __name__ == "__main__":
    sys.exit(main())