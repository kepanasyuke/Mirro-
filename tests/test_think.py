# -*- coding: utf-8 -*-
"""Юнит-тесты для мыслительного движка algos/think.py.

Запуск:  python -m unittest discover -s tests -v
Чистый модуль — не требует базы, корпуса или сети (только stdlib).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.think import think, _comb, _fact, _gcd, _lcm, _isprime, _solve_quadratic


class TestArithmeticHelpers(unittest.TestCase):
    def test_comb(self):
        self.assertEqual(_comb(10, 3), 120)
        self.assertEqual(_comb(5, 0), 1)

    def test_fact(self):
        self.assertEqual(_fact(0), 1)
        self.assertEqual(_fact(5), 120)

    def test_gcd_lcm(self):
        self.assertEqual(_gcd(48, 36), 12)
        self.assertEqual(_lcm(4, 6), 12)

    def test_isprime(self):
        self.assertFalse(_isprime(1))
        self.assertTrue(_isprime(2))
        self.assertTrue(_isprime(13))
        self.assertFalse(_isprime(15))

    def test_solve_quadratic(self):
        roots = _solve_quadratic(1, -5, 6)
        self.assertCountEqual(roots, [2.0, 3.0])
        self.assertEqual(_solve_quadratic(0, 0, 5), [])


class TestThinkRecognizes(unittest.TestCase):
    def test_addition(self):
        r = think("сколько будет 2+2")
        self.assertEqual(r["category"], "математика")
        self.assertIsNotNone(r["answer"])

    def test_percent_symbol(self):
        r = think("15% от 200")
        self.assertIn("30", str(r["answer"]))
        self.assertEqual(r["category"], "математика")

    def test_percent_word(self):
        # Регрессия: раньше «процентов» словами не распознавалось без знака %
        r = think("15 процентов от 200")
        self.assertIn("30", str(r["answer"]))
        self.assertEqual(r["category"], "математика")

    def test_quadratic(self):
        r = think("реши x^2-5x+6=0")
        self.assertIn(3.0, r["answer"])

    def test_unknown_returns_none(self):
        r = think("расскажи анекдот")
        self.assertIsNone(r["answer"])
        self.assertEqual(r["category"], "unknown")


if __name__ == "__main__":
    unittest.main()