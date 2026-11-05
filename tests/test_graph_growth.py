# -*- coding: utf-8 -*-
"""Интеграционные тесты роста понимания графа (0D → 1D → 2D → 3D).

Проверяем на РЕАЛЬНОМ KnowledgeGraph + роу-ссылках (graph.meta_routes):
  - изолированный узел = 0D;
  - прямые связи = линейная/плоская размерность (1D/2D);
  - добавление роу-ссылок мета-графа поднимает мерность к 3D;
  - средняя мера понимания сети растёт.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.zero_dimensional import (
    dimension_of, dimension_of_understanding, zero_dim_similarity,
)
from algos.neural_electric import add_meta_route


class TestMirroGraphEvolution(unittest.TestCase):
    def test_isolated_node_is_0d(self):
        g = KnowledgeGraph()
        g.add_node("A")
        dim, _deg = dimension_of(g, "A")
        self.assertEqual(dim, 0.0, "изолированный узел обязан быть 0D")

    def test_direct_edges_give_linear_dimension(self):
        g = KnowledgeGraph()
        g.from_triples([
            ("A", "связан с", "B"),
            ("A", "связан с", "C"),
            ("B", "связан с", "C"),
        ])
        dim_a, _deg_a = dimension_of(g, "A")
        dim_b, _deg_b = dimension_of(g, "B")
        # B имеет 2 связи — не ниже плоскостной меры
        iso = KnowledgeGraph()
        iso.add_node("X")
        dim_isolated = dimension_of(iso, "X")[0]
        self.assertGreater(dim_b, 0.0, "узел со связями не может оставаться 0D")
        self.assertEqual(dim_isolated, 0.0)

    def test_route_links_raise_dimension_to_3d(self):
        g = KnowledgeGraph()
        g.from_triples([
            ("A", "связан с", "B"),
            ("A", "связан с", "C"),
            ("B", "связан с", "C"),
        ])
        dim_before, _ = dimension_of(g, "A")
        # три роу-ссылки вокруг узла A => мета-зависимости => 3D
        add_meta_route(g, ("a", "связан с", "b"), ("a", "связан с", "c"), 0.5)
        add_meta_route(g, ("a", "связан с", "c"), ("a", "связан с", "b"), 0.5)
        add_meta_route(g, ("b", "связан с", "c"), ("a", "связан с", "b"), 0.5)
        dim_after, _ = dimension_of(g, "A")
        self.assertEqual(dim_after, 3.0, "узел с 3 роу-ссылками и связями — объёмный 3D")

    def test_understanding_metric_rises_with_routes(self):
        g = KnowledgeGraph()
        g.from_triples([
            ("A", "связан с", "B"),
            ("A", "связан с", "C"),
            ("B", "связан с", "C"),
        ])
        avg_before = dimension_of_understanding(g)
        add_meta_route(g, ("a", "связан с", "b"), ("a", "связан с", "c"), 0.5)
        add_meta_route(g, ("a", "связан с", "c"), ("a", "связан с", "b"), 0.5)
        add_meta_route(g, ("b", "связан с", "c"), ("a", "связан с", "b"), 0.5)
        avg_after = dimension_of_understanding(g)
        self.assertGreaterEqual(avg_after, avg_before,
                                "рост сети роу-ссылками не может понизить меру понимания")

    def test_zero_dim_similarity_still_works(self):
        g = KnowledgeGraph()
        g.from_triples([
            ("Вода", "содержит", "кислород"),
            ("Вода", "кипит при", "100"),
            ("Лёд", "содержит", "кислород"),
        ])
        sim = zero_dim_similarity(g, "вода", "лёд")
        self.assertGreater(sim, 0.0, "понятия с общим соседом (кислород) должны быть близки")


if __name__ == "__main__":
    unittest.main()