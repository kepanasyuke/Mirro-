# -*- coding: utf-8 -*-
"""Сквозная проверка всей цепочки: вопрос -> понятие -> план -> машина -> ответ.

Юнит-тесты проверяют шаги по отдельности; этот файл — всю дорогу сразу, на
настоящей базе. Он же ловит регрессии, если кто-то поменяет формат реестра,
графа или плана: тогда падает не «где-то», а здесь.

Проверки не привязаны к конкретным темам: понятия подбираются динамически,
потому что база растёт.

Запуск:  python tests/test_neuro_pipeline.py
"""
import os
import unittest

os.environ["NEURO_NO_GAP"] = "1"

from algos import concepts, lookup, neuro_answer, plan_machine, plan_router


def pick(with_ru=True, with_causes=False):
    """Имя понятия под условие (русский текст / причины), иначе None."""
    from algos import causality
    for concept in concepts.build().values():
        if not concept.get("en") or not concept.get("aliases"):
            continue
        if bool(concept.get("ru")) != with_ru:
            continue
        if with_causes and not causality.has_causes(concept):
            continue
        return concept["name"]
    return None


class TestChain(unittest.TestCase):
    """Цепочка целиком."""

    @unittest.skipUnless(pick(True), "нет понятий с русским текстом")
    def test_russian_question_gives_russian_answer(self):
        name = pick(True)
        answer = plan_router.answer_text("что такое " + name.replace("_", " "))
        self.assertTrue(answer)
        self.assertFalse(answer.startswith("What"))

    @unittest.skipUnless(pick(False), "нет понятий только с английским")
    def test_english_only_concept_is_honest(self):
        name = pick(False)
        answer = plan_router.answer_text("what is " + name.replace("_", " ") + "?")
        self.assertTrue(answer)
        self.assertIn("Описание есть только по-английски", answer)

    def test_mixed_question_finds_latin_concept(self):
        found = lookup.find("как работает mean")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "mean")

    def test_unknown_question_falls_through(self):
        self.assertIsNone(plan_router.answer_text("абракадабра ззз"))

    def test_plan_runs_on_machine(self):
        steps = neuro_answer.plan_steps("what is music?")
        executed = plan_machine.run_plan(steps, neuro_answer._plan_operations)
        self.assertGreater(executed["steps"], 0)
        self.assertEqual(executed["error"], "")

    def test_compare_mentions_both_sides(self):
        text = plan_router.answer_text("чем отличается aperture от cleft")
        self.assertTrue(text)
        self.assertIn("aperture", text)
        self.assertIn("cleft", text)

    @unittest.skipUnless(pick(True, with_causes=True), "нет понятий с причинами")
    def test_why_uses_cause_or_says_none(self):
        name = pick(True, with_causes=True)
        text = plan_router.answer_text("почему " + name.replace("_", " "))
        self.assertTrue(text)
        self.assertTrue("Причина" in text or "причин" in text.lower())

    def test_intents_are_distinct(self):
        pairs = {("что такое стек"): "definition", ("почему луна"): "why",
                 ("с чем связана музыка"): "links"}
        for question, intent in pairs.items():
            self.assertEqual(plan_router.classify(question), intent)


if __name__ == "__main__":
    unittest.main()
