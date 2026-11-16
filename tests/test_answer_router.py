# -*- coding: utf-8 -*-
"""Тесты ранжирования ответов по уверенности.

Проверяют, что выбор зависит от смысла вопроса, а не от порядка источников:
определение выигрывает у связей, связи — у определения в вопросах про связи,
а на несуществующее понятие ответа нет вовсе.
"""
import unittest

from algos.answer_router import candidates, choose


class TestRouting(unittest.TestCase):
    """Выбор источника под тип вопроса."""

    def test_definition_wins_for_what_is(self):
        best = choose("что такое память")
        self.assertIsNotNone(best)
        self.assertEqual(best["source"], "definition")

    def test_relations_win_for_links_question(self):
        best = choose("с чем связана память")
        self.assertIsNotNone(best)
        self.assertEqual(best["source"], "relations")

    def test_relations_win_for_comparison(self):
        best = choose("что общего у дружбы и доверия")
        self.assertIsNotNone(best)
        self.assertEqual(best["source"], "relations")
        self.assertIn("дружба", best["content"].lower())

    def test_unknown_concept_has_no_answer(self):
        self.assertIsNone(choose("что такое кварковый резонатор"))

    def test_confidence_is_bounded(self):
        bad = [item for item in candidates("что такое мудрость")
               if not 0.0 <= item["confidence"] <= 1.0]
        self.assertEqual(bad, [])

    def test_candidates_are_ranked(self):
        found = candidates("что такое мудрость")
        scores = [item["confidence"] for item in found]
        self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == "__main__":
    unittest.main()
