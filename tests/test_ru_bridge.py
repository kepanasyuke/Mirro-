# -*- coding: utf-8 -*-
"""Тесты русско-английского моста, графа понятий и добычи определений.

Проверяют то, ради чего мост сделан: русский вопрос находит понятие
английской базы, граф даёт связи, а ответ остаётся русским или честно
помечает пробел. Сеть и сервер не нужны.
"""
import unittest

from algos import concepts
from algos.concept_graph import EDGES, neighbours
from algos.english_kb import _EN_KB
from algos.ru_bridge import RU_KEYS, bridge, find_topic, related, ru_definition
from algos.ru_descriptions import RU_TEXT
from scripts.ru_definitions import extract_from_text


class TestBridgeKeys(unittest.TestCase):
    """Ключи моста ссылаются на существующие темы."""

    def test_all_topics_exist(self):
        missing = [topic for topic in RU_KEYS if topic not in _EN_KB]
        self.assertEqual(missing, [], f"ключи ссылаются на несуществующие темы: {missing}")

    def test_keys_are_russian(self):
        bad = [topic for topic, keys in RU_KEYS.items()
               if not keys or not any(any("\u0400" <= c <= "\u04ff" for c in key) for key in keys)]
        self.assertEqual(bad, [], f"у темы нет русских ключей: {bad}")


class TestFindTopic(unittest.TestCase):
    """Русский вопрос находит английскую тему."""

    def test_abstract_nouns_are_found(self):
        cases = {"что такое мудрость": "wisdom",
                 "объясни, что такое смелость": "courage",
                 "что такое дружба": "friendship"}
        wrong = {query: find_topic(query) for query, expected in cases.items()
                 if find_topic(query) != expected}
        self.assertEqual(wrong, {}, f"тема найдена неверно: {wrong}")

    def test_unknown_topic_is_none(self):
        self.assertIsNone(find_topic("что такое энтропия Шеннона"))

    def test_word_forms_match(self):
        self.assertEqual(find_topic("расскажи про мудрости"), find_topic("что такое мудрость"))


class TestRussianAnswer(unittest.TestCase):
    """Ответ остаётся русским; где русского текста нет — мост молчит."""

    def test_known_concept_answers_in_russian(self):
        found = bridge("что такое память")
        self.assertIsNotNone(found)
        self.assertIn("память", found["content"].lower())
        self.assertEqual(found["strategy"], "ru_bridge")

    def test_missing_russian_text_is_silent(self):
        # берём тему, у которой русского текста действительно нет: список
        # описаний растёт, и жёстко зашитая тема быстро обрастает текстом
        from algos.english_kb import _EN_KB
        from algos.ru_descriptions import RU_TEXT
        silent = [topic for topic in _EN_KB if topic not in RU_TEXT]
        self.assertTrue(silent, "все темы уже описаны по-русски")
        self.assertIsNone(ru_definition(silent[0]))

    def test_comparison_names_both_concepts(self):
        found = related("что общего у страха и тревоги")
        self.assertIsNotNone(found)
        text = found["content"].lower()
        self.assertIn("страх", text)
        self.assertIn("тревога", text)
        self.assertIn("различа", text)

    def test_comparison_labels_are_distinct(self):
        # «тревога» и «тревожность» — разные понятия из разных тем
        found = related("чем отличается тревога от тревожности")
        self.assertIsNotNone(found)
        self.assertIn("тревожность", found["content"].lower())

    def test_described_concept_answers_in_russian(self):
        found = bridge("что такое мудрость")
        self.assertIsNotNone(found)
        self.assertIn("Мудрость", found["content"])


class TestRelations(unittest.TestCase):
    """Связи понятий берутся из графа определений."""

    def test_graph_has_edges(self):
        self.assertGreater(len(EDGES), 100)

    def test_known_contrast(self):
        self.assertIn("fissure", neighbours("cleft", depth=1))

    def test_russian_text_gives_edges(self):
        # «память … факты и навыки» — русское описание связывает память с навыком
        self.assertIn("skill", neighbours("memory", depth=1))

    def test_two_concepts_answer(self):
        found = related("чем отличается смелость от терпения")
        self.assertIsNotNone(found)
        self.assertIn("смелость", found["content"])

    def test_single_concept_with_edges_answers(self):
        found = related("с чем связана память")
        self.assertIsNotNone(found)
        self.assertIn("память", found["content"])

    def test_single_concept_without_edges_is_silent(self):
        self.assertIsNone(related("с чем связано доверие"))


class TestRegistryLink(unittest.TestCase):
    """Общий реестр понятий видит русские слова через мост."""

    def test_russian_word_resolves_to_english_topic(self):
        found = concepts.find("что такое мудрость")
        self.assertIsNotNone(found)
        self.assertEqual(found["concept"]["name"], "wisdom")


class TestDefinitionExtraction(unittest.TestCase):
    """Определения добываются из текста и мусор отбрасывается."""

    def test_keeps_definition_and_drops_noise(self):
        text = ("Память — это способность сохранять и воспроизводить информацию. "
                "Почитайте в критике ОС «Фантом» о вечной памяти.")
        found = extract_from_text(text, "память")
        self.assertEqual(len(found), 1)
        self.assertIn("способность сохранять", found[0])

    def test_word_forms_are_recognised(self):
        text = "Под памятью понимают запись следов опыта."
        found = extract_from_text(text, "память")
        self.assertEqual(len(found), 1)


class TestRussianDescriptions(unittest.TestCase):
    """Русские описания написаны для существующих тем и не пустые."""

    def test_keys_exist(self):
        missing = [topic for topic in RU_TEXT if topic not in _EN_KB]
        self.assertEqual(missing, [], f"описание ссылается на несуществующую тему: {missing}")

    def test_texts_are_russian_and_complete(self):
        bad = [topic for topic, text in RU_TEXT.items()
               if len(text) < 40 or not any("\u0400" <= char <= "\u04ff" for char in text)]
        self.assertEqual(bad, [], f"описание не по-русски или слишком короткое: {bad}")

    def test_registry_uses_descriptions(self):
        found = concepts.find("что такое мудрость")
        self.assertIsNotNone(found)
        self.assertTrue(found["concept"]["ru"])


if __name__ == "__main__":
    unittest.main()
