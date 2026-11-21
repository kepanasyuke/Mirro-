# -*- coding: utf-8 -*-
"""Проверки русской рамки: имя из алиасов, связи, английский источник.

Запуск:  python tests/test_compose.py
"""
import unittest

from algos import compose


class TestTitle(unittest.TestCase):
    """Русское имя выбирается из алиасов."""

    def test_takes_cyrillic_alias(self):
        concept = {"name": "moon", "aliases": ("moon", "луна")}
        self.assertEqual(compose.russian_title(concept), "луна")

    def test_prefers_longest_alias(self):
        concept = {"name": "mean", "aliases": ("арифметическ", "арифметическое")}
        self.assertEqual(compose.russian_title(concept), "арифметическое")

    def test_falls_back_to_name(self):
        concept = {"name": "pyramid", "aliases": ("pyramid",)}
        self.assertEqual(compose.russian_title(concept), "pyramid")

    def test_underscores_replaced(self):
        concept = {"name": "hash_table", "aliases": ()}
        self.assertEqual(compose.russian_title(concept), "hash table")

    def test_bad_input(self):
        self.assertEqual(compose.russian_title(None), "")


class TestAdjectiveGuard(unittest.TestCase):
    """Обрубки прилагательных не становятся русским именем."""

    def test_bare_adjective_detected(self):
        self.assertTrue(compose._bare_adjective("иностранная"))
        self.assertTrue(compose._bare_adjective("непорочное"))

    def test_phrase_is_not_adjective(self):
        self.assertFalse(compose._bare_adjective("иностранная помощь"))

    def test_noun_is_not_adjective(self):
        self.assertFalse(compose._bare_adjective("помощь"))

    def test_fragment_skipped_in_title(self):
        concept = {"name": "aid", "aliases": ("aid", "иностранная", "помощь")}
        self.assertEqual(compose.russian_title(concept), "помощь")

    def test_only_fragment_used_when_nothing_else(self):
        concept = {"name": "aid", "aliases": ("aid", "иностранная")}
        self.assertEqual(compose.russian_title(concept), "иностранная")


class TestCompose(unittest.TestCase):
    """Сборка рамки."""

    def test_full_frame(self):
        concept = {"name": "moon", "aliases": ("moon", "луна")}
        text = compose.compose(concept, ["приливы", "орбита"], "The Moon is a satellite.")
        self.assertTrue(text.startswith("Луна — понятие"))
        self.assertIn("приливы, орбита", text)
        self.assertIn("Описание есть только по-английски", text)

    def test_english_links_are_hidden(self):
        concept = {"name": "moon", "aliases": ("луна",)}
        text = compose.compose(concept, ["tide", "orbit"], "The Moon is a satellite.")
        self.assertNotIn("tide", text)

    def test_without_links(self):
        concept = {"name": "moon", "aliases": ("луна",)}
        text = compose.compose(concept, [], "The Moon is a satellite.")
        self.assertNotIn("Связано с", text)

    def test_links_limited(self):
        concept = {"name": "x", "aliases": ()}
        text = compose.compose(concept, ["альфа", "бета", "гамма", "дельта"], "")
        self.assertIn("альфа, бета, гамма", text)
        self.assertNotIn("дельта", text)

    def test_empty_concept_gives_empty(self):
        self.assertEqual(compose.compose({}, [], ""), "")

    def test_related_text_empty(self):
        self.assertEqual(compose.related_text([]), "")
        self.assertEqual(compose.related_text(["приливы"]), "приливы")

    def test_related_text_skips_english(self):
        self.assertEqual(compose.related_text(["tide", "приливы"]), "приливы")


if __name__ == "__main__":
    unittest.main()
