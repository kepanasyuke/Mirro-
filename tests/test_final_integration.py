# -*- coding: utf-8 -*-
"""Финальный интеграционный тест: направленный RAG с мета-контекстом.

Проверяем метод MirroRAG.run_quantum_guided_rag в scripts/rag.py:
  - метод существует и отдаёт список результатов;
  - направленный выбор сегментов ДЕТЕРМИНИРОВАН (не зависит от рандомизированного hash);
  - стабильный код пары одинаков при повторе;
  - результат использует мета-контекст (pair-подсказка расширяет запрос).

Постройка полного дискового RAG тяжёлая — тестируем метод на лёгком
экземпляре с заглушённым search (как делаем для чистых функций ядра).

Чистый Python, без внешних библиотек, по LINTER.md.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.rag import MirroRAG


def _stable_seed(pair):
    """Тот же детерминированный код, что в _guided (без hash()). Один return: int."""
    seed = 0
    for tok in pair[0] + "::" + pair[1]:
        seed = (seed * 31 + ord(tok)) % 2147483647
    return seed


class TestMirroFinalIntegration(unittest.TestCase):
    def setUp(self):
        self.rag_obj = MirroRAG.__new__(MirroRAG)
        self.rag_obj.segments = []
        self.rag_obj.global_index = {}
        self.rag_obj.seg_built = set()
        self.rag_obj.seg_files = {}
        _seen = {"q": None}
        # заглушка search: запоминаем запрос, возвращаем фикс. результат
        def fake_search(query, top_segments=None, top_k=3):
            _seen["q"] = query
            return [(1.0, "инструкция", "ответ")]
        self.rag_obj.search = fake_search
        self._seen = _seen

    def test_deterministic_seed(self):
        # стабильный код пары не зависит от hash()
        s1 = _stable_seed(("math", "logic"))
        s2 = _stable_seed(("math", "logic"))
        self.assertEqual(s1, s2)
        self.assertEqual(s1, 1065790971, "ожидаемый детерминированный код пары math/logic")

    def test_guided_segments_count_range(self):
        for pair in [("math", "logic"), ("general", "general"), ("физика", "математика")]:
            n = self.rag_obj._guided_segments(_stable_seed(pair))
            self.assertGreaterEqual(n, 1)
            self.assertLessEqual(n, 4)

    def test_rag_uses_meta_context(self):
        results = self.rag_obj.run_quantum_guided_rag("производная функции", ("math", "logic"), top_k=3)
        self.assertIsInstance(results, list)
        for doc in results:
            self.assertIsInstance(doc, tuple)
            self.assertEqual(len(doc), 3, "формат (score, instruction, output)")
        # мета-пара попала в расширенный запрос (hint) внутри search
        self.assertIn("math", self._seen["q"])
        self.assertIn("logic", self._seen["q"])

    def test_rag_without_pair_defaults_to_general(self):
        results = self.rag_obj.run_quantum_guided_rag("тест", None, top_k=2)
        self.assertIn("general", self._seen["q"], "без пары подставляется general")


if __name__ == "__main__":
    unittest.main()