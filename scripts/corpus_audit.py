# -*- coding: utf-8 -*-
"""Mirro Corpus Audit — аналитика корпуса и пробелы знаний.

Читает живой индекс (scripts.algorithms.algo.examples) и строит отчёт:
  - всего/по кластерам примеров,
  - самые сильные темы (cluster с наибольшим числом примеров),
  - слабые области (клустеры/темы, которые РЕДКО отвечают относительно примеров),
  - пробелы знаний (понятия из графа, которые почти не имеют обучающих пар,
    и вопросы, на которые ответ не находился — из qa_failures).

Запуск:
   python scripts/corpus_audit.py            # сводка в консоль
   python scripts/corpus_audit.py --json     # JSON-отчёт для дашборда/API
"""
import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path

MIRRO = Path(__file__).resolve().parent.parent

# темы-домены для классификации вопроса по ключевым словам
_TOPIC_KEYWORDS = {
    "математика/алгоритмы": ("вычисл", "алгоритм", "сортир", "граф", "числ", "функци", "сложност"),
    "физика": ("физик", "энерги", "электрон", "атом", "скорост", "сил", "движени"),
    "биология": ("биолог", "клетк", "нейрон", "днк", "фотосинтез", "орган", "эволюци"),
    "химия": ("хими", "реакци", "молекул", "элемент", "кисл"),
    "космос": ("звезд", "планет", "галактик", "космос", "вселен", "черн", "орбит"),
    "программирование": ("python", "код", "функци", "перемен", "массив", "javascript", "sql", "def "),
    "наука об ИИ": ("нейросет", "машинн", "искусственн", "обучени", "перцептрон", "сеть"),
    "история/люди": ("истори", "кто такой", "биографи", "открыл", "изобр"),
    "финансы/налоги": ("налог", "деньг", "стоимост", "бюджет", "кредит", "вычет"),
    "естественные науки общие": ("природ", "веществ", "экосистема", "климат"),
}
_NUM_TOPICS = len(_TOPIC_KEYWORDS)


def _topic_of(text):
    """Классифицирует текст в одну из тем. Один return: str."""
    t = (text or "").lower()
    found = []
    for topic, kws in _TOPIC_KEYWORDS.items():
        if any(k in t for k in kws):
            found.append(topic)
    return found[0] if found else "прочее"


def audit(algo=None, limit_topic_scan=5000):
    """Строит отчёт по живому индексу. Один return: dict."""
    if algo is None:
        # импорт через локальный модуль algorithms (та же директория scripts)
        sys.path.insert(0, str(MIRRO / "scripts"))
        sys.path.insert(0, str(MIRRO))
        from scripts.algorithms import algo
    examples = getattr(algo, "examples", []) or []
    # 1. сводка по кластерам
    by_cluster = Counter(cl for _i, _o, cl in examples)
    # 2. тематический охват (по примерам вопроса; сканируем выборку)
    sample = examples[:: max(1, len(examples) // limit_topic_scan)][:limit_topic_scan]
    by_topic = Counter(_topic_of(inst) for inst, _o, _cl in sample)
    # 3. пробелы: темы, где мало примеров относительно среднего
    total = max(1, sum(by_topic.values()))
    avg_share = 1.0 / max(1, len(by_topic) or 1)
    gaps = {topic: round(cnt / total, 3) for topic, cnt in by_topic.items()
            if cnt / total < avg_share * 0.5}
    # 4. дубли: число одинаковых вопросов
    qs = [inst.lower().strip()[:100] for inst, _o, _cl in examples]
    dup = len(qs) - len(set(qs))
    # 5. слабые ответы из qa_failures (если есть) — темы, где чаще проваливаются
    fail_topic = Counter()
    try:
        fpath = MIRRO / "data" / "qa_failures.jsonl"
        if fpath.exists():
            for line in fpath.read_text("utf-8").splitlines()[-200:]:
                try:
                    rec = json.loads(line)
                except Exception:
                    continue
                for f in rec.get("fails", []):
                    fail_topic[_topic_of(f.get("q", ""))] += 1
    except Exception:
        pass

    return {
        "total_examples": len(examples),
        "vocab": len(getattr(algo, "vocab", [])) if hasattr(algo, "vocab") else None,
        "by_cluster": dict(by_cluster),
        "topic_coverage": dict(by_topic.most_common()),
        "topic_share": {t: round(c / total, 4) for t, c in by_topic.items()},
        "weak_topics": gaps,
        "duplicates": dup,
        "fail_topics": dict(fail_topic.most_common(6)),
        "strong_topics": [t for t, _ in by_topic.most_common(3)],
    }


def main():
    ap = argparse.ArgumentParser(description="Аналитика корпуса Mirro")
    ap.add_argument("--json", action="store_true")
    args = ap.parse_args()
    sys.stdout.reconfigure(encoding="utf-8")
    rep = audit()
    if args.json:
        print(json.dumps(rep, ensure_ascii=False, indent=1, default=str))
    else:
        print(f"Примеров всего: {rep['total_examples']}, словарь: {rep['vocab']}")
        print("По кластерам:", ", ".join(f"{k}={v}" for k, v in sorted(rep['by_cluster'].items(), key=lambda x: -x[1])))
        print("Сильные темы:", ", ".join(rep['strong_topics']))
        print("Слабые темы (пробелы):", ", ".join(rep['weak_topics'].keys()) or "нет")
        print("Дублей вопросов:", rep['duplicates'])
        print("Темы провалов:", ", ".join(rep['fail_topics']) or "нет")


if __name__ == "__main__":
    main()