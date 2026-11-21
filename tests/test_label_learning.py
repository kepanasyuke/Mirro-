# -*- coding: utf-8 -*-
"""Проверки обучения русских имён: счётчики, PMI, порог, запись, поиск.

Все файлы — во временном каталоге, настоящая очередь пробелов не трогается.

Запуск:  python tests/test_label_learning.py
"""
import json
import os
import tempfile
import unittest

from algos import label_learning as ll


def write_jsonl(path, rows):
    """Записывает строки JSONL."""
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


class TestCandidates(unittest.TestCase):
    """Счётчики и PMI по очередям пробелов."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.gaps = os.path.join(self.folder, "gaps.jsonl")
        self.rows = [
            {"query": "что такое музыка", "concept": "music"},
            {"query": "расскажи про музыку", "concept": "music"},
            {"query": "что такое музыка", "concept": "music"},
            {"query": "что такое стек", "concept": "stack"},
            {"query": "что такое очередь", "concept": "queue"},
        ]
        write_jsonl(self.gaps, self.rows)

    def test_entries_read(self):
        self.assertEqual(len(ll.gap_entries(self.gaps)), 5)

    def test_candidates_count(self):
        rows = ll.candidates(ll.gap_entries(self.gaps))
        self.assertTrue(rows)
        self.assertTrue(all("pmi" in row for row in rows))

    def test_frequent_pair_has_high_pmi(self):
        rows = ll.candidates(ll.gap_entries(self.gaps))
        top = {(row["word"], row["concept"]): row for row in rows}
        self.assertGreater(top[("музык", "music")]["pmi"], 0)
        self.assertEqual(top[("музык", "music")]["count"], 3)

    def test_accepted_respects_threshold(self):
        rows = ll.candidates(ll.gap_entries(self.gaps))
        accepted = ll.accepted(rows, min_count=2, min_pmi=0.5)
        words = {row["word"] for row in accepted}
        self.assertIn("музык", words)
        self.assertNotIn("стек", words)

    def test_accepted_empty_for_high_threshold(self):
        rows = ll.candidates(ll.gap_entries(self.gaps))
        self.assertEqual(ll.accepted(rows, min_count=10, min_pmi=0.0), [])


class TestStorage(unittest.TestCase):
    """Запись принятых пар и поиск по ним."""

    def setUp(self):
        self.folder = tempfile.mkdtemp()
        self.aliases = os.path.join(self.folder, "learned.jsonl")

    def test_write_and_read(self):
        rows = [{"word": "музык", "concept": "music", "count": 3, "pmi": 1.2}]
        added = ll.write_accepted(rows, self.aliases)
        self.assertEqual(added, 1)
        self.assertEqual(ll.learned(self.aliases), {"музык": "music"})

    def test_no_duplicates_on_repeat(self):
        rows = [{"word": "музык", "concept": "music", "count": 3, "pmi": 1.2}]
        ll.write_accepted(rows, self.aliases)
        self.assertEqual(ll.write_accepted(rows, self.aliases), 0)
        self.assertEqual(len(ll.learned(self.aliases)), 1)

    def test_guess_finds_concept(self):
        ll.write_accepted([{"word": "музык", "concept": "music", "count": 3, "pmi": 1.2}],
                          self.aliases)
        self.assertEqual(ll.guess("расскажи про музыку", self.aliases), "music")

    def test_guess_none_for_unknown(self):
        self.assertIsNone(ll.guess("абракадабра", self.aliases))

    def test_missing_file_is_empty(self):
        self.assertEqual(ll.learned(os.path.join(self.folder, "нет.jsonl")), {})


class TestLearnPass(unittest.TestCase):
    """Полный проход: очередь -> кандидаты -> файл."""

    def test_learn_writes_once(self):
        folder = tempfile.mkdtemp()
        gaps = os.path.join(folder, "gaps.jsonl")
        aliases = os.path.join(folder, "learned.jsonl")
        write_jsonl(gaps, [{"query": "что такое музыка", "concept": "music"},
                           {"query": "про музыку", "concept": "music"}])
        result = ll.learn(gaps, aliases, min_count=2, min_pmi=0.0)
        self.assertGreaterEqual(result["added"], 1)
        self.assertEqual(ll.learn(gaps, aliases, min_count=2, min_pmi=0.0)["added"], 0)


if __name__ == "__main__":
    unittest.main()
