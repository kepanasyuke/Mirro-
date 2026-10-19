# -*- coding: utf-8 -*-
"""Юнит-тесты для Mirro Voice (голос и характер).

Запуск:  python -m unittest discover -s tests -v
Модуль чистый — не требует базы или сети.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.voice import speak, try_jarvis, _clean, _rephrase


class TestTryJarvis(unittest.TestCase):
    def test_jarvis_trigger(self):
        res = try_jarvis("Джарвис, какой план?")
        self.assertIsNotNone(res)
        self.assertIn("Слушаю", res)

    def test_non_jarvis_returns_none(self):
        self.assertIsNone(try_jarvis("какая погода сегодня"))


class TestClean(unittest.TestCase):
    def test_removes_service_markers(self):
        text = "[Веб] Название статьи. Источник: https://example.com"
        cleaned = _clean(text)
        self.assertNotIn("[Веб]", cleaned)
        self.assertNotIn("Источник:", cleaned)

    def test_removes_br_and_code_blocks(self):
        text = "Привет<br>мир ```python def f()```"
        cleaned = _clean(text)
        self.assertNotIn("<br>", cleaned)
        self.assertNotIn("```", cleaned)

    def test_whitespace_normalized(self):
        self.assertEqual(_clean("много   пробелов\n\nи перевода"), "много пробелов и перевода")


class TestRephrase(unittest.TestCase):
    def test_lowercases_stilted_words(self):
        self.assertIn("это", _rephrase("НДС является налогом"))

    def test_strips_bureaucratic_tail(self):
        self.assertEqual(_rephrase("текст и т.д."), "текст")


class TestSpeak(unittest.TestCase):
    def test_none_input(self):
        self.assertIsNone(speak(None, "вопрос"))

    def test_short_answer_gets_intro_outro(self):
        out = speak("Привет!", "привет")
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), len("Привет!"))

    def test_preserves_core_content(self):
        raw = "НДС — это косвенный налог, который добавляется к цене товара."
        out = speak(raw, "что такое ндс")
        self.assertIn("НДС", out)

    def test_topic_hint_added(self):
        raw = "Питон — язык программирования с простым синтаксисом."
        out = speak(raw, "расскажи про python")
        self.assertIn("алгоритм", out)  # подсказка из BY_TOPIC["код"]


if __name__ == "__main__":
    unittest.main()