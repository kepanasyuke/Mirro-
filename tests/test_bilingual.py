# -*- coding: utf-8 -*-
"""Тесты русско-английского моста (algos/bilingual.py).

Проверяют: карта пар читается, русский вопрос находит английскую тему,
английский вопрос мостом не обрабатывается, сжатие не раздувает текст.
"""
import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algos.bilingual as bilingual  # noqa: E402


class BilingualMapTest(unittest.TestCase):
    def test_map_is_loaded(self):
        ru_to_en, en_to_ru = bilingual.pairs()
        self.assertGreater(len(ru_to_en), 500)
        self.assertGreater(len(en_to_ru), 500)

    def test_russian_word_finds_english_topic(self):
        self.assertIn(bilingual.find_concept("что такое мудрость"), ("wisdom", "sapience"))

    def test_transliteration_still_works(self):
        self.assertEqual("алгоритм", bilingual.transliterate("algorithm"))

    def test_russian_name_from_map(self):
        self.assertEqual("инсайт", bilingual.russian_name("insight"))


class BilingualAnswerTest(unittest.TestCase):
    def test_english_question_is_not_ours(self):
        self.assertIsNone(bilingual.try_bilingual("what is insight?"))

    def test_small_talk_gets_no_answer(self):
        self.assertIsNone(bilingual.try_bilingual("привет, как дела"))

    def test_summary_is_short_and_closed(self):
        text = "First sentence. " + "второе предложение " * 60 + "."
        summary = bilingual.summarize(text)
        self.assertLessEqual(len(summary), 321)
        self.assertTrue(summary.endswith(".") or summary.endswith("…"))

    def test_empty_text_gives_none(self):
        self.assertIsNone(bilingual.summarize("   "))

    def test_related_concepts_are_russian_words(self):
        related = bilingual.related_concepts("courage")
        self.assertIsInstance(related, list)
        self.assertTrue(all(isinstance(name, str) and name for name in related))
        self.assertTrue(all(not any("a" <= ch <= "z" for ch in name) for name in related))

    def test_unknown_topic_has_no_related(self):
        self.assertEqual([], bilingual.related_concepts("не такое понятие"))


class BriefEnglishTest(unittest.TestCase):
    """Русский вопрос не должен получать простыню по-английски."""

    def test_long_english_is_cut_to_one_sentence(self):
        text = "Photosynthesis is how green plants make food. They take in water and carbon dioxide."
        self.assertEqual(bilingual._brief(text),
                         "Photosynthesis is how green plants make food.")

    def test_empty_gives_empty(self):
        self.assertEqual(bilingual._brief("   "), "")

    def test_long_single_sentence_is_capped(self):
        text = "word " * 200
        self.assertLessEqual(len(bilingual._brief(text)), 221)


if __name__ == "__main__":
    unittest.main()
