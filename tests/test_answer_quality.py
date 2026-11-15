import os
import sys
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.mirro_core import answer_looks_bad


class CompareAnswerQualityTest(unittest.TestCase):
    """Ответ на «что общего у X и Y» обязан говорить хотя бы об одном из них."""

    def test_corpus_snippet_for_comparison_is_rejected(self):
        answer = "Объясню просто: Construct 2 Руководство к программе. Надеюсь, понятно."
        self.assertTrue(answer_looks_bad("что общего у кошка и собака", answer))

    def test_relevant_comparison_is_kept(self):
        answer = "Кошка и собака — домашние животные, оба хищники из отряда Carnivora."
        self.assertFalse(answer_looks_bad("что общего у кошка и собака", answer))

    def test_factual_guard_still_works(self):
        self.assertTrue(answer_looks_bad("что такое нейросеть",
                                         "Construct 2 Руководство к программе"))

    def test_plain_answer_is_not_rejected(self):
        answer = "У меня всё в порядке, спасибо, работаю над задачами."
        self.assertFalse(answer_looks_bad("как дела", answer))


if __name__ == "__main__":
    unittest.main()
