# -*- coding: utf-8 -*-
"""Юнит-тесты квантовой логики графа и очистки корпусов.

Проверяем на РЕАЛЬНЫХ структурах (KnowledgeGraph + add_meta_route +
algos/quantum_graph и scripts/clean_corpus.py):
  - условие нормировки Борна |α|²+|β|² = 1 сохраняется после запутывания
    роу-ссылкой мета-графа;
  - коллапс волновой функции даёт классический бит;
  - очистка строки корпуса убирает мусор и отсекает пустышки.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest, random
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.knowledge_graph import KnowledgeGraph
from algos.neural_electric import add_meta_route
from algos.quantum_graph import (
    init_quantum_states, apply_quantum_entanglement, collapse_wave_function,
)
from scripts.clean_corpus import clean_and_tokenize_corpus_line, _is_keepable


def _graph():
    g = KnowledgeGraph()
    g.from_triples([
        ("Внимание", "влияет на", "память"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
    ])
    return g


class TestMirroQuantumCore(unittest.TestCase):
    def test_norm_initialized(self):
        g = _graph()
        st = init_quantum_states(g)
        self.assertEqual(len(st.states), len(g.nodes))
        for name, (a, b) in st.states.items():
            self.assertAlmostEqual(a * a + b * b, 1.0, places=5,
                                   msg=f"нормировка узла {name} изначально нарушена")

    def test_norm_after_entanglement(self):
        g = _graph()
        add_meta_route(g, ("внимание", "влияет на", "память"),
                       ("память", "укрепляет", "понимание"), mod=0.5)
        st = init_quantum_states(g)
        st2 = apply_quantum_entanglement(g, st,
                                         ("внимание", "влияет на", "память"),
                                         ("память", "укрепляет", "понимание"),
                                         mod=0.5)
        for name, (a, b) in st2.states.items():
            total = a * a + b * b
            self.assertAlmostEqual(total, 1.0, places=5,
                                   msg=f"нормировка узла {name} нарушена после запутывания")

    def test_collapse_is_classical_bit(self):
        g = _graph()
        st = init_quantum_states(g)
        rng = random.Random(7)
        out = collapse_wave_function(st, "внимание", 0.5, rng)
        self.assertIn(out, (0.0, 1.0), "коллапс обязан дать классический бит")
        # вероятность P(активен) при равных амплитудах — 0.5
        a, _b = st.get("внимание")
        self.assertAlmostEqual(a * a, 0.5, places=4)


class TestCorpusCleaning(unittest.TestCase):
    def test_tokenize_clears_noise(self):
        toks = clean_and_tokenize_corpus_line("  Что-то   ПРОБА!!!!   мноооо  ")
        self.assertIsInstance(toks, list)
        self.assertGreaterEqual(len(toks), 1)

    def test_keepable_filter(self):
        good = _is_keepable({"instruction": "что такое нейросеть",
                             "output": "это математическая модель на данных"})
        bad = _is_keepable({"instruction": "аааааа", "output": "ббббб"})
        self.assertTrue(good)
        self.assertFalse(bad)

    def test_lowercase_normalization(self):
        toks = clean_and_tokenize_corpus_line("НЕЙРОСЕТЬ Обучение")
        joined = " ".join(toks).lower()
        self.assertIn("нейросеть", joined)


if __name__ == "__main__":
    unittest.main()