# -*- coding: utf-8 -*-
"""Юнит-тесты адаптивного характера и темперамента (algos/voice_temperament.py).

Проверяем на реальных функциях:
  - детекция психотипа по химии (дофамин/серотонин);
  - лингвистическая фильтрация токенов под психотип;
  - интеграция try_stylize_generated_output в ядре (тихое поведение при ошибке).

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.voice_temperament import determine_voice_temperament, try_apply_temperament_filters


class TestMirroVoiceTemperament(unittest.TestCase):
    def setUp(self):
        self.mock_tokens = ["математика", "код", "структура", "искусство", "театр", "ии"]

    def test_choleric_temperament_detection(self):
        chem = {"dopamine": 0.8, "serotonin": 0.3}
        self.assertEqual(determine_voice_temperament(chem), "хаотичный_холерик")

    def test_philosopher_temperament_detection(self):
        chem = {"dopamine": 0.1, "serotonin": 1.5}
        self.assertEqual(determine_voice_temperament(chem), "флегматичный_философ")

    def test_balanced_temperament_detection(self):
        chem = {"dopamine": 0.2, "serotonin": 0.8}
        self.assertEqual(determine_voice_temperament(chem), "сбалансированный")

    def test_philosopher_filters_short_words(self):
        result = try_apply_temperament_filters(self.mock_tokens, "флегматичный_философ")
        self.assertNotIn("код", result, "короткое слово «код» должно быть отфильтровано")
        self.assertNotIn("ии", result, "короткое слово «ии» должно быть отфильтровано")
        self.assertIn("математика", result)

    def test_core_stylize_returns_tuple(self):
        import core.mirro_core as mc
        text, temper = mc.try_stylize_generated_output("тестовая строка", {"dopamine": 0.8, "serotonin": 0.3})
        self.assertIsInstance(text, str)
        self.assertEqual(temper, "хаотичный_холерик")


if __name__ == "__main__":
    unittest.main()