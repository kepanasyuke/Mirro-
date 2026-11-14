# -*- coding: utf-8 -*-
"""Юнит-тесты свёртывающей кристаллизации памяти (algos/memory_crystallization.py).

Проверяем на реальной структуре: опыт хранится как атрибут graph.experience
(а не dict-поле):
  - 3 сверхпохожих вектора сжимаются в 1 центроид-кристалл;
  - изолированный вектор сохраняется неизменным;
  - математика центроида верна;
  - число кристаллов ОК.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.memory_crystallization import (
    calculate_centroid_vector, try_crystallize_experience,
)
from algos.knowledge_graph import KnowledgeGraph


def _graph_with_experience(exp):
    g = KnowledgeGraph()
    g.experience = [list(v) for v in exp]
    return g


class TestMirroMemoryCrystallization(unittest.TestCase):
    def test_centroid_vector_math(self):
        vecs = [[1.0, 0.5, 0.0], [1.0, 0.51, 0.0], [0.99, 0.5, 0.0]]
        c = calculate_centroid_vector(vecs)
        self.assertAlmostEqual(c[0], (1.0 + 1.0 + 0.99) / 3, places=6)
        self.assertAlmostEqual(c[1], (0.5 + 0.51 + 0.5) / 3, places=6)
        self.assertAlmostEqual(c[2], 0.0, places=6)

    def test_crystallization_compression(self):
        g = _graph_with_experience([
            [1.0, 0.5, 0.0],
            [1.0, 0.51, 0.0],   # сверхпохожий 1
            [0.99, 0.5, 0.0],   # сверхпохожий 2
            [0.0, 0.0, 1.0],    # изолированный
        ])
        after = try_crystallize_experience(g, similarity_threshold=0.95)
        # 4 вектора -> 2 кристалла (1 центроид + 1 изолированный)
        self.assertEqual(after, 2)
        self.assertEqual(len(g.experience), 2)

    def test_few_experiences_unchanged(self):
        g = _graph_with_experience([[1.0, 0.2], [0.5, 0.9]])
        self.assertEqual(len(g.experience), 2)
        after = try_crystallize_experience(g, similarity_threshold=0.92)
        self.assertEqual(after, 2, "разные векторы не должны сворачиваться")

    def test_empty_experience_safe(self):
        g = KnowledgeGraph()   # без атрибута experience
        self.assertEqual(try_crystallize_experience(g), 0)


class TestCrystallizationSafety(unittest.TestCase):
    """Ни при каких входных данных кристалл не должен становиться пустым
    вектором и не должен ронять процесс.

    Найдено сверкой: при опыте из нулевых/пустых векторов _cosine_similarity
    давала 0/1e-8 = 0 (или NaN), центроид группы выходил нулевым или вектор
    терял длину; на не-числовых данных функция падала TypeError.
    """

    def test_zero_vectors_are_not_merged_into_zero(self):
        g = _graph_with_experience([[0.0, 0.0], [0.0, 0.0]])
        try_crystallize_experience(g, similarity_threshold=0.0)
        # нулевые векторы не схлопываются в один «пустой кристалл»
        self.assertEqual(len(g.experience), 2)
        for vec in g.experience:
            self.assertEqual(len(vec), 2, "длина вектора не должна меняться")

    def test_zero_vector_never_absorbs_realone(self):
        g = _graph_with_experience([[0.0, 0.0], [1.0, 0.0]])
        try_crystallize_experience(g, similarity_threshold=-1.0)
        self.assertEqual(len(g.experience), 2)

    def test_ragged_vectors_do_not_crash(self):
        g = _graph_with_experience([[1.0, 2.0], [1.0, 2.0, 3.0]])
        try_crystallize_experience(g, similarity_threshold=0.5)
        self.assertEqual(len(g.experience), 2)

    def test_non_numeric_and_empty_entries_survive(self):
        g = _graph_with_experience([[], ["a", "b"]])
        try_crystallize_experience(g, similarity_threshold=0.5)
        self.assertEqual(len(g.experience), 2)
        self.assertEqual(g.experience[0], [])

    def test_nan_vectors_not_merged(self):
        g = _graph_with_experience([[float("nan"), 1.0], [float("nan"), 1.0]])
        try_crystallize_experience(g, similarity_threshold=0.5)
        self.assertEqual(len(g.experience), 2)

    def test_normal_case_still_compresses(self):
        g = _graph_with_experience([[1.0, 0.5], [1.0, 0.51], [1.0, 0.52]])
        try_crystallize_experience(g, similarity_threshold=0.92)
        self.assertEqual(len(g.experience), 1)
        self.assertAlmostEqual(g.experience[0][0], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()