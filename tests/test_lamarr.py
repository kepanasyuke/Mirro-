# -*- coding: utf-8 -*-
"""Проверки схемы Хеди Ламарр: перестройка частоты, расширение спектра, приём.

Запуск:  python tests/test_lamarr.py
"""
import unittest

from algos import lamarr as lm


class TestSequence(unittest.TestCase):
    """Регистр сдвига даёт псевдослучайную последовательность максимальной длины."""

    def test_period_of_four_bit_register(self):
        self.assertEqual(lm.period(1, (3, 2), 64), 15)

    def test_sequence_length(self):
        self.assertEqual(len(lm.lfsr(1, (3, 2), 15)), 15)

    def test_sequence_is_binary(self):
        self.assertEqual(set(lm.lfsr(3, (3, 2), 15)) <= {0, 1}, True)

    def test_sequence_not_constant(self):
        bits = lm.lfsr(1, (3, 2), 15)
        self.assertGreater(len(set(bits)), 1)


class TestHopping(unittest.TestCase):
    """Скачки по каналам выбираются той же последовательностью."""

    def test_hops_stay_within_channels(self):
        channels = ["f1", "f2", "f3", "f4"]
        hops = lm.hop_channels(channels, lm.lfsr(1, (3, 2), 15), 2)
        self.assertTrue(set(hops) <= set(channels))

    def test_hops_use_several_channels(self):
        channels = ["f%d" % index for index in range(1, 9)]
        hops = lm.hop_channels(channels, lm.lfsr(1, (3, 2), 15), 3)
        self.assertGreater(len(set(hops)), 2)

    def test_indexes_match_channels(self):
        channels = ["a", "b", "c"]
        bits = lm.lfsr(2, (3, 2), 9)
        hops = lm.hop_channels(channels, bits, 2)
        indexes = lm.hop_indexes(channels, bits, 2)
        self.assertEqual([channels[index] for index in indexes], hops)


class TestSpread(unittest.TestCase):
    """Расширение спектра обратимо, чужой код не читает передачу."""

    def test_round_trip(self):
        data = [1, 0, 1, 1, 0, 0, 1]
        code = [1, 1, 0, 1, 0, 0, 1, 1]
        self.assertEqual(lm.despread(lm.spread(data, code), code), data)

    def test_correlation_with_itself(self):
        chips = lm.spread([1, 0, 1], [1, 0, 1, 1])
        self.assertEqual(lm.correlate(chips, chips), 1.0)

    def test_other_code_does_not_correlate(self):
        data = [1, 0, 1, 1, 0, 0, 1]
        mine = lm.spread(data, [1, 1, 0, 1, 0, 0, 1, 1])
        other = lm.spread(data, [0, 1, 1, 0, 1, 1, 0, 0])
        self.assertLess(lm.correlate(mine, other), 0.5)

    def test_other_code_gives_other_message(self):
        data = [1, 0, 1, 1, 0, 0, 1]
        chips = lm.spread(data, [1, 1, 0, 1, 0, 0, 1, 1])
        self.assertNotEqual(lm.despread(chips, [0, 1, 1, 0, 1, 1, 0, 0]), data)


if __name__ == "__main__":
    unittest.main()
