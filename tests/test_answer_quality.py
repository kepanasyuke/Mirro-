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

    def test_final_gate_targets_comparisons(self):
        from core.mirro_core import _needs_final_gate
        self.assertTrue(_needs_final_gate("чем отличается кошка от собаки"))
        self.assertTrue(_needs_final_gate("что общего у нейросети и алгоритма"))
        self.assertFalse(_needs_final_gate("что такое алгоритм"))
        self.assertFalse(_needs_final_gate("сколько будет 2+2"))

    def test_english_links_are_not_shown_in_russian_frame(self):
        from algos.compose import related_text
        self.assertEqual(related_text(["память", "plan", "внимание", "trust"]),
                         "память, внимание")
        self.assertEqual(related_text(["plan", "trust"]), "")
        self.assertEqual(related_text(["фотосинтез -"]), "")

    def test_russian_answer_skips_english_links(self):
        from algos.neuro_answer import russian_answer
        text = russian_answer({"name": "океан", "ru": "Океан — водоём."}, ["plan", "море"])
        self.assertIn("море", text)
        self.assertNotIn("plan", text)

    def test_concept_text_reads_like_a_definition(self):
        from algos.concepts import _russian_text
        text = _russian_text({"topic": "налог",
                              "what": "обязательный платёж в пользу государства",
                              "ex": "подоходный налог удерживают из зарплаты"})
        self.assertTrue(text.startswith("Налог — это "), text)
        self.assertIn("Например:", text)
        self.assertNotIn("Налог. ", text)


class ConceptVersusFunctionTest(unittest.TestCase):
    """«Что такое X» — вопрос о понятии, а не о функции в коде."""

    def test_concept_question_does_not_return_function_card(self):
        from algos.module_knowledge import try_function_knowledge
        self.assertIsNone(try_function_knowledge("что такое энтропия"))

    def test_function_question_still_gets_card(self):
        from algos.module_knowledge import try_function_knowledge
        self.assertIsNotNone(try_function_knowledge("что делает binary_search"))

    def test_new_glosses_answer_with_definitions(self):
        from algos.module_knowledge import try_definition
        for question, word in (("что такое энтропия", "энтропия"),
                               ("что такое инфляция", "инфляция"),
                               ("что такое фотон", "фотон"),
                               ("что такое океан", "океан"),
                               ("что такое налог", "налог"),
                               ("что такое врач", "врач"),
                               ("что такое тревога", "тревога"),
                               ("что такое футбол", "футбол"),
                               ("что такое музыка", "музыка"),
                               ("что такое закон", "закон"),
                               ("что такое кошка", "кошка"),
                               ("что такое живопись", "живопись"),
                               ("что такое углерод", "углерод"),
                               ("что такое браузер", "браузер"),
                               ("что такое экзамен", "экзамен"),
                               ("что такое договор", "договор")):
            text = try_definition(question) or ""
            self.assertIn(word, text.lower())
            self.assertNotIn("связан с", text)


if __name__ == "__main__":
    unittest.main()
