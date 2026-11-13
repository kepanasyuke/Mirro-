# -*- coding: utf-8 -*-
"""Юнит-тесты для clean_corpus (очистка и дедупликация JSONL-корпусов).

Работают на временных файлах: боевые data/self_learned и data/processed
не читаются и не пишутся.
"""
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import clean_corpus as cc


class _CleanCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._dir = Path(self._tmp)
        self._old_sl, self._old_pr = cc.SELF_LEARNED, cc.PROCESSED
        cc.SELF_LEARNED = self._dir / "self_learned"
        cc.PROCESSED = self._dir / "processed"

    def tearDown(self):
        cc.SELF_LEARNED, cc.PROCESSED = self._old_sl, self._old_pr
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _file(self, name, rows, raw_lines=None):
        path = self._dir / name
        with open(path, "w", encoding="utf-8") as fh:
            if raw_lines is not None:
                for line in raw_lines:
                    fh.write(line + "\n")
            else:
                for row in rows:
                    fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def _rows(self, path):
        return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]


class TestIsKeepable(_CleanCase):
    def test_arithmetic_example_is_kept(self):
        # раньше токенизатор терял «=» и цифры-одиночки, пример считался мусором
        self.assertTrue(cc._is_keepable({"instruction": "2+2", "output": "4"}))

    def test_formula_is_kept(self):
        self.assertTrue(cc._is_keepable({"instruction": "x = 1", "output": "x = 1"}))

    def test_short_but_valid_is_kept(self):
        self.assertTrue(cc._is_keepable({"instruction": "Что такое НДС?", "output": "Налог"}))

    def test_empty_output_rejected(self):
        self.assertFalse(cc._is_keepable({"instruction": "Вопрос", "output": ""}))

    def test_empty_instruction_rejected(self):
        self.assertFalse(cc._is_keepable({"instruction": "", "output": "Ответ"}))

    def test_whitespace_only_rejected(self):
        self.assertFalse(cc._is_keepable({"instruction": "   ", "output": "\n\t"}))


class TestCleanJsonl(_CleanCase):
    def test_dry_run_does_not_touch_file(self):
        path = self._file("a.jsonl", [{"instruction": "в", "output": "о"},
                                      {"instruction": "", "output": ""}])
        before = path.read_text("utf-8")
        kept, removed = cc.clean_jsonl(path, apply=False)
        self.assertEqual((kept, removed), (1, 1))
        self.assertEqual(path.read_text("utf-8"), before)

    def test_apply_removes_only_dirty_rows(self):
        path = self._file("a.jsonl", [
            {"instruction": "Первый", "output": "Ответ"},
            {"instruction": "", "output": "сирота"},
            {"instruction": "2+2", "output": "4"},
        ])
        kept, removed = cc.clean_jsonl(path, apply=True)
        self.assertEqual((kept, removed), (2, 1))
        self.assertEqual([r["instruction"] for r in self._rows(path)], ["Первый", "2+2"])

    def test_dedup_keeps_first_occurrence(self):
        path = self._file("a.jsonl", [
            {"instruction": "Дубль", "output": "Ответ", "tag": "первый"},
            {"instruction": "Дубль", "output": "Ответ", "tag": "второй"},
        ])
        kept, removed = cc.clean_jsonl(path, apply=True)
        self.assertEqual((kept, removed), (1, 1))
        self.assertEqual(self._rows(path)[0]["tag"], "первый")

    def test_broken_json_line_dropped(self):
        path = self._file("a.jsonl", None, raw_lines=['{"instruction":"a","output":"b"}', "не json"])
        kept, removed = cc.clean_jsonl(path, apply=True)
        self.assertEqual((kept, removed), (1, 1))

    def test_no_tmp_files_left_behind(self):
        path = self._file("a.jsonl", [{"instruction": "a", "output": "b"}])
        cc.clean_jsonl(path, apply=True)
        leftovers = [p.name for p in self._dir.iterdir() if p.name.startswith(".clean_")]
        self.assertEqual(leftovers, [])

    def test_non_dict_json_dropped(self):
        path = self._file("a.jsonl", None, raw_lines=['[1, 2, 3]', '"строка"'])
        kept, removed = cc.clean_jsonl(path, apply=True)
        self.assertEqual((kept, removed), (0, 2))


class TestAtomicWrite(_CleanCase):
    def test_failed_write_keeps_original(self):
        path = self._file("a.jsonl", [{"instruction": "важное", "output": "не потерять"}])
        original = path.read_text("utf-8")
        old_mkstemp = cc.tempfile.mkstemp

        def boom(*args, **kwargs):
            raise OSError("диск переполнен")

        cc.tempfile.mkstemp = boom
        try:
            ok = cc._atomic_write(path, [{"instruction": "новое", "output": "заменит"}])
        finally:
            cc.tempfile.mkstemp = old_mkstemp
        self.assertFalse(ok)
        self.assertEqual(path.read_text("utf-8"), original)

    def test_failed_write_reports_zero_in_clean_jsonl(self):
        path = self._file("a.jsonl", [{"instruction": "a", "output": "b"}])
        old = cc._atomic_write
        cc._atomic_write = lambda p, rows: False
        try:
            kept, removed = cc.clean_jsonl(path, apply=True)
        finally:
            cc._atomic_write = old
        self.assertEqual((kept, removed), (0, 0))


class TestCleanDirectory(_CleanCase):
    def test_only_small_jsonl_processed(self):
        cc.PROCESSED.mkdir(parents=True)
        small = self._file("processed/small.jsonl", [{"instruction": "a", "output": "b"}])
        big = self._file("processed/big.jsonl", [{"instruction": "a", "output": "b"}])
        old_limit = cc.MAX_BYTES
        cc.MAX_BYTES = 10
        try:
            report = cc.clean_directory(cc.PROCESSED, apply=True)
        finally:
            cc.MAX_BYTES = old_limit
        self.assertEqual(report["files"], 0)
        self.assertEqual(small.read_text("utf-8"), big.read_text("utf-8"))

    def test_missing_directory_is_empty_report(self):
        report = cc.clean_directory(self._dir / "nope", apply=False)
        self.assertEqual(report, {"files": 0, "kept": 0, "removed": 0})


if __name__ == "__main__":
    unittest.main()
