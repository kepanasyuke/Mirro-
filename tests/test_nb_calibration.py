# -*- coding: utf-8 -*-
"""Юнит-тесты для калибровки априорных вероятностей Naive Bayes (улучшение №18).

scripts.algorithms.py строит ~1.5 ГБ индекс при импорте, поэтому чистая
функция _calibrate_priors извлекается из исходника без выполнения модуля.
"""
import os, re, sys, textwrap, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

ALGO_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "algorithms.py")


def _extract(name, signature):
    src = open(ALGO_PATH, encoding="utf-8-sig").read()
    m = re.search(r"    def " + name + r"\(" + signature + r".*?(?=\n    def |\n    @|# =+|\Z)", src, re.S)
    if not m:
        raise RuntimeError(f"{name} не найден в algorithms.py")
    block = m.group(0)
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
    pass


class TestCalibratePriors(unittest.TestCase):
    def setUp(self):
        self.fn = _CAL.__get__(_Stub(), _Stub)

    def test_alpha1_no_change(self):
        p = {"ru": 0.9, "design": 0.1}
        out = self.fn(p, alpha=1.0)
        self.assertAlmostEqual(out["ru"], 0.9)
        self.assertAlmostEqual(out["design"], 0.1)

    def test_normalizes_sum_to_one(self):
        out = self.fn({"ru": 0.9, "design": 0.1}, alpha=0.5)
        self.assertAlmostEqual(sum(out.values()), 1.0)

    def test_smoothes_imbalance(self):
        # Сильный дисбаланс: ru доминирует. Калибровка (alpha<1) должна
        # подтянуть редкий класс к меньшему разрыву.
        p = {"ru": 0.98, "code": 0.02}
        raw = 0.02  # доля редкого класса без калибровки
        cal = self.fn(p, alpha=0.5)["code"]
        self.assertGreater(cal, raw)

    def test_zero_priors_dropped(self):
        out = self.fn({"ru": 0.8, "empty": 0.0}, alpha=0.5)
        self.assertNotIn("empty", out)

    def test_empty_input_returns_empty(self):
        self.assertEqual(self.fn({}), {})


if __name__ == "__main__":
    unittest.main()