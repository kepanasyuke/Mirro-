# -*- coding: utf-8 -*-
"""Тесты устойчивости кристаллизации памяти к битому опыту.

Дефекты, закреплённые здесь:
  - calculate_centroid_vector падал IndexError на пустом списке векторов и
    TypeError на None-векторе внутри группы;
  - try_crystallize_experience падал TypeError, если в graph.experience
    оказывался None или строковый вектор (следы от ручного восстановления
    или от старого декодера): одна битая запись роняла свёртку всей памяти.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.memory_crystallization import (
    calculate_centroid_vector, try_crystallize_experience,
)


class FakeGraph:
    """Заглушка графа с атрибутом experience (как в модуле)."""


def _graph(experience):
    graph = FakeGraph()
    graph.experience = experience
    return graph


class TestCentroidSafety(unittest.TestCase):
    def test_empty_list_returns_empty(self):
        self.assertEqual(calculate_centroid_vector([]), [])

    def test_none_returns_empty(self):
        self.assertEqual(calculate_centroid_vector(None), [])

    def test_skips_broken_vectors(self):
        centroid = calculate_centroid_vector([None, [1.0, 3.0], ["a", "b"]])
        self.assertEqual(centroid, [1.0, 3.0], "битые векторы не должны участвовать")

    def test_ragged_vectors_padded_with_zeros(self):
        centroid = calculate_centroid_vector([[1.0, 2.0], [3.0]])
        self.assertEqual(centroid, [2.0, 1.0])


class TestCrystallizationSafety(unittest.TestCase):
    def test_none_among_duplicates_does_not_raise(self):
        graph = _graph([None, [1.0, 0.0], [1.0, 0.0]])
        crystals = try_crystallize_experience(graph, similarity_threshold=0.95)
        self.assertEqual(crystals, 2, "дубликаты сворачиваются, None остаётся как есть")
        self.assertIn(None, graph.experience)

    def test_string_vectors_do_not_raise(self):
        graph = _graph([["a"], ["a"], [1.0, 2.0]])
        self.assertEqual(try_crystallize_experience(graph), 3)

    def test_empty_vectors_do_not_raise(self):
        self.assertEqual(try_crystallize_experience(_graph([[], []])), 2)

    def test_experience_not_list_unchanged(self):
        graph = _graph("не список")
        self.assertEqual(try_crystallize_experience(graph), 0)

    def test_valid_experience_still_compresses(self):
        graph = _graph([[1.0, 0.5, 0.0], [1.0, 0.51, 0.0], [0.99, 0.5, 0.0], [0.0, 0.0, 1.0]])
        crystals = try_crystallize_experience(graph, similarity_threshold=0.95)
        self.assertEqual(crystals, 2)
        self.assertEqual(len(graph.experience), 2)


if __name__ == "__main__":
    unittest.main()
