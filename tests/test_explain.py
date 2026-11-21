# -*- coding: utf-8 -*-
"""Проверки разбора хода мысли: поля, шаги, читаемый текст.

Запуск:  python tests/test_explain.py
"""
import os
import unittest

os.environ["NEURO_NO_GAP"] = "1"

from algos import explain


class TestExplain(unittest.TestCase):
    """Разбор вопроса."""

    def test_definition_fields(self):
        data = explain.explain("что такое стек")
        self.assertIsNotNone(data)
        self.assertEqual(data["intent"], "definition")
        self.assertTrue(data["concept"])
        self.assertTrue(data["lines"])
        self.assertGreater(data["steps"], 0)

    def test_why_marks_cause_source(self):
        data = explain.explain("почему луна")
        self.assertIsNotNone(data)
        self.assertTrue(data["source"].startswith("причина"))

    def test_mixed_question_uses_latin(self):
        data = explain.explain("как работает mean")
        self.assertIsNotNone(data)
        self.assertEqual(data["via"], "latin")
        self.assertEqual(data["concept"], "mean")

    def test_unknown_gives_none(self):
        self.assertIsNone(explain.explain("абракадабра ззз"))

    def test_empty_gives_none(self):
        self.assertIsNone(explain.explain("   "))
        self.assertIsNone(explain.explain(None))

    def test_program_compiled(self):
        data = explain.explain("что такое стек")
        self.assertEqual(data["program"][-1][0], "halt")
        self.assertEqual(data["machine_error"], "")


class TestText(unittest.TestCase):
    """Читаемый текст разбора."""

    def test_text_contains_parts(self):
        text = explain.as_text("что такое стек")
        for part in ("Вопрос:", "Тип:", "Понятие:", "Шагов машины:", "Ответ:"):
            self.assertIn(part, text)

    def test_text_for_unknown_is_none(self):
        self.assertIsNone(explain.as_text("абракадабра ззз"))

    def test_plan_lines_listed(self):
        text = explain.as_text("что такое стек")
        self.assertIn("concept = concept(", text)


if __name__ == "__main__":
    unittest.main()
