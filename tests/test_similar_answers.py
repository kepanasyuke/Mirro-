import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algos.knowledge_graph as kgm


class SimilarAnswerTest(unittest.TestCase):
    """Ответ про подобие не должен звучать мусором и не должен выдумываться."""

    def setUp(self):
        self._original = kgm.kg
        self.graph = kgm.KnowledgeGraph()
        kgm.kg = self.graph

    def tearDown(self):
        kgm.kg = self._original

    def test_shared_neighbour_is_reported(self):
        self.graph.add_edge("альфа", "отражает", "общее")
        self.graph.add_edge("бета", "отражает", "общее")
        answer = kgm.try_similar("что общего у альфа и бета?") or ""
        self.assertIn("альфа", answer)
        self.assertIn("бета", answer)
        self.assertNotIn("подобие", answer)
        self.assertNotIn("имеют общие понятия, подобие", answer)

    def test_unrelated_pair_gives_no_answer(self):
        self.graph.add_edge("альфа", "отражает", "первое")
        self.graph.add_edge("бета", "отражает", "второе")
        self.assertIsNone(kgm.try_similar("что общего у альфа и бета?"))

    def test_direct_relation_is_reported_without_numbers(self):
        self.graph.add_edge("альфа", "порождает", "бета", weight=1.0)
        answer = kgm.try_similar("чем похожи альфа и бета?") or ""
        self.assertIn("напрямую связаны", answer)
        self.assertIn("порождает", answer)
        self.assertNotIn("подобие", answer)

    def test_plain_question_is_ignored(self):
        self.graph.add_edge("альфа", "отражает", "общее")
        self.graph.add_edge("бета", "отражает", "общее")
        self.assertIsNone(kgm.try_similar("расскажи про альфа"))


if __name__ == "__main__":
    unittest.main()
