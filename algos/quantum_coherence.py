# -*- coding: utf-8 -*-
"""Mirro Algorithms — 30 · Квантовая когерентность и декогеренция знаний

Физическая мотивация: если сеть слишком долго держит узел в суперпозиции ψ=α+iβ
без «измерения», её состояние рассинхронизируется со средой — источник
галюцинаций. Декогеренция плавно подавляет мнимую составляющую (β) и нормирует
вектор Борна, возвращая граф к классическому («реалистичному») базису.

Работает поверх QState (см. quantum_graph.py) — когерентность хранится отдельно,
НЕ трогая Node.__slots__. Узлы, у которых нет записи в QState, считаются
классическими (β=0).

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import math


def try_apply_decoherence_decay(graph, qst, decoherence_rate=0.08, floor=0.01):
    """Подавляет мнимую составляющую всех состояний QState (шум среды).
    Пустой граф/состояние или некорректная ставка/floor → нормированный QState
    (вырожденные векторы → |0>). Возвращает НОВЫЙ QState. Один return: QState.
    """
    from quantum_graph import QState
    out = QState()
    if graph is None or qst is None or not getattr(qst, "states", None):
        return out
    _ = graph  # параметр для совместимости сигнатуры; сам граф не меняем
    try:
        rate = max(0.0, min(1.0, float(decoherence_rate or 0.0)))
    except Exception:
        rate = 0.08
    try:
        floor = max(0.0, float(floor or 0.0))
    except Exception:
        floor = 0.01
    for name, pair in list(qst.states.items()):
        try:
            if not (isinstance(pair, (tuple, list)) and len(pair) >= 2):
                continue
            a = float(pair[0])
            nb0 = abs(float(pair[1]))
        except Exception:
            continue
        nb = nb0 * (1.0 - rate)
        if nb < floor:
            nb = 0.0
        mag = math.hypot(a, nb)
        if mag < 1e-12:
            out.states[name] = (1.0, 0.0)
            continue
        out.states[name] = (a / mag, nb / mag)
    return out


def check_phase_synchrony(qst, name_a, name_b):
    """Интерференционный член (скалярное произведение) состояний двух узлов.
    Для узлов отсутствующих в QState β=α=0, при None-qst или пустых узлах вклад 0.
    Один return: float."""
    if qst is None or not getattr(qst, "states", None):
        return 0.0
    if not name_a or not name_b:
        return 0.0
    a1, b1 = qst.get(name_a)
    a2, b2 = qst.get(name_b)
    try:
        return float(a1) * float(a2) + float(b1) * float(b2)
    except Exception:
        return 0.0


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    from quantum_graph import init_quantum_states
    g = KnowledgeGraph()
    g.add_node("внимание")
    g.add_node("память")
    st = init_quantum_states(g)          # ψ = (1/√2, 1/√2)
    st2 = try_apply_decoherence_decay(g, st, decoherence_rate=0.9)
    a, b = st2.get("внимание")
    print("после декогеренции: a=%.4f b=%.4f норм=%.4f" % (a, b, a*a + b*b))