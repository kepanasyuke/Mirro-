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
    """Евклидово расстояние между векторами на чистом Python. Один return: float."""
    return sum((a - b) ** 2 for a, b in zip(vec_a, vec_b)) ** 0.5


def _edge_conductance(graph, key):
    """Активная проводимость ребра (текущий вес). Один return: float."""
    return float(graph.edges.get(key, 0.0))


def try_bridge_resonant_edges(graph, resonance_threshold=0.15):
    """Простраивает временные мостовые роу-ссылки между рёбрами с близкой
    активной проводимостью (резонанс). Возвращает число созданных роу-ссылок.
    Один return: int."""
    from neural_electric import add_meta_route
    edges_keys = list(graph.edges.keys())
    created = 0
    for i in range(len(edges_keys)):
        for j in range(i + 1, len(edges_keys)):
            a = _edge_conductance(graph, edges_keys[i])
            b = _edge_conductance(graph, edges_keys[j])
            if abs(a - b) < resonance_threshold:
                add_meta_route(graph, edges_keys[i], edges_keys[j], mod=0.35)
                created += 1
    return created


if __name__ == "__main__":
    print("расстояние (0.1,0.2)-(0.4,0.6):",
          round(calculate_vector_distance([0.1, 0.2], [0.4, 0.6]), 4))