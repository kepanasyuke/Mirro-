# -*- coding: utf-8 -*-
"""Юнит-тесты зеркального моделирования сознания (algos/mirror_cognition.py).

Проверяем на реальном KnowledgeGraph (рёбра edges[(s,p,d)]->w, нет dict-полей):
  - профиль реагирует на маркеры усталости и арт-фокуса;
  - зеркальная модуляция подавляет юмор/хаос при строгом ИТ-фокусе,
    а математическое ядро остаётся стабильным;
  - try_route_pipeline принимает зеркальную модуляцию без поломки.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.mirror_cognition import (
    init_mirror_profile, update_mirror_profile, apply_mirror_modulation_to_graph,
)
from algos.knowledge_graph import KnowledgeGraph


class TestMirroMirrorCognition(unittest.TestCase):
    def setUp(self):
        self.graph = KnowledgeGraph()
        self.graph.add_edge("математика", "ядро", "код", 1.0)
        self.graph.add_edge("шутка", "цепь", "юмор", 1.5)
        self.profile = init_mirror_profile()

    def test_intent_adaptation_to_art(self):
        prof = update_mirror_profile(self.profile, ["искусство", "театр", "дизайн"], 0.7)
        self.assertLess(prof["user_intent_focus"], 1.0, "арт-токены понижают ИТ-фокус")

    def test_fatigue_rises_on_short_longpulse(self):
        prof = update_mirror_profile(self.profile, ["да", "нет"], session_pulse=0.9)
        self.assertGreater(prof["user_fatigue"], 0.0, "короткий запрос при высоком пульсе → усталость растёт")

    def test_mirror_suppresses_humor_keeps_core(self):
        # строгий ИТ-запрос без арт-токенов: фокус остаётся высоким
        prof = update_mirror_profile(self.profile, ["написать", "функцию", "компиляции"], 0.7)
        mod = apply_mirror_modulation_to_graph(self.graph, prof)
        core_key = ("математика", "ядро", "код")
        humor_key = ("шутка", "цепь", "юмор")
        self.assertEqual(mod[core_key], self.graph.edges[core_key],
                         "математическое ядро должно оставаться стабильным")
        # юмор подавляется фокус-фактором (фокус ≤ 1.0, значит вес юмора не растёт)
        self.assertLessEqual(mod[humor_key], self.graph.edges[humor_key])

    def test_pipeline_accepts_mirror(self):
        from algos.neural_electric import try_route_pipeline
        r = try_route_pipeline(self.graph, "написать функцию?",
                               chemistry={"acetylcholine": 1.0, "serotonin": 1.0, "dopamine": 0.1})
        self.assertIn("signal", r)
        self.assertIn("active_edges", r)


if __name__ == "__main__":
    unittest.main()