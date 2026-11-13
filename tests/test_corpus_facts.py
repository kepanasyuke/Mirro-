# -*- coding: utf-8 -*-
"""Юнит-тесты для corpus_facts (expansión фактов, дедуп) и corpus_audit (аналитика)."""
import json
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
        # ключ дедупа — только содержательные слова: служебные отброшены
        from corpus_facts import _norm_question
        self.assertEqual(_norm_question("Что такое нейрон?"), "нейрон")

    def test_norm_question_merges_punctuation_variants(self):
        from corpus_facts import _norm_question
        self.assertEqual(_norm_question("Что такое нейрон?"),
                         _norm_question("что такое  нейрон ,"))
        self.assertEqual(_norm_question("Почему небо голубое"),
                         _norm_question("почему небо голубое?"))

    def test_norm_question_empty(self):
        from corpus_facts import _norm_question
        self.assertEqual(_norm_question(""), "")
        self.assertEqual(_norm_question(None), "")

    def test_all_builtin_facts_have_unique_keys(self):
        import corpus_facts
        from collections import Counter
        keys = [corpus_facts._norm_question(q) for q, _ in corpus_facts.FACTS]
        self.assertEqual(len(keys), len(set(keys)))

    def test_dedup_across_punctuation_variants(self):
        import corpus_facts
        target = Path(self._facts_path)
        target.write_text('{"instruction": "Что такое нейрон?", "input": "", "output": "x"}\n',
                          encoding="utf-8")
        corpus_facts.TARGET = target
        added = corpus_facts.run()
        rows = [json.loads(x) for x in target.read_text("utf-8").splitlines() if x.strip()]
        keys = [corpus_facts._norm_question(r["instruction"]) for r in rows]
        self.assertEqual(len(keys), len(set(keys)))
        self.assertLess(added, len(corpus_facts.FACTS))

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