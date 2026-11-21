# -*- coding: utf-8 -*-
"""Проверки извлечения причин: маркеры, обрезка, индекс.

Запуск:  python tests/test_causality.py
"""
import unittest

from algos import causality


class TestFragments(unittest.TestCase):
    """Куски после маркеров."""

    def test_english_because(self):
        text = "The Moon is Earth's satellite because gravity holds it in orbit."
        pieces = causality.fragments(text, causality.EN_MARKERS)
        self.assertEqual(pieces, ["Gravity holds it in orbit"])

    def test_russian_because(self):
        text = "Лёд тает, потому что температура растёт."
        pieces = causality.fragments(text, causality.RU_MARKERS)
        self.assertEqual(pieces, ["Температура растёт"])

    def test_connector_removed(self):
        text = "Это происходит, потому что того, что молекулы рассеивают свет."
        pieces = causality.fragments(text, causality.RU_MARKERS)
        self.assertEqual(pieces, ["Молекулы рассеивают свет"])

    def test_no_marker_gives_empty(self):
        self.assertEqual(causality.fragments("Просто описание.", causality.RU_MARKERS), [])

    def test_short_tail_is_dropped(self):
        self.assertEqual(causality.fragments("x because y", causality.EN_MARKERS), [])

    def test_long_piece_is_cut(self):
        text = "It happens because " + "очень длинное объяснение " * 30 + "."
        pieces = causality.fragments(text, causality.EN_MARKERS)
        self.assertTrue(pieces)
        self.assertLessEqual(len(pieces[0]), causality.LIMIT + 1)
        self.assertTrue(pieces[0].endswith("…"))

    def test_leads_to(self):
        text = "Heat leads to expansion of the metal."
        self.assertEqual(causality.fragments(text, causality.EN_MARKERS), ["Expansion of the metal"])


class TestConcept(unittest.TestCase):
    """Работа с понятием реестра."""

    def test_english_concept_has_cause(self):
        concept = {"ru": "", "en": "The Moon causes tides on Earth. It orbits us."}
        pieces = causality.for_concept(concept)
        self.assertEqual(pieces[0][0], "en")
        self.assertIn("ides on Earth", pieces[0][1])

    def test_russian_concept_has_cause(self):
        concept = {"ru": "Стек работает, потому что хранит вершину.", "en": ""}
        pieces = causality.for_concept(concept)
        self.assertEqual(pieces[0][0], "ru")

    def test_no_causes(self):
        self.assertFalse(causality.has_causes({"ru": "Стек — структура данных.", "en": ""}))

    def test_limit_respected(self):
        concept = {"ru": "Потому что раз. Поэтому два. Так как три.", "en": ""}
        self.assertLessEqual(len(causality.for_concept(concept, limit=2)), 2)


class TestRealBase(unittest.TestCase):
    """На настоящей базе причины находятся."""

    def test_index_not_empty(self):
        self.assertGreater(len(causality.index()), 100)

    def test_moon_has_cause(self):
        from algos import concepts
        concept = concepts.build().get(concepts._normal("moon"))
        self.assertTrue(causality.has_causes(concept))


if __name__ == "__main__":
    unittest.main()
