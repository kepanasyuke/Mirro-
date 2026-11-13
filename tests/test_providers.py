# -*- coding: utf-8 -*-
"""Юнит-тесты для Mirro Providers (слой внешних ИИ-провайдеров).

Запуск:  python -m unittest discover -s tests -v
Тесты чистой логики (разбор ключей, статус). Сетевые вызовы не выполняются.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.providers import _resolve_key, PROVIDERS, status


class _FakeResp:
    """Подмена urllib-ответа: status + тело без реальной сети."""

    def __init__(self, body=b"", status=200):
        self._body = body
        self.status = status

    def read(self):
        return self._body

    def __enter__(self):
        return self

    def __exit__(self, *args):
        return False


class _PatchedCall(unittest.TestCase):
    """Общая обвязка: подменяет urlopen и ключ, возвращает результат вызова."""

    def setUp(self):
        import scripts.providers as p
        self.p = p
        self._old_urlopen = p.urllib.request.urlopen
        self._old_key = p._resolve_key
        p._resolve_key = lambda provider: "test-key"

    def tearDown(self):
        self.p.urllib.request.urlopen = self._old_urlopen
        self.p._resolve_key = self._old_key

    def call_with(self, resp=None, exc=None, provider="deepseek"):
        def fake_urlopen(req, timeout=None):
            if exc is not None:
                raise exc
            return resp
        self.p.urllib.request.urlopen = fake_urlopen
        return self.p._call_provider(provider, [{"role": "user", "content": "q"}])


class TestProviders(_PatchedCall):
    def test_known_provider_cfg(self):
        self.assertIn("deepseek", PROVIDERS)
        self.assertIn("openai", PROVIDERS)
        self.assertEqual(PROVIDERS["deepseek"]["model"], "deepseek-chat")

    def test_resolve_key_no_key_returns_empty(self):
        # При отсутствии env и файла секретов — пустая строка
        self.p._resolve_key = self._old_key
        old_env = {name: os.environ.pop(cfg["env"], None) for name, cfg in PROVIDERS.items()}
        try:
            self.assertEqual(_resolve_key("deepseek"), "")
        finally:
            for name, value in old_env.items():
                if value is not None:
                    os.environ[PROVIDERS[name]["env"]] = value

    def test_status_never_raises(self):
        self.p._resolve_key = self._old_key
        st = status()
        self.assertIsInstance(st, dict)
        self.assertTrue(set(st) <= set(PROVIDERS.keys()))

    def test_system_prompt_present(self):
        self.assertIn("Mirro", self.p.SYS_PROMPT)


class TestCompletionParsing(_PatchedCall):
    def test_normal_answer(self):
        body = b'{"choices": [{"message": {"content": "42"}}]}'
        self.assertEqual(self.call_with(_FakeResp(body)), "42")

    def test_non_2xx_status_is_reported(self):
        # раньше 200-проверки не было вообще
        body = b'{"choices": [{"message": {"content": "stale cache"}}]}'
        out = self.call_with(_FakeResp(body, status=503))
        self.assertTrue(out.startswith("[провайдер deepseek: ошибка 503]"))

    def test_html_body_is_not_an_answer(self):
        out = self.call_with(_FakeResp(b"<html>502 Bad Gateway</html>"))
        self.assertIsNone(out)

    def test_empty_choices_is_none(self):
        self.assertIsNone(self.call_with(_FakeResp(b'{"choices": []}')))

    def test_empty_content_is_none(self):
        body = b'{"choices": [{"message": {"content": "   "}}]}'
        self.assertIsNone(self.call_with(_FakeResp(body)))

    def test_non_string_content_is_none(self):
        body = b'{"choices": [{"message": {"content": ["x"]}}]}'
        self.assertIsNone(self.call_with(_FakeResp(body)))

    def test_http_error_reports_code(self):
        import urllib.error
        err = urllib.error.HTTPError("https://x", 401, "Unauthorized", {}, None)
        out = self.call_with(exc=err)
        self.assertIn("401", out)

    def test_timeout_is_reported_not_swallowed(self):
        import socket
        out = self.call_with(exc=socket.timeout("timed out"))
        self.assertTrue(out.startswith("[провайдер deepseek: таймаут"))

    def test_connection_error_is_none(self):
        import urllib.error
        out = self.call_with(exc=urllib.error.URLError("no route to host"))
        self.assertIsNone(out)


class TestFallback(_PatchedCall):
    def test_fallback_skips_error_strings(self):
        answers = iter(["", "второй провайдер"])
        self.p._resolve_key = lambda provider: "key"

        def fake_call(provider, messages, timeout=30):
            return next(answers)

        old_call = self.p._call_provider
        self.p._call_provider = fake_call
        try:
            self.assertEqual(self.p.fallback("q"), "второй провайдер")
        finally:
            self.p._call_provider = old_call


if __name__ == "__main__":
    unittest.main()
