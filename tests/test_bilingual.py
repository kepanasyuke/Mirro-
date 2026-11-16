import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algos.bilingual as bilingual
import algos.knowledge_graph as kgm


class TransliterationTest(unittest.TestCase):
    def test_common_loanwords(self):
        self.assertEqual(bilingual.transliterate("algorithm"), "алгоритм")
        self.assertEqual(bilingual.transliterate("graph"), "граф")
        self.assertEqual(bilingual.transliterate("photon"), "фотон")

    def test_aliases_point_to_topics(self):
        table = bilingual.build_aliases()
        self.assertEqual(table.get("алгоритм"), "algorithm")
        self.assertEqual(table.get("граф"), "graph")
        self.assertGreater(len(table), 50)


class ConceptLookupTest(unittest.TestCase):
    def test_russian_question_finds_topic(self):
        self.assertEqual(bilingual.find_concept("что такое алгоритм?"), "algorithm")

    def test_unknown_word_gives_none(self):
        self.assertIsNone(bilingual.find_concept("расскажи про кошку"))

    def test_english_question_is_not_ours(self):
        self.assertIsNone(bilingual.try_bilingual("what is algorithm"))


class BilingualAnswerTest(unittest.TestCase):
    def setUp(self):
        self._original = kgm.kg
        self.graph = kgm.KnowledgeGraph()
        self.graph.add_edge("алгоритм", "описывает", "порядок действий", weight=1.0)
        kgm.kg = self.graph

    def tearDown(self):
        kgm.kg = self._original

    def test_russian_answer_from_graph(self):
        answer = bilingual.try_bilingual("что такое алгоритм")
        self.assertIsNotNone(answer)
        self.assertIn("алгоритм", answer)

    def test_unknown_concept_falls_through(self):
        self.assertIsNone(bilingual.try_bilingual("расскажи про кошку"))


if __name__ == "__main__":
    unittest.main()
