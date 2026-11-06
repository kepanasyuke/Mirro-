# -*- coding: utf-8 -*-
"""Mirro Algorithms — 35 · Квантовый макро-резонанс (Wave Resonance)

Проблема: несколько волн активации от разных подграфов могут войти в противофазу
и полностью погасить друг друга (деструктивная интерференция) — сеть выдаёт пустой
ответ. Алгоритм принудительного резонанса выравнивает фазовые сдвиги связанных
роу-ссылок, заставляя их усиливать друг друга (конструктивная интерференция).

Совместим с реальными структурами Mirro:
  - ψ = (α, β) живут в QState (отдельный стораж, НЕ в Node.__slots__);
  - роу-ссылки живут в graph.meta_routes ({(from_edge, to_edge): mod}).

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import math

from quantum_graph import QState


def calculate_complex_phase(alpha, beta):
    """Угол фазы комплексного состояния (atan2). Один return: float."""
    return math.atan2(beta, alpha)


def _routes_of_graph(graph):
    """Роу-ссылки мета-графа (graph.meta_routes). Один return: dict."""
    return getattr(graph, "meta_routes", None) or {}


def try_align_quantum_phases(graph, qst, src_edge, tgt_edge, mod=1.0,
                             coupling_constant=0.12):
    """Синхронизирует фазы узлов целевого ребра под фазу узлов источника.

    src_edge/tgt_edge — ключи рёбер (src, pred, dst). Возвращает НОВЫЙ QState
    (чистая функция, не мутирует входной). Один return: QState.
    """
    new_states = dict(qst.states)
    if src_edge in graph.edges and tgt_edge in graph.edges:
        s_from, _p1, s_to = src_edge
        t_from, _p2, t_to = tgt_edge
        a_f, b_f = qst.get(s_from)
        phase_a = calculate_complex_phase(a_f, b_f)
        for node in (t_from, t_to):
            a, b = qst.get(node)
            phase_b = calculate_complex_phase(a, b)
            new_phase_b = phase_b + coupling_constant * (phase_a - phase_b) * mod
            new_states[node] = (math.cos(new_phase_b), math.sin(new_phase_b))
    out = QState()
    out.states = new_states
    return out


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.add_edge("a", "p", "b", 1.0)
    g.add_edge("b", "q", "c", 1.0)
    st = QState()
    st.states = {"a": (1.0, 0.0), "b": (0.0, 1.0), "c": (1.0, 0.0)}  # b сдвинут на π/2
    print("фаза b до:", round(calculate_complex_phase(0.0, 1.0), 4))
    st2 = try_align_quantum_phases(g, st, ("a", "p", "b"), ("b", "q", "c"),
                                   mod=1.0, coupling_constant=0.9)
    a, b = st2.get("c")
    print("фаза c после резонанса:", round(calculate_complex_phase(a, b), 4))