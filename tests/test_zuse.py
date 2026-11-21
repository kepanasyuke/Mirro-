# -*- coding: utf-8 -*-
"""Проверки наследия Конрада Цузе: реле, двоичная точка, клеточный автомат.

Запуск:  python tests/test_zuse.py
"""
import unittest

from algos import zuse


class TestRelay(unittest.TestCase):
    """Схема из реле считает булеву логику."""

    def test_half_adder_table(self):
        table = [zuse.half_adder(a, b) for a in (0, 1) for b in (0, 1)]
        self.assertEqual(table, [(0, 0), (1, 0), (1, 0), (0, 1)])

    def test_circuit_chain(self):
        plan = [("both", "and", ["a", "b"]), ("either", "or", ["a", "b"]),
                ("only_one", "xor", ["both", "either"])]
        signals = zuse.relay_circuit(plan, {"a": 1, "b": 0})
        self.assertEqual((signals["both"], signals["either"], signals["only_one"]), (0, 1, 1))

    def test_not_inverts(self):
        signals = zuse.relay_circuit([("inv", "not", ["a"])], {"a": 1})
        self.assertEqual(signals["inv"], 0)


class TestBinary(unittest.TestCase):
    """Двоичная арифметика и плавающая точка."""

    def test_add_binary(self):
        self.assertEqual(zuse.add_binary("101", "11"), "1000")

    def test_add_binary_zero(self):
        self.assertEqual(zuse.add_binary("0", "0"), "0")

    def test_float_round_trip(self):
        for value in (5.5, -0.75, 1024.0, 0.125):
            sign, exponent, mantissa = zuse.to_binary_float(value)
            self.assertAlmostEqual(zuse.from_binary_float(sign, exponent, mantissa), value, places=6)

    def test_float_zero(self):
        self.assertEqual(zuse.to_binary_float(0), (0, 0, "0"))

    def test_float_sign(self):
        sign, _, _ = zuse.to_binary_float(-3.25)
        self.assertEqual(sign, 1)


class TestCalculatingSpace(unittest.TestCase):
    """Клеточный автомат: локальное правило даёт глобальную картину."""

    def test_rule30_from_single_cell(self):
        self.assertEqual(zuse.cellular_step([0, 0, 1, 0, 0], 30), [0, 1, 1, 1, 0])

    def test_rule_zero_clears(self):
        self.assertEqual(zuse.cellular_step([1, 1, 1], 0), [0, 0, 0])

    def test_rule_255_fills(self):
        self.assertEqual(zuse.cellular_step([0, 0, 0], 255), [1, 1, 1])

    def test_history_length(self):
        self.assertEqual(len(zuse.run_cellular([1, 0, 1], 30, 4)), 5)

    def test_density_bounds(self):
        self.assertEqual(zuse.cellular_density([0, 0, 0]), 0.0)
        self.assertEqual(zuse.cellular_density([1, 1]), 1.0)
        self.assertEqual(zuse.cellular_density([]), 0.0)


class TestPlan(unittest.TestCase):
    """План вычисления в духе Plankalkül: шаги без ветвлений."""

    def test_even_number_of_ones(self):
        self.assertEqual(zuse.parity_program([1, 0, 1]), 0)

    def test_odd_number_of_ones(self):
        self.assertEqual(zuse.parity_program([1, 1, 1]), 1)

    def test_empty(self):
        self.assertEqual(zuse.parity_program([]), 0)


if __name__ == "__main__":
    unittest.main()
