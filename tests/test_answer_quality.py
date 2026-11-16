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

    def test_causal_question_needs_causal_answer(self):
        picture = "Эта фотография захватывает дух: высокое здание, небо ярко-голубое."
        self.assertTrue(answer_looks_bad("почему небо голубое", picture))

    def test_causal_answer_passes(self):
        answer = "Небо голубое из-за рассеяния солнечного света в атмосфере."
        self.assertFalse(answer_looks_bad("почему небо голубое", answer))


class ConceptVersusFunctionTest(unittest.TestCase):
    """«Что такое X» — вопрос о понятии, а не о функции в коде."""

    def test_concept_question_does_not_return_function_card(self):
        from algos.module_knowledge import try_function_knowledge
        self.assertIsNone(try_function_knowledge("что такое энтропия"))

    def test_function_question_still_gets_card(self):
        from algos.module_knowledge import try_function_knowledge
        self.assertIsNotNone(try_function_knowledge("что делает binary_search"))


if __name__ == "__main__":
    unittest.main()
