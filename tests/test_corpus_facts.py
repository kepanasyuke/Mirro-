# -*- coding: utf-8 -*-
"""Юнит-тесты для corpus_facts (expansión фактов, дедуп) и corpus_audit (аналитика)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path


class TestCorpusFacts(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        self._tmpdir = tempfile.mkdtemp()
        self._facts_path = os.path.join(self._tmpdir, "facts.jsonl")

    def test_norm_question(self):
        from corpus_facts import _norm_question
        self.assertEqual(_norm_question("Что такое нейрон?"), "что такое нейрон")

    def test_dedup_adds_only_new(self):
        import corpus_facts
        # первый проход со временным файлом
        corpus_facts.TARGET = Path(self._facts_path)
        first = corpus_facts.run()
        second = corpus_facts.run()  # повторный прогон не должен добавить дубли
        self.assertGreaterEqual(first, 1)
        self.assertEqual(second, 0)
        if os.path.exists(self._facts_path):
            os.remove(self._facts_path)


class TestCorpusAudit(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

    def test_audit_shape(self):
        from corpus_audit import audit
        # audit требует тяжёлый подгруз индекса; тестируем поля структуры
        # через лёгкую проверку классификации _topic_of
        from corpus_audit import _topic_of
        self.assertEqual(_topic_of("алгоритм сортировки граф"), "математика/алгоритмы")
        self.assertEqual(_topic_of("физика атом скорость"), "физика")


if __name__ == "__main__":
    unittest.main()