# -*- coding: utf-8 -*-
"""Интеграционный тест: общение с живым Mirro API на 127.0.0.1:3443.

Запуск:  python -m unittest discover -s tests -v
Если сервер Mirro не запущен — тесты пропускаются (не падают).

Проверяет: health, /v1/models, chat completion (non-stream), формат ответа,
обработку пустых/битых запросов.
"""
import json, unittest, urllib.request, urllib.error

HOST = "127.0.0.1"
PORT = 3443
BASE = f"http://{HOST}:{PORT}"


def _server_up():
    try:
        req = urllib.request.Request(BASE + "/health", method="GET")
        with urllib.request.urlopen(req, timeout=3) as resp:
            return resp.status == 200
    except Exception:
        return False


class TestLiveAPI(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = _server_up()
        if not cls.up:
            cls.skip_tests = True
        else:
            cls.skip_tests = False

    def setUp(self):
        if self.skip_tests:
            self.skipTest("Сервер Mirro не запущен — интеграционные тесты пропущены")

    def _request(self, method, path, body=None):
        data = json.dumps(body).encode("utf-8") if body is not None else None
        req = urllib.request.Request(BASE + path, data=data, method=method,
                                     headers={"Content-Type": "application/json"})
        try:
            with urllib.request.urlopen(req, timeout=10) as resp:
                raw = resp.read().decode("utf-8")
                return resp.status, (json.loads(raw) if raw else {})
        except urllib.error.HTTPError as e:
            raw = e.read().decode("utf-8") if e.readable() else ""
            return e.code, (json.loads(raw) if raw else {})

    def test_health_ok(self):
        status, body = self._request("GET", "/health")
        self.assertEqual(status, 200)
        self.assertEqual(body.get("status") or body.get("name"), "Mirro")
        self.assertIn("total_examples", body)

    def test_models_listed(self):
        status, body = self._request("GET", "/v1/models")
        self.assertEqual(status, 200)
        ids = [m["id"] for m in body.get("data", [])]
        self.assertIn("mirro/default", ids)

    def test_chat_greeting(self):
        status, body = self._request("POST", "/v1/chat/completions", {
            "model": "mirro/default",
            "messages": [{"role": "user", "content": "Привет!"}],
        })
        self.assertEqual(status, 200)
        choices = body.get("choices", [])
        self.assertTrue(choices)
        self.assertIn("content", choices[0].get("message", {}))
        self.assertIsInstance(choices[0]["message"]["content"], str)

    def test_empty_messages_bad_request(self):
        status, body = self._request("POST", "/v1/chat/completions", {"messages": []})
        self.assertEqual(status, 400)

    def test_unknown_route_404(self):
        status, _ = self._request("GET", "/no-such-route")
        self.assertEqual(status, 404)


if __name__ == "__main__":
    unittest.main()