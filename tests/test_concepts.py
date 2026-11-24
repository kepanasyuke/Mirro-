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

    def test_verb_phrase_gets_colon(self):
        text = concepts._russian_text({"topic": "сортировка слиянием",
                                       "what": "делим массив пополам и сливаем части"})
        self.assertIn("Сортировка слиянием:", text)
        self.assertNotIn("это делим", text)

    def test_noun_phrase_keeps_definition(self):
        text = concepts._russian_text({"topic": "стек", "what": "структура данных с порядком LIFO"})
        self.assertIn("Стек — это структура данных", text)

    def test_bad_wiki_pair_skipped(self):
        # «graph» и «граффити» — разные статьи, пару не берём
        pairs = concepts._wikidata_pairs()
        self.assertNotEqual(pairs.get("graph"), ("граффити",))

    def test_graffiti_is_not_graph(self):
        found = concepts.find("что такое граффити")
        self.assertTrue(found is None or found["concept"]["name"] != "graph")

    def test_multiword_label_does_not_take_foreign_key(self):
        # «сорная трава» не делает «траву» алиасом сорняка: это отдельное понятие
        registry = concepts.build()
        weed = registry.get("weed") or {}
        self.assertNotIn("трава", weed.get("aliases") or ())
        self.assertIsNotNone(registry.get("трава"))

    def test_single_word_bridge_alias_stays(self):
        # одиночная подпись ручного моста остаётся алиасом темы
        registry = concepts.build()
        graph = registry.get("graph") or {}
        self.assertIn("граф", graph.get("aliases") or ())

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
        # «дарт» не должно цепляться за «дар»; случай с «docker» больше не
        # годится: тема docker появилась в базе и ищется уже целиком
        self.assertIsNone(concepts.find("дар"))

    def test_whole_word_alias_still_matches(self):
        found = concepts.find("что такое смелость")
        self.assertIsNotNone(found)
        self.assertEqual(found["alias"], "смелость")


if __name__ == "__main__":
    unittest.main()
