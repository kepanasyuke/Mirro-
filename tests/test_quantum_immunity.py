# -*- coding: utf-8 -*-
"""Юнит-тесты квантовой когерентности и иммунного стража.

Проверяем на РЕАЛЬНОМ KnowledgeGraph (не dict-API):
  - декогеренция подавляет мнимую составляющую и сохраняет норму Борна;
  - иммунный скан подавляет аномально разогнанные веса рёбер;
  - иммунный скан удаляет авто-резонансные петли роу-ссылок (meta_routes);
  - расширенный try_balance_quantum_pinn_state гасит аномалию и держит мета-петли
    пустыми.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import add_meta_route
from algos.quantum_graph import init_quantum_states
from algos.quantum_coherence import try_apply_decoherence_decay, check_phase_synchrony
from algos.immune_sentinel import run_graph_immune_scan
from core.mirro_pinn_bridge import try_balance_quantum_pinn_state


def _graph_with_anomaly():
    g = KnowledgeGraph()
    g.add_edge("a", "p", "b", 99.0)                 # аномально разогнанное ребро
    add_meta_route(g, ("a", "p", "b"), ("a", "p", "b"), 1.0)  # авто-петля
    return g


class TestMirroQuantumImmunity(unittest.TestCase):
    def test_decoherence_preserves_norm(self):
        g = KnowledgeGraph()
        g.add_node("x")
        st = init_quantum_states(g)
        st2 = try_apply_decoherence_decay(g, st, decoherence_rate=0.9)
        a, b = st2.get("x")
        self.assertAlmostEqual(a * a + b * b, 1.0, places=6, msg="норма Борна должна сохраняться")
        self.assertLess(b, 1.0 / 2 ** 0.5 + 1e-9, "мнимая часть должна затухать")

    def test_phase_synchrony_interference(self):
        g = KnowledgeGraph()
        g.add_node("a")
        g.add_node("b")
        st = init_quantum_states(g)
        # одинаковые состояния -> полное совпадение (интерференция ~ 1)
        inter = check_phase_synchrony(st, "a", "b")
        self.assertAlmostEqual(inter, 1.0, places=6)

    def test_immune_scan_suppresses_anomaly(self):
        g = _graph_with_anomaly()
        graph, quarantined = run_graph_immune_scan(g, max_allowed_weight=5.0)
        edge = ("a", "p", "b")
        self.assertIn(edge, quarantined, "аномальное ребро должно быть карантинировано")
        self.assertLess(graph.edges[edge], 10.0, "вес должен быть подавлен ×0.1")
        self.assertEqual(graph.meta_routes, {}, "авто-петля должна быть удалена")

    def test_balance_pipeline_integration(self):
        g = _graph_with_anomaly()
        graph, is_stable = try_balance_quantum_pinn_state(g, target_energy=0.5)
        edge = ("a", "p", "b")
        self.assertLess(graph.edges[edge], 10.0, "мост должен подавить аномальный вес")
        self.assertEqual(graph.meta_routes, {}, "мост должен вычистить авто-петлю")
        self.assertIsInstance(is_stable, bool)


if __name__ == "__main__":
    unittest.main()