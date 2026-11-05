# -*- coding: utf-8 -*-
"""Юнит-тесты комбинаторного ядра (algos/10_combinatorics.py).

Проверяем на реальных функциях:
  - generate_combinations (сочетания из n по k, без itertools);
  - evaluate_best_logical_tree (выбор стабильной пары концептов по
    минимальному отклонению энергии на реальном KnowledgeGraph).

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest, importlib.util
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# модуль называется 10_combinatorics.py (цифра в начале) — грузим через importlib,
# как это делает algos/think.load_module
_ALGO_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos")
_spec = importlib.util.spec_from_file_location("combinatorics", os.path.join(_ALGO_DIR, "10_combinatorics.py"))
_comb = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_comb)
generate_combinations = _comb.generate_combinations
evaluate_best_logical_tree = _comb.evaluate_best_logical_tree

from algos.knowledge_graph import KnowledgeGraph


class TestMirroCombinatorics(unittest.TestCase):
    def test_combinations_generation(self):
        """Сочетания из 4 по 2 = 6, без повторов и дублей одного элемента."""
        elements = ["n0", "n1", "n2", "n3"]
        result = generate_combinations(elements, 2)
        self.assertEqual(len(result), 6)
        self.assertIn(["n0", "n1"], result)
        self.assertIn(["n2", "n3"], result)
        for comb in result:
            self.assertEqual(len(set(comb)), len(comb), "в сочетании не должно быть повторов")

    def test_combinations_k_gt_n(self):
        result = generate_combinations(["a", "b"], 5)
        self.assertEqual(result, [], "k>n даёт пустое множество")

    def test_best_logical_tree_real_graph(self):
        """На реальном графе выбирает пару с минимальным отклонением энергии."""
        g = KnowledgeGraph()
        # связь не">"сигнал" с весом ~0.71 (0.71^2 ≈ 0.5 → минимальный хаос)
        g.add_edge("нейрон", "передаёт", "сигнал", 0.71)
        g.add_edge("сигнал", "формирует", "мысль", 1.9)
        best_pair, min_chaos = evaluate_best_logical_tree(
            g, ["нейрон", "сигнал", "мысль"], chaos_target=0.5)
        self.assertEqual(best_pair, ("нейрон", "сигнал"),
                         "нужна пара с весом, близким к √0.5")
        self.assertLess(min_chaos, 0.1)

    def test_best_logical_tree_no_links(self):
        g = KnowledgeGraph()
        g.add_node("a")
        g.add_node("b")
        g.add_node("c")
        pair, chaos = evaluate_best_logical_tree(g, ["a", "b", "c"])
        self.assertIsNone(pair, "без связей нет пары для логического дерева")
        self.assertEqual(chaos, 999.0)


if __name__ == "__main__":
    unittest.main()