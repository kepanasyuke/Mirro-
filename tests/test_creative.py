# -*- coding: utf-8 -*-
"""Юнит-тесты для креативных генераторов Mirro (улучшение ответов на запросы
о стихах, рассказах, загадках, тостах).

Извлекает функции из core/mirro_core.py без выполнения сервера.
"""
import os, re, sys, textwrap, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

CORE_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "core", "mirro_core.py")


def _extract(name):
    src = open(CORE_PATH, encoding="utf-8-sig").read()
    # Начало функции на 0-отступе, затем её текст до следующей top-level def/class
    m = re.search(r"^def " + name + r"\([^)]*\):.*", src, re.S | re.M)
    if not m:
        raise RuntimeError(f"{name} не найден в mirro_core.py")
    start = m.start()
    # конец: следующая строка, начинающаяся с 'def ' или 'class ' на отступе 0
    rest = src[start:]
    m2 = re.search(r"^\ndef |^\nclass |^\n# ", rest, re.M)
    end = start + (m2.start() if m2 else len(rest))
    return src[start:end]


def _load_gen(fn):
    code = _extract(fn)
    ns = {}
    exec(code, ns)
    return ns[fn]


_POEM = _load_gen("_gen_poem")
_STORY = _load_gen("_gen_story")
_RIDDLE = _load_gen("_gen_riddle")
_TOAST = _load_gen("_gen_toast")
# try_creative ссылается на внутренние генераторы — подкладываем их в namespace.
_ns = {}
exec(_extract("try_creative"), _ns)
for _g in ("_gen_poem", "_gen_story", "_gen_riddle", "_gen_toast"):
    _ns[_g] = {**{"_gen_poem": _POEM, "_gen_story": _STORY, "_gen_riddle": _RIDDLE, "_gen_toast": _TOAST}}[_g]
_CREATIVE = _ns["try_creative"]


class TestCreative(unittest.TestCase):
    def test_poem(self):
        out = _POEM("Напиши стихотворение про зиму")
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), 20)
        self.assertIn("зим", out.lower())

    def test_story(self):
        out = _STORY("Сочини рассказ о коте")
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), 30)

    def test_riddle(self):
        out = _RIDDLE("Придумай загадку")
        self.assertIn("загадка", out.lower())

    def test_toast(self):
        out = _TOAST("Напиши тост")
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), 20)

    def test_creative_returns_string_for_poem(self):
        out = _CREATIVE("Напиши стихотворение про весну")
        self.assertIsInstance(out, str)
        self.assertGreater(len(out), 20)

    def test_creative_returns_none_for_factual(self):
        # Фактический вопрос НЕ должен считаться креативным.
        out = _CREATIVE("что такое НДС")
        self.assertIsNone(out)

    def test_creative_toast(self):
        out = _CREATIVE("Напиши шуточный тост")
        self.assertIsInstance(out, str)


if __name__ == "__main__":
    unittest.main()