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


if __name__ == "__main__":
    unittest.main()