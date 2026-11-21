# -*- coding: utf-8 -*-
"""Проверки связности разговора: продолжения относятся к прошлому понятию.

Запуск:  python tests/test_context.py
"""
import os
import unittest

os.environ["NEURO_NO_GAP"] = "1"

from algos import context, plan_router


class TestState(unittest.TestCase):
    """Память о последнем понятии."""

    def setUp(self):
        context.reset()

    def test_empty_after_reset(self):
        self.assertIsNone(context.last())

    def test_remember_and_read(self):
        self.assertTrue(context.remember("moon", "что такое луна"))
        self.assertEqual(context.last(), "moon")

    def test_empty_concept_not_remembered(self):
        self.assertFalse(context.remember(""))
        self.assertIsNone(context.last())

    def test_followup_not_remembered(self):
        context.remember("moon")
        self.assertFalse(context.remember_from_answer("а почему?", "tide"))

    def test_direct_question_remembered(self):
        self.assertTrue(context.remember_from_answer("что такое луна", "moon"))


class TestFollowup(unittest.TestCase):
    """Распознавание продолжений."""

    def test_markers_detected(self):
        for query in ("а почему?", "подробнее", "ещё", "tell me more"):
            self.assertTrue(context.is_followup(query), query)

    def test_full_question_is_not_followup(self):
        self.assertFalse(context.is_followup("что такое луна"))

    def test_long_phrase_is_not_followup(self):
        self.assertFalse(context.is_followup("а почему " + "очень длинно " * 5))

    def test_expand_uses_last_concept(self):
        context.reset()
        context.remember("moon")
        self.assertIn("moon", context.expand("а почему?"))

    def test_expand_without_concept(self):
        context.reset()
        self.assertEqual(context.expand("а почему?"), "а почему?")


class TestDialog(unittest.TestCase):
    """Два шага разговора подряд."""

    def setUp(self):
        context.reset()

    def test_followup_about_same_concept(self):
        first = plan_router.answer_text("что такое луна")
        second = plan_router.answer_text("а почему?")
        self.assertTrue(first)
        self.assertTrue(second)
        self.assertIn("причина", second.lower())

    def test_more_about_same_concept(self):
        plan_router.answer_text("что такое луна")
        again = plan_router.answer_text("подробнее")
        self.assertTrue(again)
        self.assertIn("лун", again.lower())

    def test_reset_breaks_continuity(self):
        plan_router.answer_text("что такое луна")
        context.reset()
        self.assertIsNone(plan_router.answer_text("подробнее"))


if __name__ == "__main__":
    unittest.main()
