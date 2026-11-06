# -*- coding: utf-8 -*-
"""Юнит-тесты синаптического утомления и рефрактерности (algos/refractory.py).

Проверяем на РЕАЛЬНОМ KnowledgeGraph (старание НЕ ломает Node.__slots__):
  - init_refractory_counters заводит пустые счётчики;
  - нагрузка (activated_nodes + высокий вес ребра) повышает утомление и
    депрессирует активную проводимость ниже базового веса;
  - фаза покоя восстанавливает узел/ребро;
  - пайплайн try_route_pipeline принимает refractory_state без поломки.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.knowledge_graph import KnowledgeGraph
from algos.refractory import (
    init_refractory_counters, update_refractory_states, apply_fatigue_to_weights,
)
from algos.neural_electric import try_route_pipeline


def _graph():
    g = KnowledgeGraph()
    g.add_edge("n0", "p", "n1", 2.0)   # высокий вес — кандидат на утомление
    g.add_edge("n1", "p", "n0", 0.8)
    return g


class TestMirroRefractorySystem(unittest.TestCase):
    def test_init_counters(self):
        g = _graph()
        st = init_refractory_counters(g)
        self.assertEqual(len(st.node_fatigue), len(g.nodes))
        self.assertEqual(len(st.edge_exhaustion), len(g.edges))
        self.assertTrue(all(v == 0.0 for v in st.node_fatigue.values()))

    def test_fatigue_lowers_conductance(self):
        g = _graph()
        st = init_refractory_counters(g)
        # нагрузка на узел n0 + ребро веса 2.0 (>0.5) -> утомление растёт
        st2 = update_refractory_states(g, st, activated_nodes=["n0"], fatigue_rate=0.5)
        edge = ("n0", "p", "n1")
        self.assertGreater(st2.edge_exhaustion[edge], 0.0, "высокий ток должен истощать ребро")
        active = apply_fatigue_to_weights(g, st2)
        self.assertLess(active[edge], g.edges[edge],
                        "уставшее ребро обязано временно снизить проводимость")

    def test_recovery_in_rest(self):
        g = _graph()
        st = init_refractory_counters(g)
        st_loaded = update_refractory_states(g, st, activated_nodes=["n0"], fatigue_rate=0.5)
        st_rest = update_refractory_states(g, st_loaded, activated_nodes=[],
                                           recovery_rate=0.5)
        self.assertEqual(st_rest.node_fatigue["n0"], 0.0, "в покое узел восстанавливается")

    def test_pipeline_accepts_refractory(self):
        g = _graph()
        st = init_refractory_counters(g)
        r = try_route_pipeline(g, "Тест?",
                               chemistry={"acetylcholine": 1.0, "serotonin": 1.0, "dopamine": 0.1},
                               refractory_state=st)
        self.assertIn("signal", r)
        self.assertIsInstance(r["active_edges"], int)


if __name__ == "__main__":
    unittest.main()