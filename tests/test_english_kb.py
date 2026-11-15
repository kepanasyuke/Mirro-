# -*- coding: utf-8 -*-
"""Тесты целостности английской базы знаний (algos/english_kb.py).

Ловят дефекты реестра тем, которые не видны при обычном импорте:
  * повтор темы в _TOPIC_TEST (одна тема — одна запись триггеров);
  * пустое/пробельное определение в _EN_KB;
  * тему без примера (нет маркера примера «For example / For instance / such as»);
  * расхождение: тема есть в _EN_KB, но её нет в _TOPIC_TEST (справке-триггерах);
  * битую кодировку (mojibake) в пользовательских строках;
  * регресс ключевого контракта try_english.

Только чтение базы, без сети и без запуска сервера.
Запуск:  python -m pytest tests/test_english_kb.py -q -p no:cacheprovider
"""
import importlib
import re
import unittest

from pathlib import Path

from algos.english_kb import _EN_KB, _TOPIC_TEST, try_english

_MOJIBAKE = re.compile("\u0420[\u0400-\u04ff]|\u0421[\u0400-\u04ff]")

SHADOWED_BY_LONGEST_KEY = [
]
# перекрытий не осталось: точное совпадение имени темы выигрывает у синонима


def _topic_names():
    """Имена тем из списка триггеров. Один return: list."""
    return [name for name, _ in _TOPIC_TEST]


def _triggers():
    """Все ключевые слова триггеров. Один return: list."""
    return [key for _, keys in _TOPIC_TEST for key in (keys or ())]


class TestKbRegistry(unittest.TestCase):
    def test_kb_is_non_empty_dict(self):
        self.assertIsInstance(_EN_KB, dict)
        self.assertGreater(len(_EN_KB), 1000)
        self.assertIsInstance(_TOPIC_TEST, list)
        self.assertGreater(len(_TOPIC_TEST), 1000)

    def test_no_duplicate_topics_in_registry(self):
        names = list(_EN_KB)
        dupes = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(dupes, [], f"повтор темы в _EN_KB: {dupes}")

    def test_no_duplicate_topics_in_trigger_list(self):
        names = _topic_names()
        dupes = sorted({n for n in names if names.count(n) > 1})
        self.assertEqual(dupes, [], f"повтор темы в _TOPIC_TEST: {dupes}")

    def test_no_duplicate_triggers_within_topic(self):
        offenders = [name for name, keys in _TOPIC_TEST
                     if len(set(keys or ())) != len(list(keys or ()))]
        self.assertEqual(offenders, [], f"повтор ключа внутри темы: {offenders}")

    def test_every_topic_has_definition(self):
        empty = [k for k, v in _EN_KB.items() if not isinstance(v, str) or not v.strip()]
        self.assertEqual(empty, [], f"пустое определение: {empty}")

    def test_every_definition_is_complete_sentence(self):
        """Определение — законченное предложение (не обрывок), длина в разумных пределах."""
        bad = [k for k, v in _EN_KB.items()
               if not v.rstrip().endswith((".", "!", "?")) or len(v.strip()) < 40 or len(v) > 3000]
        self.assertEqual(bad, [], f"оборванное определение: {bad}")

    def test_no_mojibake_in_definitions(self):
        bad = [k for k, v in _EN_KB.items() if _MOJIBAKE.search(v)]
        self.assertEqual(bad, [], f"битая кодировка в определении: {bad}")

    def test_no_mojibake_in_triggers(self):
        bad = [k for k in _triggers() if isinstance(k, str) and _MOJIBAKE.search(k)]
        self.assertEqual(bad, [], f"битая кодировка в триггере: {bad}")

    def test_registry_topics_are_covered_by_triggers(self):
        covered = set(_topic_names())
        missing = [k for k in _EN_KB if k not in covered]
        self.assertEqual(missing, [], f"тема есть в _EN_KB, но её нет в _TOPIC_TEST: {missing}")

    def test_trigger_topics_exist_in_registry(self):
        dangling = [n for n in _topic_names() if n not in _EN_KB]
        self.assertEqual(dangling, [], f"триггер без темы в _EN_KB: {dangling}")


class TestTryEnglishContract(unittest.TestCase):
    def test_returns_definition_for_known_topic(self):
        answer = try_english("what is a neural network?")
        self.assertIsInstance(answer, str)
        self.assertIn("Neural network", answer)

    def test_returns_none_for_russian_question(self):
        self.assertIsNone(try_english("расскажи про нейрон"))

    def test_returns_none_for_short_or_non_string(self):
        self.assertIsNone(try_english("hi"))
        self.assertIsNone(try_english(""))
        self.assertIsNone(try_english(None))
        self.assertIsNone(try_english(42))

    def test_each_trigger_topic_is_reachable(self):
        """Часть тем из _TOPIC_TEST отвечается по своему первому ключу.

        Пока все ключи короткие, try_english идёт в основной поиск и отдаёт
        ровно определение темы. Темы из SHADOWED_BY_LONGEST_KEY перебиваются
        ключом другой темы (стиль «мне объяснили»), поэтому здесь их пропускаем.
        """
        wrong = []
        for name, keys in _TOPIC_TEST:
            if name in SHADOWED_BY_LONGEST_KEY or not keys or not keys[0]:
                continue
            answer = try_english(f"what is {keys[0]}")
            if answer != _EN_KB.get(name):
                wrong.append((name, keys[0]))
        self.assertEqual(wrong, [], f"тема не отвечается по своему ключу: {wrong[:10]}")

    def test_shadowed_topic_list_matches_actual(self):
        """Список перебитых тем не расходится с реальным поведением базы."""
        actual = sorted({name for name, keys in _TOPIC_TEST
                         if keys and try_english(f"what is {keys[0]}") != _EN_KB.get(name)})
        self.assertEqual(actual, SHADOWED_BY_LONGEST_KEY)


class TestPartModules(unittest.TestCase):
    """english_kb_part* — каркас разбиения: срез реестра, а не вторая копия."""

    def _parts(self):
        root = Path(__file__).resolve().parent.parent / "algos"
        names = sorted(root.glob("english_kb_part*.py"))
        return [importlib.import_module("algos.%s" % path.stem) for path in names]

    def test_parts_are_slices_of_registry(self):
        wrong = []
        for mod in self._parts():
            for name, text in mod.TOPICS.items():
                if _EN_KB.get(name) != text:
                    wrong.append((mod.__name__, name))
        self.assertEqual(wrong, [], f"определение в part разошлось с _EN_KB: {wrong}")

    def test_parts_cover_existing_topics_only(self):
        missing = [(mod.__name__, n) for mod in self._parts()
                   for n in mod.TOPICS if n not in _EN_KB]
        self.assertEqual(missing, [], f"тема part-файла отсутствует в _EN_KB: {missing}")

    def test_parts_trigger_slices_match_names(self):
        wrong = [(mod.__name__, [n for n, _ in mod.TOPIC_TEST], list(mod.TOPICS))
                 for mod in self._parts()
                 if [n for n, _ in mod.TOPIC_TEST] != list(mod.TOPICS)]
        self.assertEqual(wrong, [], f"аргументы-триггеры part не совпадают с NAMES: {wrong}")


if __name__ == "__main__":
    unittest.main()
