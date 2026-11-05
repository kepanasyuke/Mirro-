# -*- coding: utf-8 -*-
"""Юнит-тесты совместной работы Хебб-модулятора роу-ссылок и логики графа.

Проверяем на РЕАЛЬНЫХ структурах Mirro (KnowledgeGraph + hebbian_update_path),
а не на иллюзорных GLOBAL_GRAPH/meta_edges из черновика:
  - лайк (+1) укрепляет рёбра активированного пути Хеббом;
  - дизлайк (−1) ослабляет их (анти-Хебб);
  - reward_sign (+1/−1) согласуется с обычным reward/punish;
  - edge_weight читает активный вес связи.

Чистый Python, без numpy, тесты не тяжёлые.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import hebbian_update_path, fire


def _graph():
    g = KnowledgeGraph()
    g.from_triples([
        ("Внимание", "влияет на", "память"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
    ])
    return g


class TestHebbianPathUpdatе(unittest.TestCase):
    def test_like_strengthens_path_edges(self):
        g = _graph()
        path = ["внимание", "память", "понимание"]
        before = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        res = hebbian_update_path(g, path, 1.0, learning_rate=0.02)
        after = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        self.assertEqual(res["strengthened"], 2, "лайк должен укрепить оба ребра пути")
        self.assertEqual(res["weakened"], 0)
        for b, a in zip(before, after):
            self.assertGreater(a, b, "вес ребра должен вырасти")

    def test_dislike_weakens_path_edges(self):
        g = _graph()
        path = ["внимание", "память", "понимание"]
        before = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        res = hebbian_update_path(g, path, -1.0, learning_rate=0.05)
        after = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        self.assertEqual(res["weakened"], 2, "дизлайк должен ослабить оба ребра")
        for b, a in zip(before, after):
            self.assertLess(a, b, "вес ребра должен уменьшиться")

    def test_like_then_dislike_returns_to_approx_original(self):
        g = _graph()
        path = ["внимание", "память", "понимание"]
        w0 = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        hebbian_update_path(g, path, 1.0, learning_rate=0.02)
        hebbian_update_path(g, path, -1.0, learning_rate=0.02)
        w1 = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        for a, b in zip(w0, w1):
            # Дельта Хебба масштабируется текущим весом, поэтому точного возврата
            # к исходному нет — допускаем небольшую погрешность асимметрии.
            self.assertAlmostEqual(a, b, places=3)

    def test_reward_sign_matches_reward_punish(self):
        g = _graph()
        wa = g.edge_weight("внимание", "память")
        g.reward_sign("внимание", "память", +1.0, amount=0.1)
        wb = g.edge_weight("внимание", "память")
        self.assertGreater(wb, wa, "reward_sign +1 повышает вес")
        g.reward_sign("внимание", "память", -1.0, amount=0.1)
        wc = g.edge_weight("внимание", "память")
        self.assertLess(wc, wb, "reward_sign -1 понижает вес")

    def test_path_from_actual_fire(self):
        g = _graph()
        chain = fire(g, "внимание")
        path = [n for n, _h, _v in chain]
        self.assertGreaterEqual(len(path), 2, "импульс должен активировать путь")
        res = hebbian_update_path(g, path, 1.0)
        self.assertGreaterEqual(res["updated"], 1, "лагодя реальному пути рёбра обновляются")


if __name__ == "__main__":
    unittest.main()