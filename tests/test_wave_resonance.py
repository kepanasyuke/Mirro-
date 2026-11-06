# -*- coding: utf-8 -*-
"""Юнит-тесты квантового макро-резонанса (algos/wave_resonance.py).

Проверяем на РЕАЛЬНЫХ структурах (QState для ψ, graph.meta_routes для роу-ссылок):
  - calculate_complex_phase считает atan2(β, α);
  - try_align_quantum_phases сближает фазы узлов целевого ребра с источником
    (конструктивная интерференция);
  - модуль нормирует состояние (|α|²+|β|²=1) после сдвига.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest, math
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import add_meta_route
from algos.quantum_graph import QState
from algos.wave_resonance import calculate_complex_phase, try_align_quantum_phases
from core.mirro_pinn_bridge import try_balance_quantum_pinn_state


def _graph_with_routed_edges():
    g = KnowledgeGraph()
    g.add_edge("src", "p", "a", 1.0)
    g.add_edge("a", "q", "b", 1.0)
    add_meta_route(g, ("src", "p", "a"), ("a", "q", "b"), mod=1.0)  # роу-ссылка
    return g


class TestMirroWaveResonance(unittest.TestCase):
    def test_complex_phase_math(self):
        self.assertAlmostEqual(calculate_complex_phase(0.0, 1.0), math.pi / 2, places=6)
        self.assertAlmostEqual(calculate_complex_phase(1.0, 0.0), 0.0, places=6)

    def test_phase_alignment_convergence(self):
        g = _graph_with_routed_edges()
        st = QState()
        st.states = {"src": (1.0, 0.0), "a": (0.0, 1.0), "b": (0.0, 1.0)}  # a,b сдвинуты на π/2
        before = calculate_complex_phase(*st.get("b"))
        st2 = try_align_quantum_phases(g, st, ("src", "p", "a"), ("a", "q", "b"),
                                       mod=1.0, coupling_constant=0.9)
        a, b = st2.get("b")
        after = calculate_complex_phase(a, b)
        # фаза цели должна сблизиться с фазой источника (0.0)
        self.assertLess(abs(after - 0.0), abs(before - 0.0))
        # норма вектора сохраняется
        self.assertAlmostEqual(a * a + b * b, 1.0, places=6)

    def test_no_route_keeps_states(self):
        g = KnowledgeGraph()
        g.add_edge("x", "p", "y", 1.0)   # без meta_routes
        st = QState()
        st.states = {"x": (1.0, 0.0), "y": (0.0, 1.0)}
        st2 = try_align_quantum_phases(g, st, ("x", "p", "y"), ("x", "p", "y"),
                                       mod=1.0, coupling_constant=0.5)
        self.assertEqual(st2.states["x"], (1.0, 0.0))

    def test_bridge_integrates_resonance(self):
        g = _graph_with_routed_edges()
        graph, _stable = try_balance_quantum_pinn_state(g, target_energy=0.5)
        self.assertEqual(len(graph.meta_routes), 1, "мост не должен ломать роу-ссылки")


if __name__ == "__main__":
    unittest.main()