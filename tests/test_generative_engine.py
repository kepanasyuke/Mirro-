# -*- coding: utf-8 -*-
"""Юнит-тесты для generative_engine (MirroAI: TF-IDF поиск, бусты, запуск).

Корпус и состояние подменяются временными файлами: боевые data/processed и
data/ai_state.json не читаются и не пишутся.
"""
import json
import os
import shutil
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import generative_engine as ge


ROWS = [
    {"instruction": "Что такое НДС", "output": "Налог на добавленную стоимость, косвенный налог."},
    {"instruction": "Как посчитать НДС", "output": "Умножь сумму на ставку и выдели налог из неё."},
    {"instruction": "Рецепт борща", "output": "Свёкла, капуста, мясо, варить час на медленном огне."},
    {"instruction": "Короткий", "output": "мало"},  # отсеян: ответ короче 20 символов
]


class _EngineCase(unittest.TestCase):
    def setUp(self):
        self._tmp = Path(tempfile.mkdtemp())
        proc = self._tmp / "processed"
        proc.mkdir()
        with open(proc / "ru.jsonl", "w", encoding="utf-8") as fh:
            for row in ROWS:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        (proc / "broken.jsonl").write_text("не json\n", "utf-8")
        self.state = self._tmp / "ai_state.json"
        self.engine = ge.MirroAI(source_dir=proc, state_file=self.state)

    def tearDown(self):
        shutil.rmtree(str(self._tmp), ignore_errors=True)


class TestBuildIndex(_EngineCase):
    def test_short_answers_skipped(self):
        self.assertEqual(len(self.engine.examples), 3)

    def test_broken_line_skipped(self):
        self.assertTrue(all("не json" not in inst for inst, _, _ in self.engine.examples))

    def test_cluster_is_file_stem(self):
        self.assertEqual({c for _, _, c in self.engine.examples}, {"ru"})

    def test_empty_corpus_does_not_divide_by_zero(self):
        empty = ge.MirroAI(source_dir=self._tmp / "nope", state_file=self.state)
        self.assertEqual(empty.total_docs, 1)
        self.assertEqual(empty.search("ндс"), [])


class TestTfidf(_EngineCase):
    def test_idf_never_negative(self):
        weight = self.engine._tfidf("ндс", 1)
        self.assertGreater(weight, 0.0)

    def test_unknown_term_has_zero_weight(self):
        self.assertEqual(self.engine._tfidf("нетакогослова", 3), 0.0)


class TestSearch(_EngineCase):
    def test_finds_relevant_answer(self):
        results = self.engine.search("что такое НДС", top_n=2)
        self.assertTrue(results)
        self.assertIn("налог", results[0][1].lower())

    def test_create_index_never_ran_against_prod(self):
        # тест не должен поднимать боевой индекс на 1.2 млн примеров
        self.assertIsNone(ge.ai._engine)

    def test_empty_query_no_results(self):
        self.assertEqual(self.engine.search("", top_n=3), [])

    def test_compose_answer_non_empty(self):
        answer = self.engine.compose_answer(self.engine.search("НДС", top_n=2))
        self.assertTrue(answer)
        self.assertIn("налог", answer.lower())

    def test_compose_answer_of_nothing_is_none(self):
        self.assertIsNone(self.engine.compose_answer([]))


class TestFeedbackAndState(_EngineCase):
    def test_like_boosts_query(self):
        self.engine.learn_from_feedback("что такое ндс", "ответ", liked=True)
        key = self.engine._boost_key("что такое ндс")
        self.assertGreater(self.engine.boost_map[key], 0)

    def test_state_persisted_and_reloaded(self):
        self.engine.learn_from_feedback("ндс", "ответ", liked=True)
        loaded = ge.MirroAI(source_dir=self.engine.source_dir, state_file=self.state)
        self.assertIn(self.engine._boost_key("ндс"), loaded.boost_map)

    def test_broken_state_file_ignored(self):
        self.state.write_text("{битый", "utf-8")
        engine = ge.MirroAI(source_dir=self.engine.source_dir, state_file=self.state)
        self.assertEqual(engine.boost_map, {})

    def test_save_state_reports_failure(self):
        bad = self._tmp / "dir.json"
        bad.mkdir()
        engine = ge.MirroAI(source_dir=self.engine.source_dir, state_file=bad)
        self.assertFalse(engine._save_state())

    def test_self_question_loop_runs(self):
        self.assertIsInstance(self.engine.self_question_loop(3), int)
        self.assertIsInstance(self.engine.status()["boost_entries"], int)


class TestLazySingleton(unittest.TestCase):
    def test_module_import_does_not_build_index(self):
        src = Path(ge.__file__).read_text("utf-8")
        self.assertNotIn("\nai = MirroAI()", src)
        self.assertIn("ai = _LazyAI()", src)

    def test_facade_delegates_to_engine(self):
        lazy = ge._LazyAI()
        self.assertIsNone(lazy._engine)
        with tempfile.TemporaryDirectory() as tmp:
            empty = ge.MirroAI(source_dir=Path(tmp) / "nope", state_file=Path(tmp) / "s.json")
        lazy._engine = empty
        self.assertIs(lazy._get(), empty)
        self.assertEqual(lazy.search("q"), [])


if __name__ == "__main__":
    unittest.main()
