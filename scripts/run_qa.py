"""Непрерывный прогон QA-проверок Mirro (вопрос → ответ).

Гоняет набор пар из tests/qa_cases.py по живому API Mirro и выводит отчёт.
Режимы:
  * одноразово:            python scripts/run_qa.py
  * непрерывно (N сек):    python scripts/run_qa.py --every 600
Все проходят — exit 0; хоть один провал — exit 1 (удобно для cron/фонового).

Результаты дописываются в data/qa_report.jsonl (история прогонов).
"""
import json
import sys
import time
import urllib.request
import urllib.error
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from tests.qa_cases import CASES as _HAND
try:
    from tests.qa_generated import CASES as _GEN
except Exception:
    _GEN = []
CASES = (_HAND + _GEN)[:1000]

MIRRO = Path(__file__).resolve().parent.parent
REPORT = MIRRO / "data" / "qa_report.jsonl"
HOST, PORT, TOKEN = "127.0.0.1", 3443, "test-secret-123"
BASE = f"http://{HOST}:{PORT}"


def _server_up():
    up = False
    try:
        req = urllib.request.Request(
            BASE + "/health", method="GET",
            headers={"Authorization": "Bearer " + TOKEN})
        with urllib.request.urlopen(req, timeout=3) as resp:
            up = resp.status == 200
    except Exception:
        up = False
    return up


def ask(question):
    body = {"model": "mirro/default",
            "messages": [{"role": "user", "content": question}]}
    req = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + TOKEN},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    msg = (data.get("choices") or [{}])[0].get("message", {})
    return (msg.get("content") or "").strip().lower()


_JUNK_FRAGMENTS = ("вот что я нахожу в связях", "имеют общие понятия, подобие",
                   "я хотел", "насколько", "хочешь поиграть", "смотри намека",
                   "связано_с", "является ли предложение сложносочинённым")


def check_case(case):
    q = case["question"]
    answer = ask(q)
    min_len = case.get("min_len", 8)
    note = "ok"
    if len(answer) < min_len:
        note = f"короткий ответ (<{min_len})"
    elif case.get("forbid") and case["forbid"].lower() in answer:
        note = f"запрещённый мусор «{case['forbid']}»"
    elif case.get("expect") and case["expect"].lower() not in answer:
        note = f"не найдено ожидаемое «{case['expect']}»"
    else:
        note = _first_junk_note(answer)
    return {"question": q, "answer_len": len(answer),
            "pass": note == "ok", "note": note, "answer": answer[:200]}


def _first_junk_note(answer):
    """Первый мусорный паттерн в ответе (без break), строка-замечание.
    Один return: str."""
    found = [j for j in _JUNK_FRAGMENTS if j in answer]
    note = "ok"
    if found:
        note = f"мусорный паттерн «{found[0]}»"
    return note


def run_once():
    results = []
    if not _server_up():
        print(f"[QA] сервер Mirro недоступен на {BASE} — прогон пропущен")
    else:
        results = [check_case(c) for c in CASES]
        passed = sum(1 for r in results if r["pass"])
        print(f"[QA] {passed}/{len(results)} пройдено, {len(results)-passed} провалов")
        for r in results:
            mark = "OK " if r["pass"] else "FAIL"
            print(f"  [{mark}] {r['question']} | len={r['answer_len']} | {r['note']}")
    return results


def append_report(results):
    try:
        REPORT.parent.mkdir(parents=True, exist_ok=True)
        passed = sum(1 for r in results if r["pass"])
        rec = {"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
               "total": len(results), "passed": passed,
               "failed": len(results) - passed,
               "results": results}
        with open(REPORT, "a", encoding="utf-8") as fh:
            fh.write(json.dumps(rec, ensure_ascii=False) + "\n")
    except Exception:
        pass


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Прогон QA-проверок Mirro")
    ap.add_argument("--every", type=int, default=0,
                    help="непрерывно, пауза между прогонами в секундах (0=одноразово)")
    args = ap.parse_args()

    all_ok = True
    go = True
    while go:
        res = run_once()
        append_report(res)
        if res and not all(r["pass"] for r in res):
            all_ok = False
        if args.every <= 0:
            go = False
        else:
            time.sleep(args.every)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
