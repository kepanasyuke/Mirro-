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
    Возвращает НОВЫЙ QState с нормированными Борн-векторами. Один return: QState.
    """
    from quantum_graph import QState
    out = QState()
    for name, (a, b) in qst.states.items():
        nb = abs(b) * (1.0 - decoherence_rate)
        if nb < floor:
            nb = 0.0
        mag = math.hypot(a, nb) or 1.0
        out.states[name] = (a / mag, nb / mag)
    return out


def check_phase_synchrony(qst, name_a, name_b):
    """Интерференционный член (скалярное произведение) состояний двух узлов.
    Для узлов отсутствующих в QState β=α=0 -> вклад 0. Один return: float."""
    a1, b1 = qst.get(name_a)
    a2, b2 = qst.get(name_b)
    return a1 * a2 + b1 * b2


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