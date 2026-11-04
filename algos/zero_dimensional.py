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
    text = ""
    if not nb:
        text = f"«{name}» — изолированная точка (нет связей, смысл ещё не развёрнут)."
    else:
        parts = [f"{p} → {o}" for p, o, _w in nb[:8]]
        text = f"«{name}» определяют связи: {', '.join(parts)}."
    return text


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


_ZD_TRIGGERS = ["00", "0d", "ноль мерности", "нульмерност", "нуль-мерност",
                "нольмерност", "точка нигде", "без координат"]
_ZD_EXPLAIN = ("Нульмерность: точка без размера и места. Понятие задано не координатой, "
               "а связями. Я мыслю: смысл узла = его отношения к другим узлам графа (0D-точка).")


def _is_zd_question(q):
    """Есть ли в запросе триггер темы нульмерности. Один return: bool."""
    return any(w in q for w in _ZD_TRIGGERS)


def _is_zd_explain(q):
    """Просят ли объяснить нульмерность. Один return: bool."""
    return ("что такое 0d" in q) or ("что такое нульмерност" in q)


def try_zero_dim(query):
    """Точка входа для try_*: отвечает на «что такое 0D/нульмерность»."""
    q = (query or "").strip().lower()
    ans = None
    if _is_zd_question(q):
        ans = _ZD_EXPLAIN
    elif _is_zd_explain(q):
        ans = zero_dim_mind(kg)
    return ans


kg = None  # заполняется через set_kg из ядра


def set_kg(g):
    global kg
    kg = g


# ================= РОСТ РАЗМЕРНОСТЕЙ (0D→1D→2D→3D) =================
def _reach2(kg, name):
    """Сколько узлов достижимо за 2 шага (только для ЛОКАЛЬНОГО вызова,
    не в массовых метриках — там дорого на больших графах). Один return: int."""
    _p, nodes2 = field_signature(kg, name, depth=2)
    return len(nodes2)


def _dim_from_deg(deg, reach2):
    """Размерность по (степени, охвату 2-го порядка). Один return: float."""
    dim = 1.5
    if deg == 0:
        dim = 0.0
    elif deg == 1:
        dim = 1.0
    elif deg >= 3:
        dim = 2.0
    return dim


def dimension_of(kg, name):
    """Мера «размерности» понятия по его степени (без дорогого обхода 2-го
    порядка — корректно и быстро работает даже на графах в десятки тысяч узлов).
    0D — изолированная точка; 1D — цепочка; 2D — плоскость. Один return."""
    deg = len(kg.neighbors(name))
    dim = _dim_from_deg(deg, 0)
    return (dim, deg)


def dimension_of_understanding(kg):
    """Общая мера «роста понимания» всей сети: средняя размерность узлов.

    От 0 (всё изолировано) до 3. Быстрый подсчёт: один проход по узлам.
    Один return: float."""
    avg = 0.0
    if kg.nodes:
        degs = [len(kg.neighbors(n)) for n in kg.nodes]
        dims = [_dim_from_deg(d, 0) for d in degs]
        avg = round(sum(dims) / len(dims), 2)
    return avg


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


_GROWTH_TRIGGERS = ["рост понимания", "размерност", "сколько у тебя размерно",
                    "уровень понимания", "как глубоко ты понимаешь"]


def _is_growth_question(q):
    """Есть ли запрос на рост понимания. Один return: bool."""
    return any(w in q for w in _GROWTH_TRIGGERS)


def _node_dim_answer(q):
    """Ответ про размерность конкретного понятия. Один return: str или None."""
    name = q.replace("какая размерность у", "").strip().rstrip("?")
    ans = None
    if name and kg is not None:
        d, deg = dimension_of(kg, name)
        ans = f"«{name}»: размерность {d} из 3, связей {deg}."
    return ans


def try_growth(query):
    """Точка входа для try_*: отвечает на вопрос про рост понимания/размерность."""
    q = (query or "").strip().lower()
    ans = None
    if _is_growth_question(q):
        ans = growth_report(kg) if kg is not None else "Граф ещё не наполнен — не могу измерить рост понимания."
    elif "какая размерность у" in q:
        ans = _node_dim_answer(q)
    return ans


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