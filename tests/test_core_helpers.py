# -*- coding: utf-8 -*-
"""Юнит-тесты для helper-функций core/mirro_core, не требующих запуска сервера.

Тестируем чистые функции, которые можно импортировать без построения индекса:
  - answer_looks_bad()  — шлюз качества ответа
  - _provider_help_hint() — подсказка при недоступном провайдере
Сам импорт mirro_core создаёт экземпляр MirroCore() и грузит processed-базу
(~2.8M строк). Чтобы не делать это в каждом тесте, тесты подгружают его лениво
и только для функций, не зависящих от загруженного индекса.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Ленивый импорт: тяжёлая инициализация только один раз для набора.
_core = None
def _get_core():
    global _core
    if _core is None:
        import core.mirro_core as mc
        _core = mc
    return _core


class TestAnswerLooksBad(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def test_empty_answer_is_bad(self):
        self.assertTrue(self.mc.answer_looks_bad("вопрос", None))
        self.assertTrue(self.mc.answer_looks_bad("вопрос", "коротко"))

    def test_code_answer_to_factual_question_is_bad(self):
        q = "что такое ндс"
        a = "function foo() { return '<?php '; } console.log('x');"
        self.assertTrue(self.mc.answer_looks_bad(q, a))

    def test_good_answer_not_bad(self):
        q = "что такое ндс"
        a = "НДС — это налог на добавленную стоимость, который платит покупатель."
        self.assertFalse(self.mc.answer_looks_bad(q, a))

    def test_factual_question_with_unrelated_answer_is_bad(self):
        q = "что такое нейросеть"
        a = "Сегодня хорошая погода, солнце светит ярко."  # ни одного ключевого слова
        self.assertTrue(self.mc.answer_looks_bad(q, a))


class TestProviderHint(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def test_returns_string_even_without_provider(self):
        # При отсутствии ключа в любом окружении функция вернёт подсказку.
        hint = self.mc._provider_help_hint()
        self.assertIsInstance(hint, str)
        # Подсказка может быть пустой (если провайдер реально настроен) или содержать текст.
        # Проверяем лишь тип и отсутствие исключений.


if __name__ == "__main__":
    unittest.main()