# -*- coding: utf-8 -*-
"""Тесты устойчивости нейро-электрического контура к битым данным.

Дефекты, закреплённые здесь:
  - compute_modulated_edges / try_route_pipeline падали трейсбеком, если хоть
    одно ребро графа имело нечисловой вес (после ручного восстановления из
    бэкапа такое встречается) — весь ответ запроса умирал;
  - add_meta_route принимал в meta_routes строку вместо ключа-тройки и mod=None
    (TypeError) или NaN, после чего propagate_meta_impulses отравлял NaN'ом все
    проводимости кадра;
  - calculate_physics_loss возвращал inf, а не числовой штраф.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import (
    add_meta_route, compute_modulated_edges, propagate_meta_impulses,
    calculate_physics_loss, try_route_pipeline,
)


def _graph_with_broken_weight():
    """Граф, где одно ребро имеет строковый вес. Один return: граф."""
    graph = KnowledgeGraph()
    graph.add_edge("a", "p", "b", 1.0)
    graph.edges[("z", "p", "y")] = "битый вес"
    return graph


class TestBrokenEdgeWeights(unittest.TestCase):
    def test_modulated_edges_survives_non_numeric_weight(self):
        modulated = compute_modulated_edges(_graph_with_broken_weight())
        self.assertIn(("a", "p", "b"), modulated)
        self.assertEqual(modulated[("z", "p", "y")], 0.0, "мусорный вес не должен течь в проводимость")

    def test_modulated_edges_skips_bad_edge_keys(self):
        graph = KnowledgeGraph()
        graph.edges["не тройка"] = 1.0
        self.assertEqual(compute_modulated_edges(graph), {})

    def test_pipeline_survives_non_numeric_weight(self):
        result = try_route_pipeline(_graph_with_broken_weight(), "привет")
        self.assertIsInstance(result["signal"], float)
        self.assertIsInstance(result["physics_loss"], float)

    def test_physics_loss_is_finite_for_infinite_weight(self):
        graph = KnowledgeGraph()
        graph.add_edge("a", "p", "b", 1.0)
        graph.edges[("i", "p", "j")] = float("inf")
        loss = calculate_physics_loss(graph)
        self.assertNotEqual(loss, float("inf"), "inf-вес должен давать числовой штраф")
        self.assertGreater(loss, 1.0)

    def test_physics_loss_empty_graph(self):
        self.assertEqual(calculate_physics_loss(KnowledgeGraph()), 0.0)
        self.assertEqual(calculate_physics_loss(None), 0.0)


class TestMetaRouteRegistration(unittest.TestCase):
    def setUp(self):
        self.graph = KnowledgeGraph()
        self.graph.add_edge("a", "p", "b", 1.0)
        self.graph.add_edge("b", "p", "c", 1.0)

    def test_rejects_non_edge_key(self):
        add_meta_route(self.graph, "abc", ("b", "p", "c"), mod=1.0)
        self.assertNotIn("abc", str(list(self.graph.meta_routes.keys())))

    def test_rejects_none_mod(self):
        add_meta_route(self.graph, ("a", "p", "b"), ("b", "p", "c"), mod=None)
        self.assertEqual(self.graph.meta_routes, {})

    def test_rejects_nan_and_inf_mod(self):
        add_meta_route(self.graph, ("a", "p", "b"), ("b", "p", "c"), mod=float("nan"))
        add_meta_route(self.graph, ("a", "p", "b"), ("b", "p", "c"), mod=float("inf"))
        self.assertEqual(self.graph.meta_routes, {})

    def test_accepts_valid_negative_mod(self):
        size = add_meta_route(self.graph, ("a", "p", "b"), ("b", "p", "c"), mod=-0.4)
        self.assertEqual(size, 1, "подавляющая роу-ссылка (mod<0) должна регистрироваться")
        self.assertEqual(self.graph.meta_routes[(("a", "p", "b"), ("b", "p", "c"))], -0.4)

    def test_list_key_is_stored_as_tuple(self):
        add_meta_route(self.graph, ["a", "p", "b"], ["b", "p", "c"], mod=0.5)
        self.assertIn((("a", "p", "b"), ("b", "p", "c")), self.graph.meta_routes)

    def test_propagation_stays_numeric(self):
        self.graph.meta_routes = {(("a", "p", "b"), ("b", "p", "c")): float("nan")}
        routed = propagate_meta_impulses(self.graph, {("a", "p", "b"): 1.0, ("b", "p", "c"): 1.0})
        self.assertEqual(routed[("b", "p", "c")], 1.0, "NaN-модуляция не должна портить проводимость")


if __name__ == "__main__":
    unittest.main()
