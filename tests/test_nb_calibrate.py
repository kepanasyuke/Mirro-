# -*- coding: utf-8 -*-
"""Юнит-тесты для NB-калибровки априорных вероятностей (улучшение №14).

Проверяет _calibrate_priors(): смягчение дисбаланса кластеров при сохранении
суммы = 1 и отсечение нулевых prior. Метод извлекается из algorithms.py,
чтобы не строить ~1.5 ГБ индекс при импорте.
"""
import os, re, sys, textwrap, unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ALGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "algorithms.py")


def _extract(name, signature, static=False):
    src = open(ALGO_PATH, encoding="utf-8-sig").read()
    m = re.search(r"    (?:static )?def " + name + r"\(" + signature + r".*?(?=\n    def |\n    @|# =+|\Z)", src, re.S)
    if not m:
        raise RuntimeError(f"{name} не найден в algorithms.py")
    block = m.group(0)
    if static:
        head, _, body = block.partition("):\n")
    else:
        head, _, body = block.partition(":\n")
    body = textwrap.dedent(body)
    body = textwrap.indent(body, "    ")
    ns = {}
    import math, random, collections, time
    ns.update({"_re": re, "time": time, "math": math, "random": random,
               "Counter": collections.Counter, "defaultdict": collections.defaultdict})
    exec(f"def {name}({signature}):\n" + body, ns)
    return ns[name]


_CAL = _extract("_calibrate_priors", "self, priors, alpha=0.5")


class _Stub:
    def _calibrate_priors(self, priors, alpha=0.5):
        return _CAL.__get__(self, _Stub)(priors, alpha)


class TestNbCalibrate(unittest.TestCase):
    def setUp(self):
        self.s = _Stub()

    def test_sum_is_one(self):
        out = self.s._calibrate_priors({"ru": 650000, "design": 6000, "math": 200000})
        self.assertAlmostEqual(sum(out.values()), 1.0, places=6)

    def test_alpha_1_keeps_frequency(self):
        priors = {"ru": 650000, "math": 200000, "design": 6000}
        out = self.s._calibrate_priors(priors, alpha=1.0)
        total = sum(priors.values())
        for cl, p in priors.items():
            self.assertAlmostEqual(out[cl], p / total, places=6)

    def test_alpha_05_reduces_imbalance(self):
        # Разумный реальный дисбаланс: ru ~ в 100 раз больше design.
        priors = {"ru": 650000, "design": 6000}
        raw_ratio = max(priors.values()) / max(min(priors.values()), 1)
        out = self.s._calibrate_priors(priors, alpha=0.5)
        out_ratio = max(out.values()) / max(min(out.values()), 1e-9)
        self.assertLess(out_ratio, raw_ratio, "калибровка должна смягчать дисбаланс")
        # Априорные остаются упорядоченными (сильнейший класс всё ещё ведущий).
        self.assertGreater(out["ru"], out["design"])

    def test_zero_and_empty(self):
        self.assertEqual(self.s._calibrate_priors({}), {})
        out = self.s._calibrate_priors({"a": 10, "b": 0, "c": 5})
        self.assertNotIn("b", out)
        self.assertAlmostEqual(sum(out.values()), 1.0, places=6)


if __name__ == "__main__":
    unittest.main()