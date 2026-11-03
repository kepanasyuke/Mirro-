# -*- coding: utf-8 -*-
"""Mirro Algorithms — 26 · Нульмерный граф (Zero-Dimensional Graph)

Инновация: понятие задано НЕ координатой, а ТОЛЬКО набором связей.
Это «точка нигде» (0D): у узла нет места, есть лишь его отношения к другим.
  - «описать узел» = перечислить его соседей и связь к ним;
  - «сравнить два узла» = сравнить их ПОЛЕ СОСЕДЕЙ (адрес в сети);
  - близость = доля пересечения окрестностей, а не совпадение слов.

Это реляционное мышление: «положение задано отношениями» (как задача трёх тел).
Лёгкий, без внешних библиотек; работает поверх knowledge_graph.
"""
from __future__ import annotations


def field_signature(kg, name, depth=1):
    """Возвращает «поле» узла: нормированное множество (сосед, направление).

    depth=1 — прямые соседи; depth=2 — соседи соседей (шире поле).
    Возвращает кортеж (sig_пары, sig_узлы): пары-связи и просто список соседних узлов.
    """
    neighbors = set(kg.neighbors(name))          # (pred, other, weight)
    pairs = set()
    nodes = set()
    for pred, other, _w in neighbors:
        pairs.add((other, pred))
        nodes.add(other)
    if depth >= 2:
        for _p, other, _w in neighbors:
            for p2, o2, _w2 in kg.neighbors(other):
                pairs.add((o2, "→" + p2))
                nodes.add(o2)
    return pairs, nodes


def overlap(a_set, b_set):
    """Доля пересечения двух полей (0..1). 0 — ничего общего, 1 — полное совпадение."""
    if not a_set or not b_set:
        return 0.0
    inter = len(a_set & b_set)
    return inter / max(len(a_set), len(b_set))


def zero_dim_similarity(kg, a, b, depth=1):
    """Нульмерная близость двух понятий: насколько совпадают их поля связей.

    Даже если слова разные — если их «окрестности» похожи, понятия близки.
    Считаем по совпадению соседних узлов (без предиката) — общее окружение.
    """
    _pa, na = field_signature(kg, a, depth)
    _pb, nb = field_signature(kg, b, depth)
    return overlap(na, nb)


def zero_dim_description(kg, name):
    """Описать понятие «нульмерно»: только через его связи, без «самого себя»."""
    nb = kg.neighbors(name)
    if not nb:
        return f"«{name}» — изолированная точка (нет связей, смысл ещё не развёрнут)."
    parts = [f"{p} → {o}" for p, o, _w in nb[:8]]
    return f"«{name}» определяют связи: {', '.join(parts)}."


def zero_dim_mind(kg):
    """Метафора нульмерного сознания: у сети нет «центра», есть распределённые связи.

    Возвращает строку-размышление о том, что смысл Мирро — в связях, а не в точке.
    """
    nodes = len(kg.nodes)
    edges = len(kg.edges)
    hub = None
    # найдём самый «связанный» узел — почти центр, но он лишь точка многих связей
    maxdeg = -1
    for n in kg.nodes:
        d = len(kg.neighbors(n))
        if d > maxdeg:
            maxdeg = d
            hub = n
    return (f"Нульмерное сознание: {nodes} точек, {edges} связей. "
            f"Даже «{hub}» — не центр, а точка ({maxdeg} связей); "
            f"смысл распределён в самих связях, а не в месте.")


def try_zero_dim(query):
    """Точка входа для try_*: отвечает на «что такое 0D/нульмерность», «сравни X и Y»,
    «опиши через связи». Возвращает строку или None."""
    q = (query or "").strip().lower()
    if any(w in q for w in ["00", "0d", "ноль мерности", "нульмерност", "нуль-мерност",
                            "нольмерност", "точка нигде", "без координат"]):
        return ("Нульмерность: точка без размера и места. Понятие задано не координатой, "
                "а связями. Я мыслю: смысл узла = его отношения к другим узлам графа (0D-точка).")
    if "что такое 0d" in q or "что такое нульмерност" in q:
        return zero_dim_mind(kg)
    return None


kg = None  # заполняется через set_kg из ядра


def set_kg(g):
    global kg
    kg = g


# ================= РОСТ РАЗМЕРНОСТЕЙ (0D→1D→2D→3D) =================
def dimension_of(kg, name):
    """Мера «размерности» понятия: насколько его смысл развёрнут в связях.

    0D — изолированная точка (нет связей);
    1D — одна цепочка (линия: понятие связано с немногими в ряд);
    2D — плоскость (много связей, есть ветвление);
    3D — «объём» (связи выходят за прямых соседей, образуя плотную сеть).
    Возвращает (dim, deg): размерность и степень узла.
    """
    deg = len(kg.neighbors(name))
    if deg == 0:
        return (0.0, 0)
    # учитываем связи «второго порядка» — насколько уходит вглубь
    _p, nodes1 = field_signature(kg, name, depth=1)
    _p, nodes2 = field_signature(kg, name, depth=2)
    reach2 = len(nodes2)           # сколько узлов достижимо за 2 шага
    # эвристика: от 0D к 3D
    if deg == 1:
        dim = 1.0 if reach2 >= 1 else 0.5
    elif reach2 >= deg * 1.5:
        dim = 3.0
    elif deg >= 3:
        dim = 2.0
    else:
        dim = 1.5
    return (dim, deg)


def dimension_of_understanding(kg):
    """Общая мера «роста понимания» всей сети: средняя размерность узлов.

    От 0 (всё изолировано) до 3 (плотная сеть смыслов). Показывает, насколько
    Мирро «развернула» знания от точек-0D к связной сети.
    """
    if not kg.nodes:
        return 0.0
    import math
    dims = [dimension_of(kg, n)[0] for n in kg.nodes]
    avg = sum(dims) / len(dims)
    return round(avg, 2)


def growth_report(kg):
    """Текстовый отчёт о росте размерностей: сколько узлов на каждом уровне."""
    buckets = {"0D": 0, "1D": 0, "2D": 0, "3D": 0}
    for n in kg.nodes:
        d, deg = dimension_of(kg, n)
        b = "0D" if d < 0.75 else ("1D" if d < 1.5 else ("2D" if d < 2.5 else "3D"))
        buckets[b] += 1
    avg = dimension_of_understanding(kg)
    return (f"Рост понимания: средняя размерность {avg} из 3. "
            f"Узлы: " + ", ".join(f"{k}={v}" for k, v in buckets.items()) + ".")


def try_growth(query):
    """Точка входа для try_*: отвечает на вопрос про рост понимания/размерность."""
    q = (query or "").strip().lower()
    if any(w in q for w in ["рост понимания", "размерност", "сколько у тебя размерно",
                            "уровень понимания", "как глубоко ты понимаешь"]):
        if kg is not None:
            return growth_report(kg)
        return "Граф ещё не наполнен — не могу измерить рост понимания."
    if "какая размерность у" in q:
        name = q.replace("какая размерность у", "").strip().rstrip("?")
        if name and kg is not None:
            d, deg = dimension_of(kg, name)
            return f"«{name}»: размерность {d} из 3, связей {deg}."
    return None


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.from_triples([
        ("Вода", "кипит при", "100 градусов"),
        ("Земля", "вращается вокруг", "Солнце"),
        ("Луна", "вращается вокруг", "Земля"),
        ("Вода", "содержит", "кислород"),
        ("Растения", "выделяют", "кислород"),
        ("Люди", "дышат", "кислород"),
    ])
    set_kg(g)
    print(zero_dim_description(g, "вода"))
    print("близость вода~кислород:", round(zero_dim_similarity(g, "вода", "кислород"), 2))
    print("близость вода~земля:", round(zero_dim_similarity(g, "вода", "земля"), 2))
    print(zero_dim_mind(g))
    print(try_zero_dim("что такое нульмерность?"))