# -*- coding: utf-8 -*-
"""Mirro Algorithms — 24 · ТТЛ-извлечение знаний (Knowledge Extraction)

Инновация: из связного русского текста вытаскивает факты вида
  (СУБЪЕКТ, ПРЕДИКАТ, ОБЪЕКТ)  и складывает их в Знаниевый граф (21).

Это «кормит» граф автоматически, чтобы понимание росло без ручного ввода.
Реализовано на regex/шаблонах русского языка — без NN-моделей, лёгкое.

Шаблоны:
  «СУБЪЕКТ ПРЕДИКАТ ОБЪЕКТ»   (подлежащее сказуемое дополнение)
  «X является/это Y» → X —есть→ Y
  «X состоит из Y»   → X —состоит из→ Y
  «X, если Y»        → Y —условие→ X
"""
import re as _re, os, sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knowledge_graph import KnowledgeGraph


# ----- предикаты, которые реально добавляют понимание -----
_VERBS = [
    "является", "представляет собой", "это", "есть", "состоит из", "включает",
    "содержит", "порождает", "создаёт", "вызывает", "влияет на", "управляет",
    "относится к", "зависит от", "приводит к", "использует", "принадлежит",
    "находится в", "производит", "похож на", "противоположен", "часть",
]
_VERBS_RE = "|".join(sorted(map(_re.escape, _VERBS), key=len, reverse=True))

# Отфыртруем мусорные «слова»
_STOP = {"и", "это", "что", "как", "то", "а", "но", "в", "на", "по", "с", "для"}


def _clean(w):
    w = _re.sub(r"[^а-яёa-z0-9\s\-]", "", w.lower()).strip()
    return w


def _sentences(text):
    """Разбивка на предложения. Один return: list отфильтрованных коротких."""
    return [s.strip() for s in _re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 10]


def _match_triple(s):
    """Достаёт (subj,pred,obj) из предложения. Один return: tuple или None."""
    m = _re.search(rf"^(.+?)\s+({_VERBS_RE})\s+(.+)$", s, flags=_re.I)
    if not m:
        return None
    return (_clean(m.group(1)), _clean(m.group(2)), _clean(m.group(3)))


def _valid(triple, min_subj, min_obj):
    """Содержательные ли субъект и объект. Один return: bool."""
    subj, _pred, obj = triple
    subj_ok = len([w for w in subj.split() if w not in _STOP]) >= min_subj
    obj_ok = len([w for w in obj.split() if w not in _STOP]) >= min_obj
    return subj_ok and obj_ok


def extract(text, min_subj=1, min_obj=1):
    """Из текста строит список триплетов (subj, pred, obj). Один return: list."""
    triples = []
    if text and len(text) >= 8:
        for s in _sentences(text):
            triple = _match_triple(s)
            if triple and _valid(triple, min_subj, min_obj):
                triples.append(triple)
    return triples


def ingest_into(kg: KnowledgeGraph, text):
    """Извлекает триплеты и кладёт их в граф. Возвращает число добавленных."""
    tri = extract(text)
    return kg.from_triples(tri)


if __name__ == "__main__":
    sample = (
        "Нейрон является основой мозга. Мысль порождает понимание. "
        "Внимание влияет на память. Память зависит от внимания."
    )
    tril = extract(sample)
    print("извлечено:", tril)
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    n = ingest_into(g, sample)
    print(f"добавлено в граф: {n}")
    print(g.summary())
    print("путь мысль->память:", g.path("мысль", "память"))