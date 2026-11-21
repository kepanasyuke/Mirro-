# -*- coding: utf-8 -*-
"""Проверки самометрики: покрытие, типы вопросов, запись и чтение снимков.

Запуск:  python tests/test_self_metrics.py
"""
import os
import tempfile
import unittest

from algos import self_metrics


class TestCoverage(unittest.TestCase):
    """Покрытие базы."""

    def test_keys_present(self):
        cover = self_metrics.coverage()
        for key in ("concepts", "with_ru", "with_en", "en_only", "causes", "gaps", "learned"):
            self.assertIn(key, cover)

    def test_counts_are_positive(self):
        cover = self_metrics.coverage()
        self.assertGreater(cover["concepts"], 1000)
        self.assertGreater(cover["with_en"], 0)

    def test_share_is_fraction(self):
        cover = self_metrics.coverage()
        self.assertGreaterEqual(cover["ru_share"], 0.0)
        self.assertLessEqual(cover["ru_share"], 1.0)


class TestIntents(unittest.TestCase):
    """Распознавание типов вопросов."""

    def test_known_sample(self):
        counts = self_metrics.intents(["что такое стек", "привет"])
        self.assertEqual(counts.get("definition"), 1)
        self.assertEqual(counts.get("unknown"), 1)

    def test_empty_sample(self):
        self.assertEqual(self_metrics.intents([]), {})


class TestAnswers(unittest.TestCase):
    """Сводка по контрольным вопросам."""

    def test_rows_have_shape(self):
        rows = self_metrics.answered(["что такое стек"])
        self.assertEqual(len(rows), 1)
        self.assertIn("answered", rows[0])
        self.assertIn("steps", rows[0])

    def test_summary_counts(self):
        snapshot = self_metrics.summary()
        self.assertEqual(snapshot["total"], len(snapshot["rows"]))
        self.assertLessEqual(snapshot["answered"], snapshot["total"])
        self.assertIn("coverage", snapshot)


class TestStorage(unittest.TestCase):
    """Запись снимка и чтение истории."""

    def test_write_and_read(self):
        folder = tempfile.mkdtemp()
        path = os.path.join(folder, "metrics.jsonl")
        self_metrics.write(path=path, snapshot={"coverage": {"concepts": 1}, "answered": 1, "total": 1})
        history = self_metrics.history(path=path)
        self.assertEqual(len(history), 1)
        self.assertEqual(history[0]["answered"], 1)

    def test_missing_file_gives_empty(self):
        self.assertEqual(self_metrics.history(path=os.path.join(tempfile.mkdtemp(), "none.jsonl")), [])


if __name__ == "__main__":
    unittest.main()
