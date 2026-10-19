# -*- coding: utf-8 -*-
"""Юнит-тесты для пакетного обучения перцептрона (улучшение №16).

scripts.algorithms.py строит ~1.5 ГБ индекс при импорте, поэтому нужные
методы извлекаются из исходника и связываются с лёгкой тестовой заглушкой.
"""
import os, re, sys, textwrap, tempfile, unittest
from pathlib import Path

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


_BATCH = _extract("train_from_history", "self, batch_size=32, epochs=1")
_TRAIN = _extract("perceptron_train", "self, query, candidate, label")
_VEC = _extract("perceptron_vectorize", "self, query, candidate")
_NOW = _extract("_now_iso", "")


class _Stub:
    """Заглушка перцептрона: примитивный токенизатор и веса."""
    def __init__(self):
        self.perceptron_weights = {}
        self.perceptron_bias = 0.0
        self.perceptron_trained = False
        self.perceptron_lr = 0.01
        self.feedback_history = []
        self.INDEX_CACHE = Path(tempfile.mkdtemp()) / "index.pkl"
        self._perceptron_train = _TRAIN.__get__(self, _Stub)
        self._perceptron_vectorize = _VEC.__get__(self, _Stub)

    def perceptron_train(self, query, candidate, label):
        return self._perceptron_train(query, candidate, label)

    def perceptron_vectorize(self, query, candidate):
        return self._perceptron_vectorize(query, candidate)

    def tokenize(self, text):
        return re.findall(r"[а-яёa-z0-9]+", text.lower())

    def train_from_history(self, batch_size=32, epochs=1):
        return _BATCH.__get__(self, _Stub)(batch_size, epochs)

    def _now_iso(self):
        return "2026-01-01T00:00:00"


class TestBatchPerceptron(unittest.TestCase):
    def setUp(self):
        self.p = _Stub()

    def test_empty_history_returns_zero(self):
        self.assertEqual(self.p.train_from_history(), 0)

    def test_trains_on_history(self):
        self.p.feedback_history = [
            ("что такое ндс", "НДС это налог на добавленную стоимость", True),
            ("напиши функцию python", "def f(): return 1", True),
            ("неправильный ответ", "абракадабра случайный", False),
        ]
        n = self.p.train_from_history(batch_size=3, epochs=2)
        self.assertEqual(n, 6)
        # веса появились
        self.assertTrue(self.p.perceptron_weights)
        self.assertTrue(any(v != 0 for v in self.p.perceptron_weights.values()) or self.p.perceptron_bias != 0)

    def test_respects_batch_size(self):
        self.p.feedback_history = [(f"q{i}", f"a{i} ответ текст", i % 2 == 0) for i in range(10)]
        n = self.p.train_from_history(batch_size=4)
        self.assertEqual(n, 4)

    def test_weights_change_after_batch(self):
        # С нулевыми весами activation=0 => prediction=1, поэтому лайк (label=+1)
        # обучается без ошибки. А дизлайк (label=-1) даёт ошибку предсказания
        # и обязательно меняет веса.
        self.p.feedback_history = [("реши задачу", "нужно решение задачи", False)] * 3
        before_bias = self.p.perceptron_bias
        self.p.train_from_history(batch_size=3, epochs=5)
        changed = (self.p.perceptron_bias != before_bias) or any(
            v != 0 for v in self.p.perceptron_weights.values())
        self.assertTrue(changed)


if __name__ == "__main__":
    unittest.main()