# -*- coding: utf-8 -*-
"""Проверки ответа по понятию: прямой путь и путь через план на машине.

Тесты не привязаны к конкретным темам: база растёт каждую минуту, поэтому
понятия «с русским текстом» и «только с английским» ищутся динамически.

Запуск:  python tests/test_neuro_answer.py
"""
import os
import unittest

os.environ["NEURO_NO_GAP"] = "1"

from algos import concepts, neuro_answer as na


def pick(with_ru):
    """Имя понятия с русским текстом или, наоборот, только с английским."""
    for concept in concepts.build().values():
        has_ru = bool(concept["ru"])
        if concept["en"] and has_ru == with_ru and len(concept["aliases"]) > 0:
            return concept["name"]
    return None


RUSSIAN = pick(True)
ENGLISH_ONLY = pick(False)


class TestDirect(unittest.TestCase):
    """Прямой путь: реестр -> русский текст."""

    @unittest.skipUnless(RUSSIAN, "в базе нет понятий с русским текстом")
    def test_russian_entry_answers(self):
        answer = na.answer("что такое " + RUSSIAN.replace("_", " "))
        self.assertTrue(answer)
        self.assertNotIn("По-русски это пока не описано", answer)

    @unittest.skipUnless(ENGLISH_ONLY, "в базе нет понятий только с английским")
    def test_english_entry_answers_in_frame(self):
        answer = na.answer("what is " + ENGLISH_ONLY.replace("_", " ") + "?")
        self.assertTrue(answer)
        self.assertIn("Описание есть только по-английски", answer)

    def test_unknown_query_is_none(self):
        self.assertIsNone(na.answer("zzz qqq xyzzy"))

    def test_short_query_is_none(self):
        self.assertIsNone(na.answer("привет"))


class TestPlan(unittest.TestCase):
    """Путь через план: шаги исполняются машиной."""

    @unittest.skipUnless(RUSSIAN, "в базе нет понятий с русским текстом")
    def test_plan_finds_russian_entry(self):
        found = na.try_plan("что такое " + RUSSIAN.replace("_", " "))
        self.assertIsNotNone(found)
        self.assertTrue(found["has_ru"])
        self.assertGreater(found["steps"], 0)

    @unittest.skipUnless(ENGLISH_ONLY, "в базе нет понятий только с английским")
    def test_plan_finds_english_entry(self):
        found = na.try_plan("what is " + ENGLISH_ONLY.replace("_", " ") + "?")
        self.assertIsNotNone(found)
        self.assertFalse(found["has_ru"])
        self.assertGreater(found["steps"], 0)

    @unittest.skipUnless(RUSSIAN, "в базе нет понятий с русским текстом")
    def test_plan_answer_matches_direct(self):
        query = "что такое " + RUSSIAN.replace("_", " ")
        self.assertEqual(na.answer(query), na.answer_by_plan(query))

    def test_plan_returns_none_for_unknown(self):
        self.assertIsNone(na.answer_by_plan("zzz qqq xyzzy"))

    def test_plan_steps_shape(self):
        steps = na.plan_steps("what is music?")
        self.assertEqual(len(steps), 2)
        self.assertEqual(steps[0][1], "concept")
        self.assertEqual(steps[1][2], ["=concept"])

    @unittest.skipUnless(ENGLISH_ONLY, "в базе нет понятий только с английским")
    def test_missing_russian_is_honest(self):
        found = na.try_plan("what is " + ENGLISH_ONLY.replace("_", " ") + "?")
        self.assertIn("Описание есть только по-английски", found["answer"])


if __name__ == "__main__":
    unittest.main()
