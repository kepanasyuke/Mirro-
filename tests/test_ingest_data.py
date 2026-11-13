# -*- coding: utf-8 -*-
"""Юнит-тесты для ingest_data (конвертация датасетов и идемпотентность ingest).

Боевые каталоги D:\\Mirro\\data\\raw и data\\processed не используются:
RAW/PROC подменяются на временный каталог.
"""
import gzip
import json
import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import ingest_data as ing


class _IngestCase(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_raw, self._old_proc = ing.RAW, ing.PROC
        ing.RAW = Path(self._tmp) / "raw"
        ing.PROC = Path(self._tmp) / "processed"
        ing.RAW.mkdir(parents=True)
        ing.PROC.mkdir(parents=True)

    def tearDown(self):
        ing.RAW, ing.PROC = self._old_raw, self._old_proc
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write(self, rel, rows):
        path = ing.RAW / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def _lines(self, cluster):
        path = ing.PROC / f"{cluster}.jsonl"
        if not path.exists():
            return []
        return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]


class TestDetectCluster(unittest.TestCase):
    def test_basic_map(self):
        self.assertEqual(ing.detect_cluster("ru_turbo_saiga/train.jsonl"), "ru")
        self.assertEqual(ing.detect_cluster("openai/gsm8k/test.jsonl"), "math")

    def test_capitalised_keys_match(self):
        # ключи с заглавными буквами раньше не совпадали никогда
        self.assertEqual(ing.detect_cluster("WebSight/train"), "design")
        self.assertEqual(ing.detect_cluster("websight/data.jsonl"), "design")
        self.assertEqual(ing.detect_cluster("MATH-500/test.jsonl"), "math")
        self.assertEqual(ing.detect_cluster("CodeAlpaca-20k/train.jsonl"), "code")
        self.assertEqual(ing.detect_cluster("WizardCoder/data.jsonl"), "code")

    def test_unknown_is_general(self):
        self.assertEqual(ing.detect_cluster("some_random_ds/file.jsonl"), "general")

    def test_empty_id_is_general(self):
        self.assertEqual(ing.detect_cluster(""), "general")


class TestConvertItem(unittest.TestCase):
    def test_alpaca_format(self):
        conv = ing.convert_item({"instruction": "2+2?", "input": "", "output": "4"})
        self.assertEqual(conv, {"instruction": "2+2?", "input": "", "output": "4"})

    def test_sharegpt_format(self):
        conv = ing.convert_item({"conversations": [
            {"from": "human", "value": "Привет"},
            {"from": "gpt", "value": "Здравствуй"},
        ]})
        self.assertEqual(conv["instruction"], "Привет")
        self.assertEqual(conv["output"], "Здравствуй")

    def test_qa_format(self):
        conv = ing.convert_item({"question": "Что такое НДС", "answer": "Налог"})
        self.assertEqual(conv["instruction"], "Что такое НДС")

    def test_unrecognised_returns_none(self):
        self.assertIsNone(ing.convert_item({"unknown": "shape"}))


class TestExtractItems(_IngestCase):
    def test_broken_jsonl_line_skipped(self):
        path = ing.RAW / "ds" / "data.jsonl"
        path.parent.mkdir(parents=True)
        path.write_text('{"instruction":"a","output":"b"}\nне json\n', "utf-8")
        items = ing._extract_items(path)
        self.assertEqual(len(items), 1)

    def test_json_array(self):
        path = ing.RAW / "ds" / "data.json"
        path.parent.mkdir(parents=True)
        path.write_text(json.dumps([{"instruction": "a", "output": "b"}]), "utf-8")
        self.assertEqual(len(ing._extract_items(path)), 1)

    def test_gz_is_decompressed(self):
        path = ing.RAW / "ds" / "data.jsonl.gz"
        path.parent.mkdir(parents=True)
        with gzip.open(path, "wb") as fh:
            fh.write('{"instruction":"a","output":"b"}\n'.encode("utf-8"))
        self.assertEqual(len(ing._extract_items(path)), 1)

    def test_broken_gz_returns_empty(self):
        path = ing.RAW / "ds" / "data.jsonl.gz"
        path.parent.mkdir(parents=True)
        path.write_bytes(b"not a gzip stream at all")
        self.assertEqual(ing._extract_items(path), [])


class TestIdempotentScan(_IngestCase):
    def test_second_scan_adds_nothing(self):
        self._write("ru_turbo_saiga/train.jsonl", [
            {"instruction": "Как дела", "output": "Хорошо"},
            {"instruction": "Который час", "output": "Полдень"},
        ])
        ing.scan_raw_data()
        first = self._lines("ru")
        ing.scan_raw_data()
        second = self._lines("ru")
        self.assertEqual(len(first), 2)
        self.assertEqual(len(second), 2)
        self.assertEqual(first, second)

    def test_duplicates_inside_one_dataset_are_dropped(self):
        row = {"instruction": "Повтор", "output": "Повтор"}
        self._write("ru_turbo_saiga/a.jsonl", [row, row])
        ing.scan_raw_data()
        self.assertEqual(len(self._lines("ru")), 1)

    def test_new_file_appends_only_new_rows(self):
        self._write("ru_turbo_saiga/a.jsonl", [{"instruction": "один", "output": "1"}])
        ing.scan_raw_data()
        self._write("ru_turbo_saiga/b.jsonl", [
            {"instruction": "один", "output": "1"},
            {"instruction": "два", "output": "2"},
        ])
        ing.scan_raw_data()
        self.assertEqual(len(self._lines("ru")), 2)

    def test_existing_file_content_preserved(self):
        path = ing.PROC / "ru.jsonl"
        path.write_text('{"instruction":"старый","input":"","output":"ряд"}\n', "utf-8")
        self._write("ru_turbo_saiga/a.jsonl", [{"instruction": "новый", "output": "ряд"}])
        ing.scan_raw_data()
        rows = self._lines("ru")
        self.assertEqual([r["instruction"] for r in rows], ["старый", "новый"])

    def test_record_key_is_stable(self):
        conv = {"instruction": " a ", "input": "", "output": "b"}
        self.assertEqual(ing.record_key(conv), ing.record_key(dict(conv)))
        self.assertNotEqual(ing.record_key(conv),
                            ing.record_key({"instruction": "a", "input": "", "output": "c"}))


if __name__ == "__main__":
    unittest.main()
