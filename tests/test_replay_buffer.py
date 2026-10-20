# -*- coding: utf-8 -*-
"""Юнит-тесты для реплей-буфера feedback (улучшение №13).

Проверяет, что autonomous_learn пере-игрывает накопленную историю
оценённых пользователем пар (query, response, liked) и тем самым не
забывает явные предпочтения.
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


_AUTONOMOUS = _extract("autonomous_learn", "self, cycles=30")


class _StubReplay:
    """Заглушка: считает, сколько раз пере-игран feedback."""
    def __init__(self):
        self.learned_calls = 0
        self.feedback_history = []
        self.examples = []  # пустая база — цикл по sample не запускается

    def perceptron_train(self, q, r, liked):
        self.learned_calls += 1
        return True

    def tokenize(self, text):
        return ["x"]

    def compose_answer(self, q, top_n=4):
        return None

    def autonomous_learn(self, cycles=30):
        return _AUTONOMOUS.__get__(self, _StubReplay)(cycles)


class TestReplayBuffer(unittest.TestCase):
    def test_empty_history_nothing_replayed(self):
        s = _StubReplay()
        n = s.autonomous_learn(cycles=1)
        # нет examples -> цикл по sample пуст, feedback пуст
        self.assertEqual(s.learned_calls, 0)

    def test_feedback_replayed_in_autonomous(self):
        s = _StubReplay()
        s.feedback_history = [
            ("что такое ндс", "НДС это налог на добавленную стоимость", True),
            ("напиши функцию", "def f(): return 1", True),
            ("плохой ответ", "абракадабра", False),
        ]
        n = s.autonomous_learn(cycles=1)
        # 3 пары feedback пере-играны
        self.assertGreaterEqual(s.learned_calls, 3)
        self.assertGreaterEqual(n, 3)


if __name__ == "__main__":
    unittest.main()