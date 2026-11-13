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


class TestResponseChainRobustness(unittest.TestCase):
    """Цепочка try_* не должна рвать ответ и не должна отдавать None пустым.

    Корень дефекта: ветка `else` после прямого обработчика в build_response
    выполнялась всегда, поэтому веб-поиск перекрывал уже найденный ответ
    графа/многочастного разбора.
    """

    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def test_search_stages_keep_explicit_answer(self):
        kept = {"content": "ответ графа", "strategy": "graph_infer"}
        _prompt, result = self.mc._answer_by_search_stages("что такое граф", "ru", "", kept)
        self.assertEqual(result["strategy"], "graph_infer")
        self.assertEqual(result["content"], "ответ графа")

    def test_search_stages_never_return_none_when_broken(self):
        def boom(*_a, **_k):
            raise RuntimeError("сломанный поиск")
        original = self.mc._search_best
        self.mc._search_best = boom
        try:
            _prompt, result = self.mc._answer_by_search_stages("вопрос", "general", "")
        finally:
            self.mc._search_best = original
        self.assertIsInstance(result, dict)
        self.assertTrue(result.get("content"))

    def test_web_first_none_or_string_does_not_leak(self):
        original = self.mc._try_web_first
        for bad in (None, "", "не dict"):
            self.mc._try_web_first = lambda *_a, _v=bad, **_k: _v
            try:
                self.assertIsNone(self.mc._try_web_first_guard("вопрос"))
            finally:
                self.mc._try_web_first = original

    def test_web_first_exception_is_swallowed(self):
        original = self.mc._try_web_first
        def boom(*_a, **_k):
            raise RuntimeError("сеть недоступна")
        self.mc._try_web_first = boom
        try:
            self.assertIsNone(self.mc._try_web_first_guard("вопрос"))
        finally:
            self.mc._try_web_first = original

    def test_first_stage_exception_returns_none(self):
        original = self.mc._clarify_guess
        def boom(*_a, **_k):
            raise RuntimeError("сломанное уточнение")
        self.mc._clarify_guess = boom
        try:
            self.assertIsNone(self.mc._guarded_first_stage("вопрос"))
        finally:
            self.mc._clarify_guess = original

    def test_first_stage_rejects_dict_without_content(self):
        original = self.mc._clarify_guess
        self.mc._clarify_guess = lambda *_a, **_k: {"content": "", "strategy": "clarify"}
        try:
            self.assertIsNone(self.mc._guarded_first_stage("вопрос"))
        finally:
            self.mc._clarify_guess = original

    def test_voice_or_none_drops_empty_voicing(self):
        original = self.mc._voice
        self.mc._voice = lambda *_a, **_k: ""
        try:
            self.assertIsNone(self.mc._voice_or_none("ответ", "вопрос", "web"))
        finally:
            self.mc._voice = original

    def test_fallback_chain_marks_web_confidence(self):
        original_web = self.mc.try_web
        self.mc.try_web = lambda *_a, **_k: "ответ из интернета"
        try:
            result = self.mc._fallback_chain("вопрос")
        finally:
            self.mc.try_web = original_web
        self.assertEqual(result["strategy"], "web")
        self.assertEqual(result["confidence"], 0.45)

    def test_text_of_normalises_non_string_content(self):
        self.assertEqual(self.mc._text_of({"content": None}), "")
        self.assertEqual(self.mc._text_of({"content": {"a": 1}}), "{'a': 1}")
        self.assertEqual(self.mc._text_of({"content": "строка"}), "строка")
        self.assertEqual(self.mc._text_of(None), "")


class TestChatContract(unittest.TestCase):
    """Контракт /v1/chat/completions без поднятия сервера (прямой вызов хендлера)."""

    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def _handler(self):
        h = self.mc.MirroAPI.__new__(self.mc.MirroAPI)
        h.sent = []
        h.wfile = _FakeWriter(h.sent)
        h._json = lambda data, status=200: h.sent.append(("json", status, data))
        h.send_response = lambda status: None
        h.send_header = lambda *a, **k: None
        h.end_headers = lambda: None
        h.wfile.flush = lambda: None
        return h

    def setUp(self):
        self._orig_build = self.mc.build_response
        self.mc.build_response = lambda prompt, cluster, context="": {
            "content": "первая строка\nвторая строка", "strategy": "base",
            "thinking": ["шаг"], "plan": "план", "source": "база знаний"}

    def tearDown(self):
        self.mc.build_response = self._orig_build

    def test_empty_messages_returns_400(self):
        h = self._handler()
        h._handle_chat({"messages": []})
        self.assertEqual(h.sent[0][0], "json")
        self.assertEqual(h.sent[0][1], 400)
        self.assertIn("error", h.sent[0][2])

    def test_json_payload_has_reasoning_and_content(self):
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": "привет"}]})
        kind, _status, payload = h.sent[-1]
        self.assertEqual(kind, "json")
        message = payload["choices"][0]["message"]
        self.assertTrue(message["content"])
        self.assertIn("reasoning_content", message)
        self.assertEqual(payload["model"], "mirro-evolutionary-v4")

    def test_stream_sends_one_event_per_line_and_done(self):
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": "привет"}], "stream": True})
        raw = b"".join(h.sent)
        self.assertTrue(raw.endswith(b"data: [DONE]\n\n"))
        events = [e for e in raw.decode("utf-8").split("\n\n") if e]
        self.assertEqual(len(events), 3)

    def test_stream_events_are_valid_json(self):
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": "привет"}], "stream": True})
        raw = b"".join(h.sent).decode("utf-8")
        for event in raw.split("\n\n"):
            if event.startswith("data:") and "[DONE]" not in event:
                import json as _j
                self.assertIsInstance(_j.loads(event[len("data:"):].strip()), dict)

    def test_non_string_content_does_not_crash_stream(self):
        self.mc.build_response = lambda *a, **k: {"content": None, "strategy": "base"}
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": "вопрос"}], "stream": True})

    def test_stream_never_emits_literal_backslash_n(self):
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": "привет"}], "stream": True})
        raw = b"".join(h.sent)
        self.assertNotIn(b"data: " + chr(92).encode() + b"n", raw)

    def test_stream_keeps_cyrillic_unescaped(self):
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": "привет"}], "stream": True})
        raw = b"".join(h.sent).decode("utf-8")
        self.assertIn("первая строка", raw)

    def test_giant_input_is_accepted(self):
        big = "слово " * 20000
        h = self._handler()
        h._handle_chat({"messages": [{"role": "user", "content": big}]})
        self.assertEqual(h.sent[-1][0], "json")


class _FakeWriter:
    def __init__(self, sink):
        self.sink = sink

    def write(self, data):
        self.sink.append(data)


if __name__ == "__main__":
    unittest.main()