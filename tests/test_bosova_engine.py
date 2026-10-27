# -*- coding: utf-8 -*-
"""Юнит-тесты для выполнимых босовских алгоритмов (algos/bosova_engine.py).

Модуль чистый (не строит индекс), поэтому импортируем напрямую и проверяем:
- арифметика по правилам Босовой (ЕСЛИ/ТО, проценты, сложение);
- тройственное рассуждение «нейрон-нигде» (трёх тел + Шеннон);
- схемы для самоописания (рекурсия, вспомогательный алгоритм);
- точка входа применить() корректно не срабатывает на бытовом вопросе.
"""
import os, sys, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.bosova_engine import (  # noqa: E402
    решить_арифметику,
    тройственность,
    схема_мышления,
    список_схем,
    применить,
)


class TestBosovaArithmetic(unittest.TestCase):
    def test_slozhenie(self):
        ans, scheme = решить_арифметику("Сколько будет 4 + 5?")
        self.assertEqual(ans, 9)
        self.assertTrue(scheme)

    def test_vychitanie(self):
        ans, _ = решить_арифметику("Сколько будет 10 - 3?")
        self.assertEqual(ans, 7)

    def test_procent(self):
        ans, _ = решить_арифметику("Сколько будет 25% от 200?")
        self.assertEqual(ans, 50)

    def test_bez_operacii(self):
        ans, _ = решить_арифметику("Расскажи про нейросети")
        self.assertIsNone(ans)


class TestBosovaTernary(unittest.TestCase):
    def test_nahodit_tri_elementa(self):
        tr = тройственность("страх связан с опасностью и влияет на контроль между людьми")
        self.assertIsNotNone(tr)
        self.assertEqual(len(tr["elements"]), 3)
        self.assertIn("влияние_третьего", tr)

    def test_ne_nahodit_bez_treh(self):
        tr = тройственность("привет как дела")
        self.assertIsNone(tr)

    def test_relations_summary(self):
        tr = тройственность("время связано с пространством и влияет на движение тел")
        if tr:
            self.assertTrue(0 <= tr["влияние_третьего"] <= 1)


class TestBosovaSchemes(unittest.TestCase):
    def test_rekursiya(self):
        s = схема_мышления("рекурсия")
        self.assertIn("Рекурсия", s["name"])
        self.assertTrue(s["steps"])

    def test_spisok_shem_ne_pust(self):
        self.assertGreaterEqual(len(список_схем()), 3)


class TestBosovaEntry(unittest.TestCase):
    def test_arifmetika_cherez_vhod(self):
        res = применить("Сколько будет 4 плюс 5?")
        self.assertIsNotNone(res)
        self.assertEqual(res["kind"], "bosova_arifmetika")
        self.assertEqual(res["answer"], "9")

    def test_bytovoy_vopros_ignor(self):
        res = применить("как дела сегодня")
        self.assertIsNone(res)


if __name__ == "__main__":
    unittest.main()