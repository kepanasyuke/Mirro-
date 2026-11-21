# -*- coding: utf-8 -*-
"""Проверки диспетчера планов: тип вопроса, разбор пары, тексты ответов.

Запуск:  python tests/test_plan_router.py
"""
import os
import unittest

os.environ["NEURO_NO_GAP"] = "1"

from algos import plan_router


class TestClassify(unittest.TestCase):
    """Тип вопроса определяется по маркерам."""

    def test_definition(self):
        self.assertEqual(plan_router.classify("что такое стек"), "definition")

    def test_definition_english(self):
        self.assertEqual(plan_router.classify("what is music?"), "definition")

    def test_compare(self):
        self.assertEqual(plan_router.classify("чем отличается стек от очереди"), "compare")

    def test_compare_english(self):
        self.assertEqual(plan_router.classify("difference between stack and queue"), "compare")

    def test_links(self):
        self.assertEqual(plan_router.classify("с чем связана музыка"), "links")

    def test_why(self):
        self.assertEqual(plan_router.classify("почему небо синее"), "why")

    def test_unknown(self):
        self.assertEqual(plan_router.classify("привет"), "unknown")


class TestSplit(unittest.TestCase):
    """Пара сущностей из вопроса сравнения."""

    def test_split_by_ot(self):
        left, right = plan_router.split_pair("чем отличается стек от очереди?")
        self.assertIn("стек", left)
        self.assertEqual(right, "очереди")

    def test_split_by_and(self):
        left, right = plan_router.split_pair("сравни стек и очередь")
        self.assertIn("стек", left)
        self.assertEqual(right, "очередь")

    def test_no_pair(self):
        self.assertEqual(plan_router.split_pair("что такое стек"), (None, None))


class TestPlans(unittest.TestCase):
    """Набор шагов под каждый тип."""

    def test_definition_plan_has_two_steps(self):
        self.assertEqual(len(plan_router.plan_for("definition", "x")), 2)

    def test_compare_plan_has_seven_steps(self):
        self.assertEqual(len(plan_router.plan_for("compare", "a и b")), 7)

    def test_unknown_has_no_plan(self):
        self.assertEqual(plan_router.plan_for("unknown", "x"), [])


class TestRender(unittest.TestCase):
    """Тексты не врут о том, чего нет."""

    def test_links_text(self):
        text = plan_router.render("links", {"concept": {"name": "music"}, "links": ["art"]})
        self.assertEqual(text, "music — связи: art.")

    def test_links_without_neighbours(self):
        text = plan_router.render("links", {"concept": {"name": "music"}, "links": []})
        self.assertEqual(text, "music — связи: нет.")

    def test_why_admits_no_causality(self):
        text = plan_router.render("why", {"concept": {"name": "music"}, "links": ["art"]})
        self.assertTrue(text.startswith("Причинных связей в базе нет"))

    def test_compare_text_has_all_parts(self):
        values = {"left": {"name": "a"}, "right": {"name": "b"},
                  "links_left": ["x"], "links_right": ["y"],
                  "shared": ["z"], "only_left": ["x"], "only_right": ["y"]}
        text = plan_router.render("compare", values)
        self.assertIn("Общее: z", text)
        self.assertIn("Только у a: x", text)
        self.assertIn("Только у b: y", text)

    def test_empty_values_give_empty_text(self):
        self.assertEqual(plan_router.render("compare", {}), "")
        self.assertEqual(plan_router.render("links", {}), "")

    def test_compare_adds_definitions_without_contrast(self):
        values = {"left": {"name": "love", "ru": "Любовь — это глубокое чувство."},
                  "right": {"name": "friendship", "ru": "Дружба — близкие отношения."},
                  "links_left": ["жизнь"], "links_right": ["trust"],
                  "shared": [], "only_left": ["жизнь"], "only_right": ["trust"]}
        text = plan_router.render("compare", values, "чем отличается любовь от дружбы")
        self.assertIn("По описаниям: Любовь — глубокое чувство", text)
        self.assertIn("Дружба — близкие отношения", text)
        self.assertNotIn("Любовь — Любовь", text)

    def test_compare_without_definitions_stays_short(self):
        values = {"left": {"name": "a", "ru": ""}, "right": {"name": "b", "ru": ""},
                  "links_left": [], "links_right": [], "shared": []}
        self.assertNotIn("По описаниям", plan_router.render("compare", values))

    def test_compare_side_words_removed(self):
        left, right = plan_router.split_pair("сходство любви и дружбы")
        self.assertEqual((left, right), ("любви", "дружбы"))

    def test_why_without_cause_gives_definition(self):
        values = {"concept": {"name": "rain", "ru": "Дождь — осадки в виде капель воды."},
                  "links": []}
        text = plan_router.render("why", values, "почему идёт дождь")
        self.assertIn("Причинных связей в базе нет", text)
        self.assertIn("Дождь — осадки", text)

    def test_compare_one_side_missing(self):
        values = {"left": None, "right": {"name": "friendship",
                                         "ru": "Дружба — близкие отношения."},
                  "links_left": [], "links_right": ["trust"], "shared": []}
        text = plan_router.render("compare", values, "сходство любви и дружбы")
        self.assertIn("любви", text)
        self.assertIn("Дружба", text)


class TestRealAnswers(unittest.TestCase):
    """Живые вопросы на настоящих базах."""

    def test_definition_answer_non_empty(self):
        text = plan_router.answer_text("что такое стек")
        self.assertTrue(text)

    def test_links_answer_mentions_relation(self):
        text = plan_router.answer_text("с чем связана музыка")
        self.assertTrue("связи:" in text or "связано с" in text)

    def test_compare_answer_builds(self):
        text = plan_router.answer_text("чем отличается стек от очереди")
        self.assertTrue(text)
        detailed = "Общее:" in text
        honest = "связей в графе у них нет" in text
        self.assertTrue(detailed or honest)

    def test_unknown_returns_none(self):
        self.assertIsNone(plan_router.answer_text("привет"))


class TestStats(unittest.TestCase):
    """Вопросы о самой базе."""

    def test_classify_total(self):
        self.assertEqual(plan_router.classify("сколько всего понятий"), "stats")

    def test_classify_russian(self):
        self.assertEqual(plan_router.classify("сколько понятий с русским текстом"), "stats")

    def test_plan_is_single_step(self):
        self.assertEqual(len(plan_router.plan_for("stats", "x")), 1)

    def test_render_total(self):
        values = {"data": {"concepts": 100, "with_ru": 20, "en_only": 80, "causes": 5}}
        text = plan_router.render("stats", values, "сколько всего понятий")
        self.assertIn("100", text)
        self.assertIn("20", text)

    def test_render_russian_variant(self):
        values = {"data": {"concepts": 100, "with_ru": 20, "en_only": 80, "causes": 5}}
        self.assertIn("20 из 100", plan_router.render("stats", values, "сколько с русским текстом"))

    def test_render_causes_variant(self):
        values = {"data": {"concepts": 100, "with_ru": 20, "en_only": 80, "causes": 5}}
        self.assertIn("5", plan_router.render("stats", values, "сколько с причинами"))

    def test_live_answer(self):
        text = plan_router.answer_text("сколько всего понятий")
        self.assertTrue(text)
        self.assertIn("Понятий всего", text)

    def test_word_in_query(self):
        self.assertEqual(plan_router._stat_word("сколько тем про математику"), "математику")

    def test_word_ignores_language_branches(self):
        self.assertEqual(plan_router._stat_word("сколько понятий с русским текстом"), "")

    def test_render_word_variant(self):
        values = {"data": {"concepts": 100, "with_ru": 20, "word": "стек",
                           "word_count": 3, "word_ru": 2}}
        text = plan_router.render("stats", values, "сколько про стек")
        self.assertIn("«стек»", text)
        self.assertIn("3 из 100", text)


if __name__ == "__main__":
    unittest.main()
