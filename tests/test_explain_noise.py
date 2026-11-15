import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algos.knowledge_graph as kgm


class ExplainNoiseTest(unittest.TestCase):
    """Объяснение понятия не должно состоять из корпусных связок."""

    def setUp(self):
        self.graph = kgm.KnowledgeGraph()

    def test_noisy_edges_only_gives_none(self):
        self.graph.add_edge("язык", "связано_с", "строк", weight=1.0)
        self.assertIsNone(self.graph.explain("язык"))

    def test_meaningful_edge_is_reported(self):
        self.graph.add_edge("язык", "отражает", "речь", weight=1.0)
        text = self.graph.explain("язык") or ""
        self.assertIn("отражает", text)
        self.assertIn("речь", text)

    def test_noisy_predicate_never_leaks(self):
        self.graph.add_edge("язык", "связано_с", "строк", weight=1.0)
        self.graph.add_edge("язык", "отражает", "речь", weight=1.0)
        text = self.graph.explain("язык") or ""
        self.assertNotIn("связано_с", text)

    def test_unknown_node_gives_none(self):
        self.assertIsNone(self.graph.explain("такого-узла-нет"))


if __name__ == "__main__":
    unittest.main()
