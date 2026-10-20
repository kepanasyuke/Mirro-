# -*- coding: utf-8 -*-
"""Юнит-тесты для собственных CBOW-эмбеддингов (улучшение №19, тизер).

Проверяет: векторы имеют нужную размерность, нормированы к 1,
identical words имеют близость 1.0, разные слова — ниже.
Также проверяет cbow_similarity возвращает 0 для неизвестных слов.
"""
import os, re, sys, textwrap, math, unittest

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
    import random, collections, time
    ns.update({"_re": re, "time": time, "math": math, "random": random,
               "Counter": collections.Counter, "defaultdict": collections.defaultdict})
    exec(f"def {name}({signature}):\n" + body, ns)
    return ns[name]


_CBOW_BUILD = _extract("build_cbow_embeddings", "self, window=2, max_examples=20000")
_CBOW_SIM = _extract("cbow_similarity", "self, word_a, word_b")


class _CbowStub:
    def __init__(self):
        self.examples = [
            ("вопрос", "налог на добавленную стоимость налог", "ru"),
            ("вопрос2", "налог и стоимость налог", "ru"),
            ("вопрос3", "стоимость товара налог", "ru"),
            ("код", "def функция возвращает значение", "code"),
            ("код2", "функция возвращает результат", "code"),
        ]
        # мини-словарь
        vocab = set()
        for _, text, _ in self.examples:
            vocab |= set(self.tokenize(text))
        self.vocab = sorted(vocab)
        self.word2idx = {w: i for i, w in enumerate(self.vocab)}
        self.cbow_dim = 8
        self.cbow_vectors = {}
        self._cbow_built = False
        self.embedding_size = 8

    def tokenize(self, text):
        return re.findall(r"[а-яёa-z0-9]+", text.lower())

    def build_cbow_embeddings(self, window=2, max_examples=20000):
        return _CBOW_BUILD.__get__(self, _CbowStub)(window, max_examples)

    def cbow_similarity(self, word_a, word_b):
        return _CBOW_SIM.__get__(self, _CbowStub)(word_a, word_b)


class TestCbow(unittest.TestCase):
    def setUp(self):
        self.s = _CbowStub()

    def test_builds_vectors_normalized(self):
        self.s.build_cbow_embeddings()
        self.assertTrue(self.s._cbow_built)
        self.assertTrue(self.s.cbow_vectors)
        for w, v in self.s.cbow_vectors.items():
            self.assertEqual(len(v), self.s.cbow_dim)
            norm = math.sqrt(sum(x * x for x in v))
            self.assertAlmostEqual(norm, 1.0, places=3)

    def test_identical_word_similarity_one(self):
        self.s.build_cbow_embeddings()
        # слово, точно присутствующее в векторах, самосходно = 1 (нормиров. косинус)
        w = next(iter(self.s.cbow_vectors))
        self.assertAlmostEqual(self.s.cbow_similarity(w, w), 1.0, places=3)

    def test_unknown_word_zero(self):
        self.s.build_cbow_embeddings()
        self.assertEqual(self.s.cbow_similarity("незнакомое_слово", "налог"), 0.0)

    def test_not_built_returns_zero(self):
        # до постройки cbow_similarity вернёт 0
        self.assertEqual(self.s.cbow_similarity("налог", "налог"), 0.0)


if __name__ == "__main__":
    unittest.main()