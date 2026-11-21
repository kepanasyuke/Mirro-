# -*- coding: utf-8 -*-
"""Проверки извлечения различий: маркеры, цель, обрезка, поиск между понятиями.

Запуск:  python tests/test_contrast.py
"""
import unittest

from algos import contrast

APERTURE = {"name": "aperture", "en": "An aperture is an opening. It differs from a cleft, "
                                     "which is a division of the stuff itself."}
CLEFT = {"name": "cleft", "en": "A cleft is a split in rock."}


class TestClauses(unittest.TestCase):
    """Разбор противопоставлений в тексте."""

    def test_differs_from(self):
        rows = contrast.clauses(APERTURE["en"])
        self.assertEqual(rows[0][0], "cleft")
        self.assertTrue(rows[0][1].startswith("differs from a cleft"))

    def test_opposite_of(self):
        rows = contrast.clauses("Good is the opposite of evil in this scheme.")
        self.assertEqual(rows[0][0], "evil")

    def test_unlike(self):
        rows = contrast.clauses("Unlike a comet, an asteroid has no tail.")
        self.assertEqual(rows[0][0], "comet")

    def test_no_marker(self):
        self.assertEqual(contrast.clauses("Простое определение без сравнений."), [])

    def test_article_stripped(self):
        rows = contrast.clauses("It differs from the recess in depth.")
        self.assertEqual(rows[0][0], "recess")

    def test_long_clause_cut(self):
        text = "It differs from a cleft " + "очень длинное пояснение " * 30
        rows = contrast.clauses(text)
        self.assertLessEqual(len(rows[0][1]), contrast.LIMIT + 1)


class TestBetween(unittest.TestCase):
    """Различие между двумя понятиями."""

    def test_forward_direction(self):
        piece = contrast.between(APERTURE, CLEFT)
        self.assertTrue(piece.startswith("differs from a cleft"))

    def test_backward_direction(self):
        piece, source = contrast.difference(CLEFT, APERTURE)
        self.assertEqual(source, "aperture")
        self.assertIn("cleft", piece)

    def test_no_relation_gives_empty(self):
        self.assertEqual(contrast.between({"name": "x", "en": "X is a thing."}, {"name": "y"}), "")

    def test_missing_text(self):
        self.assertEqual(contrast.between({"name": "x"}, {"name": "y"}), "")


class TestRealBase(unittest.TestCase):
    """На настоящей базе различия находятся."""

    def test_aperture_and_cleft(self):
        from algos import concepts
        registry = concepts.build()
        first = registry.get(concepts._normal("aperture"))
        second = registry.get(concepts._normal("cleft"))
        piece, source = contrast.difference(first, second)
        self.assertTrue(piece)
        self.assertIn(source, ("aperture", "cleft"))


if __name__ == "__main__":
    unittest.main()
