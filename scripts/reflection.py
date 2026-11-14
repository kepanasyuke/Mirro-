# -*- coding: utf-8 -*-
"""Mirro Reflection — самоанализ ошибок и автоулучшение знаний.

Читает провалы из data/qa_failures.jsonl (формат qa_watch: {ts, fails:[{q,note,answer}]})
и «рефлексирует»: за каждый провал, где ответ остался пустым/мусорным, подбирает
сильную связь из графа между ключевыми словами вопроса и УКРЕПЛЯЕТ её, чтобы
следующий раз понятие было связано лучше. Если понятие, названное в вопросе,
в графе отсутствует — заводит его как помеченный узел-кандидат и связывает с
парой. Тихий — не падает при ошибках.

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
KG_MODEL = MIRRO / "models" / "knowledge_graph.pkl"

_STOP = set(("и", "в", "на", "с", "по", "за", "от", "до", "из", "у", "для", "о",
             "не", "ни", "что", "как", "это", "то", "про", "мне", "меня", "ты",
             "я", "расскажи", "напиши", "какой", "какая", "какие", "такое", "объясни",
             "который", "которая", "можно", "нужно", "все", "очень", "теперь", "где",
             "когда", "почему", "есть", "быть", "будет", "через", "между", "при"))

# слова-обёртки запроса: «что означает variance» давало «тема «означает/variance»»,
# хотя «означает» — не понятие, а связка. Такие в кандидаты не годятся.
_ASK_GLUE = set(("означает", "значит", "делает", "такое", "понятие", "понимать",
                 "отвечать", "работает", "зачем", "термин", "определение",
                 "объяснят", "расскажи", "покажи", "помоги", "хочу", "хотел"))


def _words(text):
    """Очищенные ключевые слова вопроса (дефисные термины склеиваем в одно).
    Один return: list[str]."""
    return [w for w in re.findall(r"[а-яёa-z]{3,}", re.sub(r"-", "", (text or "").lower()))
            if w not in _STOP]


def _subject_words(words):
    """Ключевые слова без слов-обёрток запроса («означает», «понятие»…).
    Один return: list[str]."""
    return [w for w in words if w not in _ASK_GLUE]


def _last_failures(limit=200):
    """Собирает последние провалы из лога, дедуплицируя одинаковые вопросы.
    Порог — ХОТЯ БЫ ОДНО ключевое слово: раньше здесь требовалось >=3 слов,
    а _reinforce_graph работает уже с двумя. В итоге «связал/пополнил» были
    мертвы: ни один вопрос с 1–2 словами не доходил до правки, и цикл
    рефлексия → граф не замыкался никогда (0 из 124 строк лога).
    Один return: list dict."""
    fails = []
    seen = set()
    try:
        lines = FAILURES.read_text("utf-8").splitlines()
        for line in lines[-limit:]:
            try:
                rec = json.loads(line)
            except Exception:
                continue
            for f in rec.get("fails", [])[:10]:
                q = f.get("q", "")
                if not q or not _words(q):
                    continue
                key = _words(q)
                if tuple(key) in seen:
                    continue
                seen.add(tuple(key))
                fails.append({"question": q, "note": f.get("note", ""),
                              "answer": f.get("answer", "")})
    except Exception:
        fails = []
    return fails


def _model_path():
    """Файл модели графа (меняется в тестах). Один return: Path."""
    return KG_MODEL


def _save_graph(kg, note):
    """Пишет граф на диск, только если правка реально изменила рёбра.
    НЕ перечитывает файл перед записью: load() стёр бы только что добавленные
    узлы-кандидаты и записал на диск прежний граф. Защита от затирания —
    проверка, что в памяти связей больше нуля. Один return: bool."""
    ok = False
    if kg.count_edges() > 0:
        ok = bool(kg.save(_model_path()))
    return ok


def _pick_pair(words):
    """Пара ключевых слов для правки: сначала связка из двух *понятий*
    (без слов-обёрток запроса), иначе первые два слова. Один return: tuple."""
    subject = _subject_words(words)
    pair = (subject[0], subject[1]) if len(subject) >= 2 else (words[0], words[1])
    return pair


def _reinforce_graph(fail):
    """Укрепляет слабые связи графа по провальному вопросу.
    Берёт пару ключевых слов вопроса и усиливает их ребро (если существует),
    добавляя слово в граф. Один return: str (отчёт одной правки)."""
    note = ""
    try:
        sys.path.insert(0, str(MIRRO / "algos"))
        from knowledge_graph import kg
        words = _words(fail.get("question", ""))
        if not words:
            return "мало ключевых слов для рефлексии"
        if len(words) >= 2:
            kg.load(_model_path())
            a, b = _pick_pair(words)
            # понятия нет в графе — заводим его как кандидата и связываем:
            # раньше такой провал лишь писал «кандидат на пополнение» и на этом
            # цикл обрывался — граф не получал НИЧЕГО
            outside = kg.still_outside(a, b)
            if outside:
                # в графе нет хотя бы одного понятия пары — заводим его как
                # узел-кандидат и связываем с парой: раньше такой провал лишь
                # писал «кандидат на пополнение», и граф не получал ничего
                added = kg.admit_candidate(a, b, weight=0.3)
                if added["edge_added"] or added["nodes_added"]:
                    note = f"пополнил {a}↔{b} (+{added['nodes_added']} узлов)"
            elif kg.edge_weight(a, b) > 0:
                # если узел есть и связь есть — усиливаем (рефлексия: «это важно»)
                n = kg.reward(a, b, amount=0.15)
                note = f"усилил связь {a}↔{b} ({n})"
            else:
                # ребро ещё нет — добавляем слабое, но осмысленное
                kg.add_edge(a, "связано с", b, weight=0.3)
                note = f"связал {a}↔{b}"
            if note:
                _save_graph(kg, note)
        else:
            note = "мало ключевых слов для рефлексии"
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
            # считаем только реально выполненные правки графа
            if f["note"].startswith(("усилил", "связал", "пополнил")):
                done += 1
            try:
                with open(REFLECTED, "a", encoding="utf-8") as fh:
                    fh.write(json.dumps({"ts": time.strftime("%Y-%m-%dT%H:%M:%S"),
                                         "question": f["question"][:120],
                                         "result": f["note"]}, ensure_ascii=False) + "\n")
            except Exception:
                pass
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
