# -*- coding: utf-8 -*-
"""Юнит-тесты для Mirro Providers (слой внешних ИИ-провайдеров).

Запуск:  python -m unittest discover -s tests -v
Тесты чистой логики (разбор ключей, статус). Сетевые вызовы не выполняются.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.providers import _resolve_key, PROVIDERS, status


class TestProviders(unittest.TestCase):
    def test_known_provider_cfg(self):
        self.assertIn("deepseek", PROVIDERS)
        self.assertIn("openai", PROVIDERS)
        self.assertEqual(PROVIDERS["deepseek"]["model"], "deepseek-chat")

    def test_resolve_key_no_key_returns_empty(self):
        # При отсутствии env и файла секретов — пустая строка
        for name in ("deepseek", "openai"):
            self.assertEqual(_resolve_key(name), "")

    def test_status_never_raises(self):
        st = status()
        self.assertIsInstance(st, dict)
        self.assertTrue(set(st) <= set(PROVIDERS.keys()))

    def test_system_prompt_present(self):
        import scripts.providers as p
        self.assertIn("Mirro", p.SYS_PROMPT)


if __name__ == "__main__":
    unittest.main()