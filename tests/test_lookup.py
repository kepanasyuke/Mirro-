# -*- coding: utf-8 -*-
"""Проверки поиска: язык слова важнее языка вопроса.

Запуск:  python tests/test_lookup.py
"""
import unittest

from algos import lookup


class TestLanguage(unittest.TestCase):
    """Определение языка по словам."""

    def test_russian_question(self):
        self.assertEqual(lookup.answer_language("что такое стек"), "ru")

    def test_english_question(self):
        self.assertEqual(lookup.answer_language("what is music?"), "la")

    def test_mixed_with_latin_term(self):
        self.assertEqual(lookup.answer_language("как работает mean"), "ru")

    def test_latin_terms_extracted(self):
        self.assertEqual(lookup.latin_terms("как работает mean и median"), ["mean", "median"])

    def test_short_latin_skipped(self):
        self.assertEqual(lookup.latin_terms("a b cd"), [])


class TestFind(unittest.TestCase):
    """Латинский термин выигрывает у грубого русского алиаса."""

    def test_latin_term_beats_russian_alias(self):
        found = lookup.find("как работает mean")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "mean")
        self.assertEqual(found["via"], "latin")

    def test_median_too(self):
        found = lookup.find("как работает median")
        self.assertEqual(found["concept"]["name"], "median")

    def test_russian_question_uses_registry(self):
        found = lookup.find("что такое стек")
        self.assertIsNotNone(found)
        self.assertIn(found["via"], ("word", "registry"))
        self.assertIn("стек", found["concept"]["name"])

    def test_russian_alias_still_works(self):
        found = lookup.find("среднее арифметическое")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "mean")

    def test_unknown_is_none(self):
        self.assertIsNone(lookup.find("абракадабра ззз"))

    def test_english_unknown_ignores_question_word(self):
        self.assertIsNone(lookup.find("what is quark?"))

    def test_english_known_found(self):
        found = lookup.find("what is entropy?")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "entropy")

    def test_case_word_beats_meta_word(self):
        found = lookup.find("какие связи у графа")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "graph")

    def test_case_ending_stripped(self):
        found = lookup.find("с чем связана музыка")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "music")

    def test_fleeting_vowel_found(self):
        # проверяем механизм, а не конкретную тему: реестр растёт, и «любви»
        # может вести и на «любовь», и на «привязанность»
        found = lookup.find("любви")
        self.assertIsNotNone(found)
        self.assertTrue((found["concept"].get("ru") or "").strip())

    def test_fleeting_vowel_no_false_hits(self):
        self.assertIsNone(lookup.find("абракадабра"))

    def test_genitive_of_short_noun(self):
        for word in ("сна", "сны"):
            found = lookup.find(word)
            self.assertIsNotNone(found, word)
            self.assertIn("сон", found["concept"]["name"])

    def test_exact_word_beats_stem_match(self):
        # «банк» — это банк, а не «банка» (сосуд), хотя основа общая
        found = lookup.find("что такое банк")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "_банк")

    def test_case_form_keeps_its_concept(self):
        found = lookup.find("что такое банка")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "jar")

    def test_two_word_phrase_preferred(self):
        found = lookup.find("что такое хеш таблица")
        self.assertIsNotNone(found)
        self.assertIn("хеш", found["concept"]["name"])

    def test_restored_ending(self):
        # механизм, а не тема: «воды» должно находить хоть какое-то понятие
        # с русским текстом (реестр растёт, алиасы меняются)
        found = lookup.find("воды")
        self.assertIsNotNone(found)
        self.assertTrue((found["concept"].get("ru") or "").strip())

    def test_unknown_with_meta_word_is_none(self):
        self.assertIsNone(lookup.find("сколько связей у графика"))

    def test_long_word_is_not_short_topic(self):
        found = lookup.find("что такое градиент")
        self.assertIsNotNone(found)
        self.assertNotEqual(found["concept"]["name"], "град")

    def test_part_of_compound_is_not_topic(self):
        self.assertIsNone(lookup.find("что такое хеш-функция"))

    def test_compound_word_alone_has_no_topic(self):
        self.assertIsNone(lookup.find("хеш-функция"))

    def test_phrase_still_wins_over_word(self):
        found = lookup.find("поиск в ширину")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "bfs")

    def test_learned_fallback(self):
        found = lookup.find_with_learned("абракадабра ззз", "/nonexistent/path.jsonl")
        self.assertIsNone(found)


if __name__ == "__main__":
    unittest.main()
