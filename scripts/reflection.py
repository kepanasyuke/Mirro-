# -*- coding: utf-8 -*-
"""Mirro Reflection — самоанализ ошибок и автоулучшение знаний.

Читает провалы из data/qa_failures.jsonl (формат qa_watch: {ts, fails:[{q,note,answer}]})
и «рефлексирует»: за каждый провал, где ответ остался пустым/мусорным, подбирает
сильную связь из графа между ключевыми словами вопроса и УКРЕПЛЯЕТ её, чтобы
следующий раз понятие было связано лучше. Тихий — не падает при ошибках.

Запуск:
   python scripts/reflection.py            # разобрать последнюю пачку провалов
   python scripts/reflection.py --once     # разобрать и выйти (для cron/фона)
"""
import argparse
import json
import os
import re
import sys
import time
from pathlib import Path

MIRRO = Path(__file__).resolve().parent.parent
FAILURES = MIRRO / "data" / "qa_failures.jsonl"
REFLECTED = MIRRO / "data" / "reflection_log.jsonl"

_STOP = set(("и", "в", "на", "с", "по", "за", "от", "до", "из", "у", "для", "о",
             "не", "ни", "что", "как", "это", "то", "про", "мне", "меня", "ты",
             "я", "расскажи", "напиши", "какой", "какая", "какие", "такое", "объясни"))


def _words(text):
    return [w for w in re.findall(r"[а-яёa-z]{3,}", (text or "").lower()) if w not in _STOP]


def _last_failures(limit=200):
    """Собирает последние провалы из лога. Один return: list dict."""
    fails = []
    try:
        lines = FAILURES.read_text("utf-8").splitlines()
        for line in lines[-limit:]:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            for f in rec.get("fails", [])[:10]:
                fails.append({"question": f.get("q", ""), "note": f.get("note", ""),
                              "answer": f.get("answer", "")})
    except Exception:
        fails = []
    return fails


def _reinforce_graph(fail):
    """Укрепляет слабые связи графа по провальному вопросу.
    Берёт пару ключевых слов вопроса и усиливает их ребро (если существует),
    добавляя слово в граф. Один return: str (отчёт одной правки)."""
    note = ""
    try:
        sys.path.insert(0, str(MIRRO / "algos"))
        from knowledge_graph import kg
        words = _words(fail.get("question", ""))
        if len(words) >= 2:
            a, b = words[0], words[1]
            # если узел есть и связь есть — усиливаем (рефлексия: «это важно»)
            if a in kg.nodes and b in kg.nodes and kg.edge_weight(a, b) > 0:
                n = kg.reward(a, b, amount=0.15)
                note = f"усилил связь {a}↔{b} ({n})"
            elif a in kg.nodes and b in kg.nodes:
                # ребро ещё нет — добавляем слабое, но осмысленное
                kg.add_edge(a, "связано с", b, weight=0.3)
                note = f"связал {a}↔{b}"
            else:
                # понятия нет в графе — это сигнал, что тема слабо покрыта
                note = f"тема «{a}/{b}» вне графа — кандидат на пополнение"
        else:
            note = "мало ключевых слов для рефлексии"
        # персистентность: сохраняем изменения графа тихо
        try:
            kg.save(MIRRO / "models" / "knowledge_graph.pkl")
        except Exception:
            pass
    except Exception as e:
        note = f"ошибка рефлексии: {e}"
    return note


def run(limit=200):
    """Прогоняет рефлексию по последним провалам. Один return: int (правок)."""
    fails = _last_failures(limit)
    done = 0
    if fails:
        REFLECTED.parent.mkdir(parents=True, exist_ok=True)
        for f in fails:
            f["note"] = _reinforce_graph(f)
            try:
                with open(REFLECTED, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                         "question": f["question"][:120],
                                         "result": f["note"]}, ensure_ascii=False) + "\n")
            except Exception:
                pass
            done += 1
    return done


def main():
    ap = argparse.ArgumentParser(description="Рефлексия Mirro")
    ap.add_argument("--limit", type=int, default=200)
    ap.add_argument("--once", action="store_true", help="один прогон и выход")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    run(args.limit)
    print(f"Рефлексия: разобрано провалов — {_count_failures()}")
    if not args.once:
        # фоновый режим: крутится каждые 10 минут пока жив
        while True:
            time.sleep(600)
            run(args.limit)


def _count_failures():
    try:
        return sum(1 for _ in FAILURES.open("r", encoding="utf-8"))
    except Exception:
        return 0


if __name__ == "__main__":
    sys.exit(main())