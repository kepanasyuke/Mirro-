# -*- coding: utf-8 -*-
"""Проверки теории информации: энтропия, взаимная информация, PMI, канал, код.

Запуск:  python tests/test_information.py
"""
import math
import unittest

from algos import information as inf


class TestEntropy(unittest.TestCase):
    """Энтропия и собственная информация."""

    def test_uniform_four_bits(self):
        self.assertAlmostEqual(inf.entropy({1: 1, 2: 1, 3: 1, 4: 1}), 2.0, places=6)

    def test_certainty_is_zero(self):
        self.assertAlmostEqual(inf.entropy({"only": 7}), 0.0, places=6)

    def test_biased_binary(self):
        self.assertAlmostEqual(inf.entropy({"a": 9, "b": 1}), 0.469, places=3)

    def test_surprise_of_certainty(self):
        self.assertEqual(inf.surprise(1.0), 0.0)

    def test_surprise_of_half(self):
        self.assertAlmostEqual(inf.surprise(0.5), 1.0, places=6)


class TestDependence(unittest.TestCase):
    """Взаимная информация и PMI."""

    def test_independent_pairs_give_zero(self):
        self.assertAlmostEqual(inf.mutual_information([(0, 0), (0, 1), (1, 0), (1, 1)]), 0.0, places=6)

    def test_identical_pairs_give_one_bit(self):
        self.assertAlmostEqual(inf.mutual_information([(0, 0), (1, 1)]), 1.0, places=6)

    def test_pmi_positive_for_frequent_pair(self):
        self.assertGreater(inf.pmi(10, 20, 30, 100), 0)

    def test_pmi_negative_for_rare_pair(self):
        self.assertLess(inf.pmi(1, 50, 50, 1000), 0)

    def test_pmi_zero_without_data(self):
        self.assertEqual(inf.pmi(0, 0, 0, 0), 0.0)


class TestChannelAndCode(unittest.TestCase):
    """Кросс-энтропия, KL, пропускная способность, код Хаффмана."""

    def test_cross_entropy_equals_entropy_when_equal(self):
        counts = {"a": 3, "b": 1}
        self.assertAlmostEqual(inf.cross_entropy(counts, counts), inf.entropy(counts), places=6)

    def test_kl_is_zero_for_same_distribution(self):
        counts = {"a": 3, "b": 1}
        self.assertAlmostEqual(inf.kl_divergence(counts, counts), 0.0, places=6)

    def test_capacity_of_clean_channel(self):
        self.assertAlmostEqual(inf.channel_capacity_bsc(0.0), 1.0, places=6)

    def test_capacity_of_noisy_channel(self):
        self.assertAlmostEqual(inf.channel_capacity_bsc(0.1), 0.531, places=3)

    def test_huffman_beats_fixed_code(self):
        counts = {"a": 5, "b": 2, "c": 1, "d": 1}
        self.assertLess(inf.average_code_length(counts), 2.0)
        self.assertGreater(inf.average_code_length(counts), inf.entropy(counts) - 1)

    def test_huffman_single_symbol(self):
        self.assertEqual(inf.huffman_lengths({"only": 4}), {"only": 1})


if __name__ == "__main__":
    unittest.main()
