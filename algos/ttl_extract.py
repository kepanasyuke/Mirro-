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
    # дополнения под математику/код
    "называется", "равно", "равняется", "решается", "представляет",
    "вычисляет", "возвращает", "принимает", "выражается через", "равен",
    "требует", "используется для", "решает", "определяет", "преобразует",
    "находит", "является аргументом", "соединяет", "усиливает", "ослабляет",
    "активирует", "улучшает", "ухудшает",
]
_VERBS_RE = "|".join(sorted(map(_re.escape, _VERBS), key=len, reverse=True))

# Шаблон условия: «если X, то Y» / «X, если Y»
_IF_RE = _re.compile(r"^(?:если|если бы)\s+(.+?)[,;]?\s+то\s+(.+)$", flags=_re.I)
_IF_POST_RE = _re.compile(r"^(.+?)[,;]?\s+если\s+(.+)$", flags=_re.I)

# Отфыртруем мусорные «слова» (служебные/связки)
_STOP = {
    "и", "это", "что", "как", "то", "а", "но", "в", "на", "по", "с", "для",
    "однако", "затем", "также", "который", "которая", "которые", "чтобы", "когда",
    "если", "при", "из", "от", "до", "за", "над", "под", "при этом", "при этом,",
    "то есть", "например", "именно", "только", "уже", "ещё", "тут", "там", "более",
    "менее", "сам", "сама", "сами", "весь", "все", "всё", "другой", "другая",
    "можно", "нужно", "надо", "это тот", "он", "она", "они", "мы", "вы", "этот",
}


def _clean(w):
    w = _re.sub(r"[^а-яёa-z0-9\s\-]", "", w.lower()).strip()
    return w


def _clean_sentence(s):
    """Чистит предложение от мусорных вводных. Один return: str."""
    return _re.sub(r"^(напиши|как|объясни|расскажи,?)\s+", "", s.strip())


def _match_condition(s):
    """Ловит «если X то Y»/«X если Y» -> (X, 'условие для', Y). Один return: tuple|None."""
    match = None
    m = _IF_RE.search(s)
    if m:
        cond, then = _clean(m.group(1)), _clean(m.group(2))
        if cond and then:
            match = (cond, "условие для", then)
    if match is None:
        m2 = _IF_POST_RE.search(s)
        if m2:
            then, cond = _clean(m2.group(1)), _clean(m2.group(2))
            if then and cond:
                match = (then, "если", cond)
    return match


def _sentences(text):
    """Разбивка на предложения. Один return: list отфильтрованных коротких."""
    return [s.strip() for s in _re.split(r"(?<=[.!?])\s+", text) if len(s.strip()) >= 10]


def _match_triple(s):
    """Достаёт (subj,pred,obj) из предложения. Один return: tuple или None."""
    triple = None
    m = _re.search(rf"^(.+?)\s+({_VERBS_RE})\s+(.+)$", s, flags=_re.I)
    if m:
        triple = (_clean(m.group(1)), _clean(m.group(2)), _clean(m.group(3)))
    return triple


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
        for raw in _sentences(text):
            s = _clean_sentence(raw)
            triple = _match_triple(s) or _match_condition(s)
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