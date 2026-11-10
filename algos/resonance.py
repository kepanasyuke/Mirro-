# -*- coding: utf-8 -*-
"""Mirro Algorithms — 28 · Волновой резонанс роу-связей (Wave Resonance)

Инновация: если два отдалённых участка графа «вибрируют» синхронно — их рёбра
имеют близкую активную проводимость (сходный «химический фон») — между ними
автоматически простраивается ВРЕМЕННАЯ мостовая роу-ссылка. Так сеть сама
эволюционирует топологию во время диалога, а не только по жёстким триплетам.

Работает поверх реального KnowledgeGraph:
    edges[(src, pred, dst)] -> weight;   роу-ссылки в graph.meta_routes.

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def calculate_vector_distance(vec_a, vec_b):
    """Евклидово расстояние между векторами. Разная длина → минимум по паре,
    хвост считается разницей. Один return: float."""
    if vec_a is None or vec_b is None:
        return 0.0
    dist = 0.0
    n = max(len(vec_a), len(vec_b))
    for i in range(n):
        a = vec_a[i] if i < len(vec_a) else 0.0
        b = vec_b[i] if i < len(vec_b) else 0.0
        dist += (a - b) ** 2
    return dist ** 0.5


def _edge_conductance(graph, key):
    """Активная проводимость ребра (текущий вес). Один return: float."""
    try:
        return float(graph.edges.get(key, 0.0))
    except Exception:
        return 0.0


def try_bridge_resonant_edges(graph, resonance_threshold=0.15):
    """Простраивает временные мостовые роу-ссылки между рёбрами с близкой
    активной проводимостью (резонанс). Пустой граф/некорректный порог → 0.
    Возвращает число созданных роу-ссылок. Один return: int."""
    if graph is None or not hasattr(graph, "edges") or resonance_threshold <= 0:
        return 0
    from neural_electric import add_meta_route
    edges_keys = list(graph.edges.keys())
    created = 0
    if len(edges_keys) < 2:
        return 0
    conduct = {k: _edge_conductance(graph, k) for k in edges_keys}
    pairs = []
    for i in range(len(edges_keys)):
        for j in range(i + 1, len(edges_keys)):
            a = conduct[edges_keys[i]]
            b = conduct[edges_keys[j]]
            if abs(a - b) < resonance_threshold:
                pairs.append((edges_keys[i], edges_keys[j]))
    for ea, eb in pairs:
        add_meta_route(graph, ea, eb, mod=0.35)
        created += 1
    return created


if __name__ == "__main__":
    print("расстояние (0.1,0.2)-(0.4,0.6):",
          round(calculate_vector_distance([0.1, 0.2], [0.4, 0.6]), 4))