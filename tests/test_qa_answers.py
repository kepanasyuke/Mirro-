# -*- coding: utf-8 -*-
"""Регрессионные тесты качества ответов Mirro (вопрос → ответ).

Гоняет набор QA-пар из tests/qa_cases.py по живому API Mirro на 127.0.0.1:3443
и проверяет, что ответ:
  * не пустой и не слишком короткий;
  * содержит ожидаемое ключевое слово (expect), если задано;
  * НЕ содержит мусорное/«рваное» слово (forbid), если задано.

Если сервер не запущен — тесты пропускаются (не падают).
Токен берётся из MIRRO_TOKEN или по умолчанию test-secret-123.

Запуск:  python -m unittest tests.test_qa_answers -v
"""
import json
import os
import unittest
import urllib.request
import urllib.error

from tests.qa_cases import CASES

HOST = "127.0.0.1"
PORT = 3443
BASE = f"http://{HOST}:{PORT}"
TOKEN = os.environ.get("MIRRO_TOKEN", "test-secret-123")


def _server_up():
    ok = False
    try:
        req = urllib.request.Request(
            BASE + "/health", method="GET",
            headers={"Authorization": "Bearer " + TOKEN})
        with urllib.request.urlopen(req, timeout=3) as resp:
            ok = resp.status == 200
    except Exception:
        ok = False
    return ok


def ask(question):
    body = {"model": "mirro/default",
            "messages": [{"role": "user", "content": question}]}
    req = urllib.request.Request(
        BASE + "/v1/chat/completions",
        data=json.dumps(body).encode("utf-8"),
        headers={"Content-Type": "application/json",
                 "Authorization": "Bearer " + TOKEN},
        method="POST")
    with urllib.request.urlopen(req, timeout=30) as resp:
        data = json.loads(resp.read().decode("utf-8"))
    msg = (data.get("choices") or [{}])[0].get("message", {})
    return (msg.get("content") or "").strip().lower()


def _check_case(case):
    q = case["question"]
    answer = ask(q)
    min_len = case.get("min_len", 8)
    note = "ok"
    passed = True
    if len(answer) < min_len:
        passed = False
        note = f"слишком короткий ответ (< {min_len})"
    elif case.get("forbid") and case["forbid"].lower() in answer:
        passed = False
        note = f"запрещённый мусор «{case['forbid']}» встречен"
    elif case.get("expect") and case["expect"].lower() not in answer:
        passed = False
        note = f"ожидалось «{case['expect']}», но не найдено"
    return passed, note


class TestQARegression(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.up = _server_up()

    def setUp(self):
        if not self.up:
            self.skipTest("Сервер Mirro не запущен — QA-тесты пропущены")

    def _run_case(self, i):
        case = CASES[i]
        ok, note = _check_case(case)
        self.assertTrue(ok, note)

    def test_qa_case_01(self): self._run_case(0)
    def test_qa_case_02(self): self._run_case(1)
    def test_qa_case_03(self): self._run_case(2)
    def test_qa_case_04(self): self._run_case(3)
    def test_qa_case_05(self): self._run_case(4)
    def test_qa_case_06(self): self._run_case(5)
    def test_qa_case_07(self): self._run_case(6)
    def test_qa_case_08(self): self._run_case(7)
    def test_qa_case_09(self): self._run_case(8)
    def test_qa_case_10(self): self._run_case(9)
    def test_qa_case_11(self): self._run_case(10)
    def test_qa_case_12(self): self._run_case(11)
    def test_qa_case_13(self): self._run_case(12)
    def test_qa_case_14(self): self._run_case(13)


if __name__ == "__main__":
    unittest.main()
