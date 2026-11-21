# -*- coding: utf-8 -*-
"""Тесты графа понятий: рёбра не должны появляться из обрывков слов.

Слой упоминаний строится по вхождению русской подписи в русский текст
другого понятия. Ошибка здесь тихая: граф цел, но связи врут — «любовь
связана с забором», «массив с массой», потому что основа слова совпала
внутри чужой словоформы.
"""
import unittest

from algos import concept_graph


class TestLabelMatching(unittest.TestCase):
    """Шаблон упоминания смотрит на падежное окончание, а не на любые буквы."""

    def test_different_word_is_not_a_form(self):
        # «забор» не должен находиться в «заботе»
        pattern = concept_graph._label_pattern("забор")
        self.assertFalse(pattern.search("любовь и забота о близких"))

    def test_case_form_matches(self):
        pattern = concept_graph._label_pattern("забота")
        self.assertTrue(pattern.search("любовь и забота о близких"))
        self.assertTrue(pattern.search("нужна забота близких"))
        self.assertTrue(pattern.search("живёт в заботе о семье"))

    def test_plural_and_adjective_forms_match(self):
        self.assertTrue(concept_graph._label_pattern("данные").search("структура данных"))
        self.assertTrue(concept_graph._label_pattern("функция").search("вызов функций"))
        self.assertTrue(concept_graph._label_pattern("масса").search("массы и объёмы"))

    def test_base_drops_trailing_vowels(self):
        self.assertEqual(concept_graph._label_base("данные"), "данн")
        self.assertEqual(concept_graph._label_base("забота"), "забот")


class TestEdges(unittest.TestCase):
    """Собранные рёбра указывают на настоящие понятия."""

    def test_known_edges_exist(self):
        self.assertIn("_список", concept_graph.neighbours("_массив"))
        self.assertIn("_алгоритм", concept_graph.neighbours("_стек"))

    def test_no_fence_edge_from_love(self):
        self.assertNotIn("_забор", concept_graph.neighbours("_любовь"))

    def test_no_mass_edge_from_array(self):
        self.assertNotIn("_масса", concept_graph.neighbours("_массив"))

    def test_edges_point_to_known_topics(self):
        from algos.module_knowledge import _KNOWLEDGE

        module_nodes = {"_" + str(entry.get("topic") or key).strip()
                        for key, entry in _KNOWLEDGE.items()}
        dangling = []
        for targets in concept_graph.EDGES.values():
            for target in targets:
                if target.startswith("_") and target not in module_nodes:
                    dangling.append(target)
        self.assertEqual(dangling[:5], [])


if __name__ == "__main__":
    unittest.main()
