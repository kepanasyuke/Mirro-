# -*- coding: utf-8 -*-
"""Тест резонансного моста: algos/resonance + scripts/synaptic_plasticity +
core/mirro_pinn_bridge на РЕАЛЬНОМ KnowledgeGraph.

Проверяем три вещи:
  - резонанс простраивает мостовую роу-ссылку между рёбрами с близкой проводимостью;
  - прунинг удаляет мёртвую роу-ссылку (LTD по |mod| < порога);
  - мост балансирует энергию и сообщает стабильность.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import add_meta_route
from algos.resonance import calculate_vector_distance, try_bridge_resonant_edges
from scripts.synaptic_plasticity import clean_weak_meta_edges
from core.mirro_pinn_bridge import try_balance_quantum_pinn_state


class TestMirroResonanceBridge(unittest.TestCase):
    def setUp(self):
        self.graph = KnowledgeGraph()
        # два ребра с близкой активной проводимостью (0.80 и 0.82) — кандидаты на резонанс
        self.graph.add_edge("n0", "p", "n1", 0.80)
        self.graph.add_edge("n1", "p", "n0", 0.82)
        # мёртвая роу-ссылка с низким mod — должна быть прунена
        add_meta_route(self.graph, ("n0", "p", "n1"), ("n1", "p", "n0"), mod=0.01)

    def test_vector_distance(self):
        self.assertAlmostEqual(calculate_vector_distance([0.0, 0.0], [3.0, 4.0]), 5.0, places=6)

    def test_resonance_creates_route(self):
        created = try_bridge_resonant_edges(self.graph, resonance_threshold=0.15)
        # рёбра веса 0.80 и 0.82 -> разница 0.02 < 0.15 -> создаётся роу-ссылка
        self.assertGreaterEqual(created, 1)
        # роу-ссылка (from_edge, to_edge) -> mod добавлена в meta_routes
        self.assertTrue(hasattr(self.graph, "meta_routes") and self.graph.meta_routes,
                        "после резонанса в meta_routes должны появиться роу-ссылки")

    def test_pruning_removes_dead_route(self):
        # до прунинга есть мёртвая (0.01) + возможно резонансная (0.35)
        removed = clean_weak_meta_edges(self.graph, extinction_threshold=0.05)
        self.assertGreaterEqual(removed, 1, "мёртвая роу-ссылка с mod=0.01 должна быть удалена")

    def test_pinn_bridge_pipeline(self):
        graph, is_stable = try_balance_quantum_pinn_state(
            self.graph, target_energy=0.64, dopamine_level=0.5)
        # мёртвая роу-ссылка удалена прунингом; осталась(и) только с mod>=порог
        for key, mod in graph.meta_routes.items():
            self.assertGreaterEqual(abs(mod), 0.05)
        # стабильность определена булевым значением
        self.assertIsInstance(is_stable, bool)


if __name__ == "__main__":
    unittest.main()