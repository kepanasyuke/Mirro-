# -*- coding: utf-8 -*-
"""Mirro Algorithms — 29 · Синаптическое утомление и рефрактерность

Защита от самовозбуждения (эпилептиформной активности графа весов): нейроны и
связи после мощной активации временно «устают» — активная проводимость падает,
затем восстанавливается. Это не даёт импульсам бесконечно циркулировать по
роу-ссылкам (взрыв градиентов / «каша»).

Важно: Node использует __slots__ и не хранит произвольные поля, поэтому утомление
держится в ОТДЕЛЬНОМ чистом сторадже RefractoryState (аналог quantum_graph.QState):
    node_fatigue: {имя_узла: 0..1}
    edge_exhaustion: {edge_key: 0..1}   (edge_key = (src, pred, dst))

Чистый Python, атомарные функции (один return), по LINTER.md.
"""


class RefractoryState:
    """Счётчики утомления узлов и рёбер графа. Отдельно от Node/edges."""
    def __init__(self):
        self.node_fatigue = {}     # name -> float
        self.edge_exhaustion = {}  # edge_key -> float


def init_refractory_counters(graph):
    """Инициализирует нулевые счётчики для всех узлов и рёбер.
    Пустой/некорректный граф → пустой стейт. Один return: RefractoryState."""
    st = RefractoryState()
    if graph is None or not hasattr(graph, "nodes") or not hasattr(graph, "edges") \
        or graph.nodes is None or graph.edges is None:
        return st
    for name in graph.nodes:
        st.node_fatigue[name] = 0.0
    for key in graph.edges:
        st.edge_exhaustion[key] = 0.0
    return st


def update_refractory_states(graph, st, activated_nodes=(), recovery_rate=0.1,
                             fatigue_rate=0.25):
    """Пересчитывает утомление узлов и рёбер за одну эпоху.
    Ставки клампятся в [0,1]; activated_nodes нормализуется в множество.
    None-граф или граф без edges → пустой стейт. Возвращает новый
    RefractoryState. Один return: RefractoryState."""
    if graph is None or not hasattr(graph, "edges") or not isinstance(graph.edges, dict) \
        or not hasattr(graph, "nodes"):
        return RefractoryState()
    try:
        recovery_rate = float(recovery_rate or 0.0)
        fatigue_rate = float(fatigue_rate or 0.25)
    except Exception:
        recovery_rate, fatigue_rate = 0.1, 0.25
    recovery_rate = max(0.0, min(1.0, recovery_rate)) if recovery_rate == recovery_rate else 0.1
    fatigue_rate = max(0.0, min(1.0, fatigue_rate)) if fatigue_rate == fatigue_rate else 0.25
    if st is None or not isinstance(st, RefractoryState):
        st = init_refractory_counters(graph)
    new_st = RefractoryState()
    if isinstance(activated_nodes, (list, tuple, set)):
        act = set(activated_nodes)
    else:
        act = set()
    for name in graph.nodes:
        try:
            cur = float(st.node_fatigue.get(name, 0.0) or 0.0)
        except Exception:
            cur = 0.0
        if name in act:
            new_st.node_fatigue[name] = min(1.0, cur + fatigue_rate)
        else:
            new_st.node_fatigue[name] = max(0.0, cur - recovery_rate)
    for key in graph.edges:
        try:
            cur = float(st.edge_exhaustion.get(key, 0.0) or 0.0)
        except Exception:
            continue
        try:
            w = abs(float(graph.edges.get(key, 0.0)))
        except Exception:
            continue
        if w > 0.5:
            new_st.edge_exhaustion[key] = min(1.0, cur + fatigue_rate * w)
        else:
            new_st.edge_exhaustion[key] = max(0.0, cur - recovery_rate)
    return new_st


def apply_fatigue_to_weights(graph, st, floor=0.2):
    """Временно депрессирует веса рёбер на основе их утомления.
    Если изначальный вес уже ниже floor — оставляем его как есть.
    Пустой/некорректный граф, None-стейт или floor<0 → {}; веса рёбер и
    exhaustion коерсируются в float. Возвращает dict без мутации графа.
    Один return: dict."""
    out = {}
    try:
        floor = float(floor)
    except Exception:
        floor = 0.2
    if floor != floor or floor in (float("inf"), float("-inf")):
        floor = 0.2
    if graph is None or not hasattr(graph, "edges") or not isinstance(graph.edges, dict) \
        or st is None or floor < 0:
        return out
    exhaust = getattr(st, "edge_exhaustion", None)
    if not isinstance(exhaust, dict):
        exhaust = {}
    for key, w in graph.edges.items():
        try:
            w = float(w)
        except Exception:
            continue
        try:
            exhaustion = float(exhaust.get(key, 0.0) or 0.0)
        except Exception:
            exhaustion = 0.0
        retention = max(0.0, 1.0 - 0.8 * exhaustion)
        fatigued = w * retention
        # не завышаем исходно малые веса и не увеличиваем при утомлении
        out[key] = fatigued if (w >= floor and fatigued >= floor) else w
    return out


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.add_edge("a", "p", "b", 2.0)
    st = init_refractory_counters(g)
    st2 = update_refractory_states(g, st, activated_nodes=["a"], fatigue_rate=0.5)
    active = apply_fatigue_to_weights(g, st2)
    print("вес до:", g.edges[("a", "p", "b")], "актив после утомления:", round(active[("a", "p", "b")], 4))