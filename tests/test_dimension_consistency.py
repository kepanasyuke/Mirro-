# -*- coding: utf-8 -*-
"""Тесты согласованности метрик размерности и живучести мета-графа.

Дефекты, закреплённые здесь:
  - growth_report считал среднюю размерность только по степеням, а разбивку
    по уровням — через dimension_of. Отчёт мог одновременно говорить
    «средняя размерность 1.5» и «3D=1»: мета-граф в среднем не учитывался;
  - dimension_of / growth_report падали, если графу ни разу не назначали
    meta_routes, а в meta_routes содержались битые ключи;
  - массовая метрика по всем узлам перебирала весь мета-граф для каждого
    узла: на 20 000 рёбер — около 114 секунд (бюджет /health — доли секунды).

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, time, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.zero_dimensional import (
    dimension_of, dimension_of_understanding, growth_report,
)
from algos.neural_electric import add_meta_route


def _graph_with_routes():
    """Граф с тремя роу-ссылками вокруг узла A. Один return: граф."""
    graph = KnowledgeGraph()
    graph.from_triples([
        ("A", "связан с", "B"),
        ("A", "связан с", "C"),
        ("A", "связан с", "D"),
        ("B", "связан с", "C"),
    ])
    graph.meta_routes = {}
    add_meta_route(graph, ("a", "связан с", "b"), ("a", "связан с", "c"), mod=0.5)
    add_meta_route(graph, ("a", "связан с", "c"), ("a", "связан с", "d"), mod=0.5)
    add_meta_route(graph, ("a", "связан с", "d"), ("a", "связан с", "b"), mod=0.5)
    return graph


def _average_of_per_node(graph):
    """Среднее по dimension_of — эталон для отчёта. Один return: float."""
    dims = [dimension_of(graph, name)[0] for name in graph.nodes]
    return round(sum(dims) / len(dims), 2) if dims else 0.0


class TestDimensionConsistency(unittest.TestCase):
    def test_growth_report_average_matches_per_node_dimensions(self):
        graph = _graph_with_routes()
        expected = _average_of_per_node(graph)
        report = growth_report(graph)
        self.assertIn("средняя размерность %s" % expected, report,
                      "средняя в отчёте обязана считаться тем же dimension_of")
        self.assertGreater(expected, dimension_of_understanding(
            KnowledgeGraph()), "мета-граф должен поднимать среднюю меру")

    def test_understanding_metric_counts_routes(self):
        graph = _graph_with_routes()
        without_meta = KnowledgeGraph()
        without_meta.from_triples([(s, p, o) for (s, p, o) in graph.edges])
        self.assertGreater(dimension_of_understanding(graph),
                           dimension_of_understanding(without_meta),
                           "роу-ссылки обязаны отражаться в мере понимания")

    def test_report_ba_3d_bucket_affects_average(self):
        graph = _graph_with_routes()
        report = growth_report(graph)
        self.assertIn("3D=1", report)
        self.assertIn("средняя размерность %s" % _average_of_per_node(graph), report)


class TestMetaGraphSafety(unittest.TestCase):
    def test_missing_meta_routes_attribute(self):
        graph = KnowledgeGraph()
        graph.from_triples([("A", "p", "B"), ("A", "p", "C")])
        self.assertFalse(hasattr(graph, "meta_routes"))
        # два соседа — ещё не «плоскость» (2.0 требует трёх связей), главное — нет падения
        self.assertEqual(dimension_of(graph, "A"), (1.5, 2))
        self.assertIsInstance(growth_report(graph), str)

    def test_broken_meta_route_keys_are_skipped(self):
        graph = _graph_with_routes()
        graph.meta_routes[("мусор", 42)] = 1.0
        graph.meta_routes[("строка", ("a", "связан с", "b"))] = 1.0
        self.assertIsInstance(growth_report(graph), str)
        self.assertGreaterEqual(dimension_of_understanding(graph), 0.0)

    def test_empty_graph_has_no_division_by_zero(self):
        graph = KnowledgeGraph()
        self.assertEqual(dimension_of_understanding(graph), 0.0)
        self.assertIn("средняя размерность 0.0", growth_report(graph))

    def test_mass_metric_is_fast_on_large_graph(self):
        graph = KnowledgeGraph()
        for i in range(4000):
            graph.add_edge("n%d" % i, "p", "n%d" % (i + 1), 0.8)
        graph.meta_routes = {(("n0", "p", "n1"), ("n1", "p", "n2")): -0.3}
        started = time.time()
        dimension_of_understanding(graph)
        elapsed = time.time() - started
        self.assertLess(elapsed, 5.0,
                        "массовая метрика не должна перебирать мета-граф на каждый узел")


if __name__ == "__main__":
    unittest.main()
