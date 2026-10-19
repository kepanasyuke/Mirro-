# -*- coding: utf-8 -*-
"""Юнит-тесты для Mirro Reasoning Engine.

Запуск:  python -m unittest discover -s tests -v
Модуль чистый — не требует базы, корпуса или сети.
"""
import sys, os, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.reasoning_engine import score_candidate, choose_best, _tokenize, run_self_check


class TestTokenizer(unittest.TestCase):
    def test_cyrillic_latin_digits(self):
        self.assertEqual(_tokenize("Привет, world 123!"), ["привет", "world", "123"])

    def test_lowercase(self):
        self.assertEqual(_tokenize("МОСКВА"), ["москва"])

    def test_empty(self):
        self.assertEqual(_tokenize("  ,.!!  "), [])


class TestScoreCandidate(unittest.TestCase):
    def test_favors_preferred_cluster(self):
        q = "что такое ндс"
        s_same, _ = score_candidate(q, "НДС — налог.", "ru", 1.0, preferred="ru")
        s_other, _ = score_candidate(q, "сторонний текст", "general", 1.0, preferred="ru")
        self.assertGreater(s_same, s_other)

    def test_penalizes_generated(self):
        q = "как дела"
        s_gen, _ = score_candidate(q, "что-то сгенерированное", "generated", 1.0, preferred="ru")
        s_norm, _ = score_candidate(q, "обычный ответ", "ru", 1.0, preferred="ru")
        self.assertGreater(s_norm, s_gen)

    def test_word_overlap_bonus(self):
        q = "столица франции"
        s_overlap, _ = score_candidate(q, "Франция — большая страна, столица — Париж.", "ru", 1.0)
        s_none, _ = score_candidate(q, "не имеет ничего общего", "ru", 1.0)
        self.assertGreater(s_overlap, s_none)


class TestChooseBest(unittest.TestCase):
    def test_no_candidates(self):
        best, score, reason = choose_best("что такое ндс", [])
        self.assertIsNone(best)
        self.assertEqual(reason, "нет кандидатов")

    def test_prefers_same_cluster(self):
        q = "что такое ндс"
        cands = [
            (("шум", "абра кадабра", "generated"), 8.0),
            (("ндс", "НДС — косвенный налог.", "ru"), 3.0),
        ]
        best, _, _ = choose_best(q, cands, preferred="ru")
        self.assertTrue(best and "НДС" in best)

    def test_returns_none_if_not_in_preferred(self):
        q = "что такое ндс"
        cands = [(("ндс", "НДС — налог.", "general"), 4.0)]
        best, _, reason = choose_best(q, cands, preferred="code")
        self.assertIsNone(best)
        self.assertIn("нет в кластере", reason)


class TestSelfCheck(unittest.TestCase):
    def test_all_checks_pass(self):
        ok, details = run_self_check()
        self.assertTrue(ok, msg=details)


if __name__ == "__main__":
    unittest.main()