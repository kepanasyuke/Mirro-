# -*- coding: utf-8 -*-
"""Юнит-тесты для экспоненциального затухания boost (улучшение №14).

scripts.algorithms.py строит TF-IDF индекс (~1.5 ГБ) при импорте из-за
singleton `algo = MirroAlgorithms()`, поэтому чистые методы boost
извлекаются из исходника модуля без его выполнения.
"""
import os, re, sys, textwrap, time, unittest

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
    code = f"def {name}({signature}):\n" + body
    ns = {}
    # Извлечённые методы ссылаются на глобальные имена модуля (_re, time, math).
    import math, random, collections
    ns.update({"_re": re, "time": time, "math": math, "random": random,
               "Counter": collections.Counter, "defaultdict": collections.defaultdict})
    exec(code, ns)
    return ns[name]


class _FakeBoost:
    """Минимальная заглушка с теми же атрибутами, что у MirroAlgorithms."""
    def __init__(self):
        self.qa_boost = {}
        self.qa_boost_ts = {}
        self.boost_decay_hours = 168.0


class TestBoostMethods(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.boost_key = staticmethod(_extract("_boost_key", "inst"))
        cls.decay = staticmethod(_extract("_decay_boost", "self, key, now=None"))
        cls.add = staticmethod(_extract("_add_boost", "self, key, delta"))

    def _make(self):
        f = _FakeBoost()
        # Привязываем извлечённые функции как bound-method к заглушке.
        # Присваивание голой функции атрибуту экземпляра НЕ связывает self,
        # поэтому используем __get__ (дескриптор функции).
        f._boost_key = self.boost_key.__get__(f, type(f))
        f._decay_boost = self.decay.__get__(f, type(f))
        f._add_boost = self.add.__get__(f, type(f))
        return f

    def test_stable_key(self):
        k1 = self.boost_key("НДС это налог на добавленную стоимость")
        k2 = self.boost_key("НДС это налог на добавленную стоимость")
        self.assertEqual(k1, k2)
        # регистронезависимый и без пунктуации
        self.assertNotIn("?", k1)

    def test_decay_halflife(self):
        f = self._make()
        t0 = 1_000_000.0
        f.qa_boost["k"] = 1.0
        f.qa_boost_ts["k"] = t0
        # через одни период полураспада — буст должен стать вдвое меньше
        after = f._decay_boost("k", t0 + 168 * 3600)
        self.assertAlmostEqual(after, 0.5, places=4)

    def test_decay_two_halflifes(self):
        f = self._make()
        t0 = 1_000_000.0
        f.qa_boost["k"] = 1.0
        f.qa_boost_ts["k"] = t0
        after = f._decay_boost("k", t0 + 336 * 3600)
        self.assertAlmostEqual(after, 0.25, places=4)

    def test_no_decay_immediately(self):
        f = self._make()
        f.qa_boost["k"] = 1.0
        f.qa_boost_ts["k"] = 1_000_000.0
        after = f._decay_boost("k", 1_000_000.0)
        self.assertAlmostEqual(after, 1.0, places=4)

    def test_unknown_key_zero(self):
        f = self._make()
        self.assertEqual(f._decay_boost("missing"), 0.0)

    def test_tiny_boost_pruned(self):
        f = self._make()
        f.qa_boost["k"] = 0.01
        f.qa_boost_ts["k"] = 0.0
        f._decay_boost("k", 100.0)
        self.assertNotIn("k", f.qa_boost)

    def test_add_accumulates(self):
        f = self._make()
        f._add_boost("k", 0.4)
        f._add_boost("k", 0.4)
        self.assertGreater(f.qa_boost["k"], 0.79)


if __name__ == "__main__":
    unittest.main()