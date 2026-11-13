# -*- coding: utf-8 -*-
"""Юнит-тесты для self_learn (дедуп записей, meta, устойчивость к сбоям сети).

Все каталоги (data/self_learned, data/processed, logs) подменяются на
временные: боевые данные и сеть не затрагиваются.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import self_learn as sl


class _LearnCase(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        self._saved = (sl.MIRRO, sl.LEARN_DIR, sl.LOG_DIR, sl.CORE_DIR, sl.LEARN_META)
        sl.MIRRO = self._tmp
        sl.LEARN_DIR = self._tmp / "data" / "self_learned"
        sl.LOG_DIR = self._tmp / "logs"
        sl.CORE_DIR = self._tmp / "core"
        sl.LEARN_META = sl.LEARN_DIR / "meta.json"
        sl.LEARN_DIR.mkdir(parents=True)
        sl.LOG_DIR.mkdir(parents=True)
        (self._tmp / "data" / "processed").mkdir(parents=True)

    def tearDown(self):
        sl.MIRRO, sl.LEARN_DIR, sl.LOG_DIR, sl.CORE_DIR, sl.LEARN_META = self._saved
        shutil.rmtree(str(self._tmp), ignore_errors=True)

    def _lines(self, path):
        if not path.exists():
            return []
        return [json.loads(x) for x in path.read_text("utf-8").splitlines() if x.strip()]

    def _write_logs(self, count=12):
        rows = [{"success": True, "prompt_len": 50, "cluster": "ru", "ts": i,
                 "provider": "deepseek", "latency_ms": 10, "tokens": 5}
                for i in range(count)]
        (sl.LOG_DIR / "calls.jsonl").write_text(
            "\n".join(json.dumps(r) for r in rows), "utf-8")


class TestExampleDedup(_LearnCase):
    def test_append_new_examples_skips_existing(self):
        path = sl.LEARN_DIR / "x.jsonl"
        row = {"instruction": "a", "input": "", "output": "b"}
        self.assertEqual(sl.append_new_examples(path, [row]), 1)
        self.assertEqual(sl.append_new_examples(path, [row]), 0)
        self.assertEqual(len(self._lines(path)), 1)

    def test_append_new_examples_dedups_within_batch(self):
        path = sl.LEARN_DIR / "x.jsonl"
        row = {"instruction": "a", "input": "", "output": "b"}
        self.assertEqual(sl.append_new_examples(path, [row, dict(row)]), 1)

    def test_append_keeps_existing_file_content(self):
        path = sl.LEARN_DIR / "x.jsonl"
        path.write_text('{"instruction": "старое", "input": "", "output": "ряд"}\n', "utf-8")
        sl.append_new_examples(path, [{"instruction": "новое", "input": "", "output": "ряд"}])
        self.assertEqual([r["instruction"] for r in self._lines(path)], ["старое", "новое"])

    def test_example_key_is_stable_and_trims(self):
        a = {"instruction": " q ", "input": "", "output": "o"}
        self.assertEqual(sl.example_key(a), sl.example_key(dict(a)))
        self.assertNotEqual(sl.example_key(a),
                            sl.example_key({"instruction": "q2", "input": "", "output": "o"}))

    def test_broken_json_line_ignored_in_keys(self):
        path = sl.LEARN_DIR / "x.jsonl"
        path.write_text("не json\n", "utf-8")
        self.assertEqual(sl.existing_keys(path), set())


class TestLearnFromLogs(_LearnCase):
    def test_second_run_adds_nothing(self):
        self._write_logs()
        learner = sl.SelfLearner()
        first = learner.learn_from_logs()
        second = learner.learn_from_logs()
        self.assertEqual(first, 12)
        self.assertEqual(second, 0)
        self.assertEqual(len(self._lines(sl.LEARN_DIR / "selflog_general.jsonl")), 12)

    def test_too_few_logs_are_skipped(self):
        self._write_logs(count=9)
        self.assertEqual(sl.SelfLearner().learn_from_logs(), 0)

    def test_broken_log_lines_do_not_break(self):
        self._write_logs(count=10)
        with open(sl.LOG_DIR / "calls.jsonl", "a", encoding="utf-8") as fh:
            fh.write("\nмусор\n")
        self.assertEqual(sl.SelfLearner().learn_from_logs(), 10)


class TestSkillsKnowledge(_LearnCase):
    def test_skills_written_once(self):
        learner = sl.SelfLearner()
        learner.build_skills_knowledge()
        learner.build_skills_knowledge()
        processed = sl.MIRRO / "data" / "processed"
        code_rows = self._lines(processed / "code.jsonl")
        expected = len([s for s in sl.MIRRO_SKILLS if s["domain"] == "code"])
        self.assertEqual(len(code_rows), expected)

    def test_skills_file_rewritten_not_appended(self):
        learner = sl.SelfLearner()
        learner.build_skills_knowledge()
        learner.build_skills_knowledge()
        rows = self._lines(sl.LEARN_DIR / "mirro_own_skills.jsonl")
        self.assertEqual(len(rows), len(sl.MIRRO_SKILLS))


class TestMeta(_LearnCase):
    def test_broken_meta_falls_back_to_defaults(self):
        sl.LEARN_META.write_text("{битый", "utf-8")
        meta = sl.SelfLearner().meta
        self.assertEqual(meta["total_sessions"], 0)
        self.assertEqual(meta["domains"], {})

    def test_partial_meta_gets_missing_keys(self):
        sl.LEARN_META.write_text('{"total_sessions": 5}', "utf-8")
        meta = sl.SelfLearner().meta
        self.assertEqual(meta["total_sessions"], 5)
        self.assertIn("total_learned", meta)
        self.assertIsInstance(meta["domains"], dict)

    def test_save_meta_is_atomic_and_readable(self):
        learner = sl.SelfLearner()
        learner.meta["total_sessions"] = 3
        self.assertTrue(learner._save_meta())
        saved = json.loads(sl.LEARN_META.read_text("utf-8"))
        self.assertEqual(saved["total_sessions"], 3)
        self.assertFalse(list(sl.LEARN_DIR.glob("*.tmp")))

    def test_save_meta_reports_failure(self):
        learner = sl.SelfLearner()
        sl.LEARN_META = self._tmp / "good.json"
        self.assertTrue(learner._save_meta())
        # место под временный файл занято каталогом — запись обязана вернуть False
        (self._tmp / "bad.json.tmp").mkdir()
        sl.LEARN_META = self._tmp / "bad.json"
        self.assertFalse(learner._save_meta())


class TestFetch(_LearnCase):
    def test_non_2xx_response_ignored(self):
        class Resp:
            status = 503

            def read(self):
                return b'{"query": {}}'

            def __enter__(self):
                return self

            def __exit__(self, *args):
                return False

        old = sl.urllib.request.urlopen
        sl.urllib.request.urlopen = lambda req, timeout=None: Resp()
        try:
            self.assertIsNone(sl.SelfLearner()._fetch_json("https://example.invalid"))
        finally:
            sl.urllib.request.urlopen = old

    def test_network_error_returns_none(self):
        import urllib.error

        def boom(req, timeout=None):
            raise urllib.error.URLError("offline")

        old = sl.urllib.request.urlopen
        sl.urllib.request.urlopen = boom
        try:
            self.assertIsNone(sl.SelfLearner()._fetch_text("https://example.invalid"))
        finally:
            sl.urllib.request.urlopen = old


if __name__ == "__main__":
    unittest.main()
