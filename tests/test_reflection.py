# -*- coding: utf-8 -*-
"""Юнит-тесты рефлексии Mirro (scripts/reflection.py)."""
import os
import sys
import tempfile
import unittest
from pathlib import Path


class TestReflection(unittest.TestCase):
    def setUp(self):
        sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))
        self._tmp = tempfile.mkdtemp()

    def test_words_extracts_keywords(self):
        from reflection import _words
        w = _words("что такое нейрон в мозге и как он работает")
        self.assertTrue(len(w) >= 3)
        self.assertNotIn("что", w)
        self.assertNotIn("и", w)

    def test_last_failures_empty_when_no_file(self):
        from reflection import _last_failures
        # подменим путь на несуществующий
        import reflection
        reflect_backup = reflection.FAILURES
        reflection.FAILURES = Path(self._tmp) / "nope.jsonl"
        try:
            self.assertEqual(_last_failures(), [])
        finally:
            reflection.FAILURES = reflect_backup

    def test_words_min_len(self):
        from reflection import _words
        self.assertEqual(_words("в на по и"), [])  # только стоп-слова


if __name__ == "__main__":
    unittest.main()