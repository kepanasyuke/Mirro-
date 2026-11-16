# -*- coding: utf-8 -*-
"""Проверка единого реестра понятий: обе базы попадают, поиск находит.

Запуск:  python tests/test_concepts.py
"""
import unittest

from algos import concepts


class TestRegistry(unittest.TestCase):
    """Реестр собирается из обеих баз и ничего не теряет."""

    def test_every_english_topic_is_present(self):
        from algos.english_kb import _EN_KB
        registry = concepts.build()
        missing = [name for name in _EN_KB if concepts._normal(name) not in registry]
        self.assertEqual(missing, [])

    def test_every_russian_entry_is_present(self):
        from algos.module_knowledge import _KNOWLEDGE
        registry = concepts.build()
        missing = [name for name in _KNOWLEDGE if concepts._normal(name) not in registry]
        self.assertEqual(missing, [])

    def test_russian_entries_have_russian_text(self):
        from algos.module_knowledge import _KNOWLEDGE
        registry = concepts.build()
        empty = [name for name in _KNOWLEDGE
                 if not registry[concepts._normal(name)]["ru"]]
        self.assertEqual(empty, [])

    def test_english_topics_have_aliases(self):
        registry = concepts.build()
        empty = [c["name"] for c in registry.values() if c["en"] and not c["aliases"]]
        self.assertEqual(empty, [])

    def test_stats_add_up(self):
        info = concepts.stats()
        self.assertEqual(info["with_ru"] + info["en_only"], info["concepts"])
        self.assertGreater(info["concepts"], 2000)


class TestLookup(unittest.TestCase):
    """Поиск по алиасам: русские записи и английские темы."""

    def test_english_question_finds_topic(self):
        found = concepts.find("what is music?")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "music")

    def test_russian_question_finds_russian_entry(self):
        found = concepts.find("что такое пузырьковая сортировка")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "bubble_sort")
        self.assertTrue(found["concept"]["ru"])

    def test_unknown_question_returns_none(self):
        self.assertIsNone(concepts.find("zzz qqq xyzzy"))

    def test_short_aliases_are_skipped(self):
        found = concepts.find("  в  ")
        self.assertIsNone(found)

    def test_alias_does_not_match_inside_a_word(self):
        # «dock» не должно цепляться за «docker», «дарт» — за «дар»
        self.assertIsNone(concepts.find("что такое docker"))
        self.assertIsNone(concepts.find("дар"))

    def test_whole_word_alias_still_matches(self):
        found = concepts.find("что такое смелость")
        self.assertIsNotNone(found)
        self.assertEqual(found["alias"], "смелость")


if __name__ == "__main__":
    unittest.main()
