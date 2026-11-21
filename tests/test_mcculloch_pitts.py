# -*- coding: utf-8 -*-
"""Проверки нейрона Маккаллока–Питтса: логические вентили и предел одного слоя.

Запуск:  python tests/test_mcculloch_pitts.py
"""
import unittest

from algos import mcculloch_pitts as mp


class TestGates(unittest.TestCase):
    """Пороговый нейрон даёт базовую булеву логику."""

    def test_and(self):
        self.assertEqual([out for _, out in mp.truth_table(mp.and_gate)], [0, 0, 0, 1])

    def test_or(self):
        self.assertEqual([out for _, out in mp.truth_table(mp.or_gate)], [0, 1, 1, 1])

    def test_not(self):
        self.assertEqual([mp.not_gate(0), mp.not_gate(1)], [1, 0])

    def test_nand(self):
        self.assertEqual([out for _, out in mp.truth_table(mp.nand_gate)], [1, 1, 1, 0])

    def test_xor_needs_two_layers(self):
        self.assertEqual([out for _, out in mp.truth_table(mp.xor_gate)], [0, 1, 1, 0])


class TestLimits(unittest.TestCase):
    """Что решается одним нейроном, а что нет."""

    def test_and_is_separable(self):
        self.assertTrue(mp.is_linearly_separable(mp.truth_table(mp.and_gate)))

    def test_xor_is_not_separable(self):
        self.assertFalse(mp.is_linearly_separable(mp.truth_table(mp.xor_gate)))

    def test_evaluate_rows(self):
        self.assertEqual(mp.evaluate([1, 1], 2, [(0, 0), (1, 1)]), [0, 1])

    def test_constant_weights(self):
        self.assertEqual(mp.constant_weights(3, 2.0), [2.0, 2.0, 2.0])

    def test_neuron_below_threshold(self):
        self.assertEqual(mp.neuron([1, 1], [1, 0], 2), 0)


if __name__ == "__main__":
    unittest.main()
