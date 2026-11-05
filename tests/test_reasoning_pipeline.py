# -*- coding: utf-8 -*-
"""Интеграционные тесты сквозного мыслительного пайплайна (Reasoning Pipeline).

Покрывает всю цепочку роу-ссылок на РЕАЛЬНОМ KnowledgeGraph:
  биометрия → модулированные рёбра → роу-импульсы → PINN-физика → опыт → декодер
  + эволюционное скрещивание весов (scripts/evolve_weights.py).

Чистый Python, без numpy, атомарно.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import (
    compute_modulated_edges, propagate_meta_impulses, calculate_physics_loss,
    try_extract_biometric_context, try_route_pipeline, fire, hebbian_update_path,
    add_meta_route,
)
from algos.graph_infer import (
    try_get_memory_experience, generate_dynamic_inference, remember_pattern,
)
from scripts.evolve_weights import run as run_evolution, fitness


def _graph():
    g = KnowledgeGraph()
    g.from_triples([
        ("Внимание", "влияет на", "память"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
        ("Знание", "строится на", "понимание"),
    ])
    return g


class TestReasoningPipeline(unittest.TestCase):
    def test_biometric_context_from_query(self):
        bio = try_extract_biometric_context("Просто вопрос?")
        self.assertEqual(bio["gsr_stress"], 0.65, "вопросительный знак повышает GSR")
        bio2 = try_extract_biometric_context("Без знака")
        self.assertEqual(bio2["gsr_stress"], 0.40)

    def test_modulated_edges_change_with_chemistry(self):
        g = _graph()
        low = compute_modulated_edges(g, ach=0.5, serotonin=0.5, dopamine=0.0)
        high = compute_modulated_edges(g, ach=1.5, serotonin=1.5, dopamine=0.2)
        base = g.edges[("внимание", "влияет на", "память")]
        self.assertAlmostEqual(low[("внимание", "влияет на", "память")], base * 0.25, places=3)
        self.assertGreater(high[("внимание", "влияет на", "память")], base)

    def test_meta_impulses_amplify_following_edge(self):
        g = _graph()
        mod = compute_modulated_edges(g, ach=1.0, serotonin=1.0, dopamine=0.0)
        routed = propagate_meta_impulses(g, mod)
        first_w = mod[("внимание", "влияет на", "память")]
        second_after = routed[("память", "укрепляет", "понимание")]
        self.assertGreater(second_after, mod[("память", "укрепляет", "понимание")],
                           "роу-импульс от первого ребра должен усилить следующее")

    def test_physics_loss_positive_and_zero_on_empty(self):
        g = _graph()
        self.assertGreater(calculate_physics_loss(g, 0.6), 0.0)
        empty = KnowledgeGraph()
        self.assertEqual(calculate_physics_loss(empty, 0.6), 0.0)

    def test_route_pipeline_produces_answer(self):
        g = _graph()
        r = try_route_pipeline(g, "Как связаны внимание и знание?",
                               chemistry={"acetylcholine": 1.1, "serotonin": 0.9, "dopamine": 0.1})
        self.assertIsInstance(r["signal"], float)
        self.assertIsNotNone(r["answer"], "при малом rel-loss пайплайн должен выдать ответ")
        self.assertGreater(r["active_edges"], 0)

    def test_hebbian_feedback_strengthens_path(self):
        g = _graph()
        path = ["внимание", "память", "понимание"]
        before = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        hebbian_update_path(g, path, 1.0, learning_rate=0.03)
        after = [g.edge_weight(path[i], path[i + 1]) for i in range(len(path) - 1)]
        for b, a in zip(before, after):
            self.assertGreater(a, b, "лайк укрепляет рёбра пути")

    def test_memory_and_dynamic_inference(self):
        g = _graph()
        pat = [1.0, 1.0, 1.0, 1.0]
        self.assertEqual(try_get_memory_experience(g, pat), [0.0, 0.0, 0.0, 0.0],
                         "без опыта возвращается нулевой паттерн")
        remember_pattern(g, [0.9, 1.0, 0.8, 1.0])
        sig, integ = generate_dynamic_inference(g, [0.5, -0.2, 1.0, 0.8])
        self.assertIsInstance(sig, float)
        self.assertEqual(len(integ), len(g.edges))

    def test_evolution_improves_fitness(self):
        g = _graph()
        f0 = fitness(g, 0.6)
        rep = run_evolution(g, generations=10)
        f1 = fitness(g, 0.6)
        self.assertGreaterEqual(f1, f0, "эволюция не должна ухудшить fitness")
        self.assertGreaterEqual(rep["experience"], 1, "лучший паттерн должен уйти в память")

    def test_route_edge_suppresses_chaos_and_keeps_physics(self):
        """Ключевой интеграционный тест: точная связь через роу-ссылку с
        отрицательным mod подавляет проводимость хаотичного ребра («кашу»),
        при этом PINN-физика графа сохраняет энергию в норме."""
        g = KnowledgeGraph()
        g.from_triples([
            ("математика", "даёт", "чётки"),
            ("чётки", "запутывает", "хаос"),   # это «каша» — целевое подавление
        ])
        # роу-ссылка: точная математика (ребро 0) гасит хаотичное ребро 1
        e0 = ("математика", "даёт", "чётки")
        e1 = ("чётки", "запутывает", "хаос")
        add_meta_route(g, e0, e1, mod=-0.8)

        mod = compute_modulated_edges(g, ach=1.1, serotonin=0.95, dopamine=0.05)
        routed = propagate_meta_impulses(g, mod)

        chaos_before = mod[e1]
        chaos_after = routed[e1]
        self.assertLess(chaos_after, chaos_before,
                        "роу-ссылка должна подавить активный вес хаотичного ребра")
        self.assertAlmostEqual(chaos_after, chaos_before + mod[e0] * (-0.8), places=4)

        # PINN-цензор: энергия после модуляции остаётся валидной и конечной
        loss = calculate_physics_loss(g, target_energy=0.65)
        self.assertIsInstance(loss, float)
        self.assertGreaterEqual(loss, 0.0, "физический Loss не может быть отрицательным")
        self.assertLess(chaos_after, 1.0, "амплитуда подавленной «каши» ниже базовой")


if __name__ == "__main__":
    unittest.main()