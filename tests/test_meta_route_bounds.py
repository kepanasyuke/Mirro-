# -*- coding: utf-8 -*-
"""Тесты границ мета-графа (роу-ссылок): взрывной рост и обрезка.

Дефект, который здесь закреплён: try_bridge_resonant_edges перебирал ВСЕ пары
рёбер. На 200 рёбрах это 19 900 роу-ссылок за один шаг пайплайна
(core/mirro_pinn_bridge вызывает мост на каждом запросе) — квадратичный рост
памяти и времени вплоть до MemoryError на реальном графе.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import add_meta_route
from algos.resonance import (
    META_ROUTE_CAP, try_bridge_resonant_edges, prune_meta_routes, conductance_of,
)


def _chain(count, weight=0.8):
    """Цепочка из count рёбер с одинаковой проводимостью. Один return: граф."""
    graph = KnowledgeGraph()
    for i in range(count):
        graph.add_edge("n%d" % i, "p", "n%d" % (i + 1), weight)
    graph.meta_routes = {}
    return graph


class TestMetaRouteBounds(unittest.TestCase):
    def test_growth_is_linear_not_quadratic(self):
        graph = _chain(200)
        created = try_bridge_resonant_edges(graph)
        self.assertLessEqual(created, 400, "рост роу-ссылок обязан быть линейным по рёбрам")
        self.assertLess(len(graph.meta_routes), 20000, "полный перебор пар раздувает мета-граф")

    def test_meta_routes_respect_cap(self):
        graph = _chain(300)
        try_bridge_resonant_edges(graph, max_routes=50)
        self.assertLessEqual(len(graph.meta_routes), 50, "meta_routes не должен пробивать max_routes")

    def test_repeated_bridging_is_idempotent(self):
        graph = _chain(60)
        first = try_bridge_resonant_edges(graph)
        size = len(graph.meta_routes)
        second = try_bridge_resonant_edges(graph)
        self.assertGreater(first, 0)
        self.assertEqual(second, 0, "повторный шаг не должен дублировать те же роу-ссылки")
        self.assertEqual(len(graph.meta_routes), size)

    def test_bridging_skips_non_resonant_pairs(self):
        graph = KnowledgeGraph()
        graph.add_edge("a", "p", "b", 0.10)
        graph.add_edge("c", "p", "d", 0.90)
        created = try_bridge_resonant_edges(graph, resonance_threshold=0.15)
        self.assertEqual(created, 0, "разница проводимости 0.8 > порога — резонанса быть не должно")

    def test_prune_keeps_strongest_routes(self):
        graph = _chain(3)
        for i in range(10):
            add_meta_route(graph, ("n0", "p", "n1"), ("n%d" % i, "p", "n%d" % (i + 1)), mod=0.01 * i)
        add_meta_route(graph, ("n1", "p", "n2"), ("n2", "p", "n3"), mod=0.95)
        removed = prune_meta_routes(graph, cap=2)
        self.assertEqual(removed, len(graph.meta_routes) + removed - 2)
        self.assertEqual(len(graph.meta_routes), 2)
        self.assertIn(0.95, graph.meta_routes.values(), "должна выжить самая сильная роу-ссылка")

    def test_broken_graph_returns_zero(self):
        self.assertEqual(try_bridge_resonant_edges(None), 0)
        self.assertEqual(try_bridge_resonant_edges(object()), 0)
        self.assertEqual(try_bridge_resonant_edges(_chain(5), resonance_threshold=0), 0)
        self.assertEqual(prune_meta_routes(None), 0)

    def test_conductance_of_rejects_broken_weights(self):
        graph = KnowledgeGraph()
        graph.edges[("a", "p", "b")] = float("nan")
        graph.edges[("c", "p", "d")] = float("inf")
        graph.edges[("e", "p", "f")] = "битый вес"
        self.assertEqual(conductance_of(graph, ("a", "p", "b")), 0.0)
        self.assertEqual(conductance_of(graph, ("c", "p", "d")), 0.0)
        self.assertEqual(conductance_of(graph, ("e", "p", "f")), 0.0)


class TestPipelineDoesNotExplode(unittest.TestCase):
    def test_bridge_then_prune_cycle_stays_bounded(self):
        """Цикл «мост -> прунинг слабых» не должен накапливать мета-граф."""
        from scripts.synaptic_plasticity import clean_weak_meta_edges
        graph = _chain(150)
        for _step in range(5):
            try_bridge_resonant_edges(graph)
            clean_weak_meta_edges(graph)
        self.assertLess(len(graph.meta_routes), META_ROUTE_CAP + 1)


if __name__ == "__main__":
    unittest.main()
