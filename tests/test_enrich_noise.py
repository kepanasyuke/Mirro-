import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algos.knowledge_graph as kgm


class EnrichNoiseFilterTest(unittest.TestCase):
    """Мусорные корпусные связки не должны попадать в ответ про связи."""

    def setUp(self):
        self._original = kgm.kg
        self.graph = kgm.KnowledgeGraph()
        kgm.kg = self.graph

    def tearDown(self):
        kgm.kg = self._original

    def test_noisy_edges_are_skipped_in_enrich(self):
        self.graph.add_edge("понятие", "связано_с", "нейросеть", weight=1.0)
        self.assertEqual([], self.graph.enrich("понятие", max_hop=2))

    def test_noisy_only_graph_gives_no_answer(self):
        self.graph.add_edge("понятие", "связано_с", "нейросеть", weight=1.0)
        self.assertIsNone(kgm.try_enrich("что связано с понятие?"))
        self.assertIsNone(kgm.try_what_links("что связано с понятие?"))

    def test_meaningful_edge_survives(self):
        self.graph.add_edge("понятие", "отражает", "нейросеть", weight=1.0)
        answer = kgm.try_enrich("что связано с понятие?")
        self.assertIsNotNone(answer)
        self.assertIn("нейросеть", answer)

    def test_answer_has_no_junk_phrases(self):
        self.graph.add_edge("понятие", "связано_с", "нейросеть", weight=1.0)
        self.graph.add_edge("понятие", "отражает", "знание", weight=0.8)
        answer = kgm.try_enrich("что связано с понятие?") or ""
        self.assertNotIn("связано_с", answer)
        self.assertNotIn("нахожу в связях", answer)
        self.assertNotIn("понятие понятие", answer)

    def test_what_links_skips_noisy_predicate(self):
        self.graph.add_edge("понятие", "связано_с", "нейросеть", weight=1.0)
        self.graph.add_edge("понятие", "отражает", "знание", weight=0.8)
        lines = self.graph.what_links("понятие")
        joined = " ".join(lines)
        self.assertNotIn("связано_с", joined)
        self.assertIn("отражает", joined)


if __name__ == "__main__":
    unittest.main()
