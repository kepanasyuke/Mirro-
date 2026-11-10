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
    """Угол фазы комплексного состояния (atan2).
    Нулевые/нечисловые амплитуды → 0.0. Значения клампятся в ±[0,1].
    Один return: float."""
    try:
        a = max(-1.0, min(1.0, float(alpha)))
        b = max(-1.0, min(1.0, float(beta)))
    except Exception:
        return 0.0
    if a == 0.0 and b == 0.0:
        return 0.0
    result = math.atan2(b, a)
    return result if result == result else 0.0


def _routes_of_graph(graph):
    """Роу-ссылки мета-графа (graph.meta_routes). Пустой/None-граф → {}.
    Один return: dict."""
    if graph is None or not isinstance(getattr(graph, "meta_routes", None), dict):
        return {}
    meta = graph.meta_routes
    return dict(meta)


def try_align_quantum_phases(graph, qst, src_edge, tgt_edge, mod=1.0,
                             coupling_constant=0.12):
    """Синхронизирует фазы узлов целевого ребра под фазу узлов источника.

    src_edge/tgt_edge — ключи рёбер (src, pred, dst). Пустые граф/состояние,
    некорректные рёбра или битые пары состояний → неизменённая копия;
    coupling_constant и mod клампятся в [0,1]. Возвращает НОВЫЙ QState
    (не мутирует входной). Один return: QState.
    """
    if graph is None or qst is None or not getattr(qst, "states", None) \
        or not getattr(graph, "edges", None):
        return QState()
    try:
        coupling_constant = max(0.0, min(1.0, float(coupling_constant or 0.0)))
        mod = max(0.0, min(1.0, float(mod or 1.0)))
    except Exception:
        coupling_constant = 0.12
        mod = 1.0
    # NaN-защита: если получилось не-число — возвращаемся к дефолтам
    if coupling_constant != coupling_constant:
        coupling_constant = 0.12
    if mod != mod:
        mod = 1.0
    new_states = dict(qst.states)
    try:
        if src_edge in graph.edges and tgt_edge in graph.edges:
            # рёбра должны быть индексируемыми тройками (src, pred, dst)
            try:
                if len(src_edge) < 3 or len(tgt_edge) < 3:
                    raise ValueError("bad edge key")
            except TypeError:
                raise ValueError("bad edge key")
            s_from = src_edge[0]
            t_from = tgt_edge[0]
            src_pair = qst.get(s_from)
            if src_pair is None or not isinstance(src_pair, (tuple, list)) or len(src_pair) < 2:
                return qst
            a_f, b_f = src_pair
            phase_a = calculate_complex_phase(a_f, b_f)
            for node in (t_from, tgt_edge[2]):
                pair = qst.get(node)
                if pair is None or not isinstance(pair, (tuple, list)) or len(pair) < 2:
                    continue
                a, b = pair
                phase_b = calculate_complex_phase(a, b)
                new_phase_b = phase_b + coupling_constant * (phase_a - phase_b) * mod
                new_states[node] = (math.cos(new_phase_b), math.sin(new_phase_b))
    except Exception:
        new_states = dict(qst.states) if isinstance(qst.states, dict) else {}
    out = QState()
    out.states = dict(new_states) if isinstance(new_states, dict) else dict(qst.states)
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