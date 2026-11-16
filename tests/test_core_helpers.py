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
        self.mc.try_web = lambda *_a, **_k: "ответ из интернета на вопрос"
        try:
            result = self.mc._fallback_chain("вопрос")
        finally:
            self.mc.try_web = original_web
        self.assertEqual(result["strategy"], "web")
        self.assertEqual(result["confidence"], 0.45)

    def test_irrelevant_web_answer_is_ignored(self):
        original_web = self.mc.try_web
        self.mc.try_web = lambda *_a, **_k: "Налог на добавленную стоимость"
        try:
            result = self.mc._fallback_chain("кварковый резонатор")
        finally:
            self.mc.try_web = original_web
        self.assertNotEqual(result.get("strategy"), "web")

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

    def test_messages_not_a_list_returns_400(self):
        h = self._handler()
        h._handle_chat({"messages": "привет"})
        self.assertEqual(h.sent[0][1], 400)


class TestRequestBodyParsing(unittest.TestCase):
    """_read не должен молча подменять не-UTF8 тело ASCII-мусором."""

    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def _read_handler(self, raw, content_length=None):
        h = self.mc.MirroAPI.__new__(self.mc.MirroAPI)

        class _Headers(dict):
            def get(self, name, default=None):
                if name.lower() == "content-length":
                    return str(len(raw) if content_length is None else content_length)
                return default

        h.headers = _Headers()
        h.rfile = _RawReader(raw)
        return h

    def test_invalid_utf8_is_rejected(self):
        raw = b'{"messages": [{"role": "user", "content": "\xff\xfe\xfa"}]}'
        with self.assertRaises(UnicodeDecodeError):
            self._read_handler(raw)._read()

    def test_negative_content_length_is_zero(self):
        body = self._read_handler(b"{}", content_length=-5)._read()
        self.assertIsNone(body)

    def test_non_numeric_content_length_rejected(self):
        h = self._read_handler(b"{}")
        h.headers = {"Content-Length": "много"}
        self.assertIsNone(h._read())

    def test_valid_body_is_parsed(self):
        body = self._read_handler('{"messages": [{"role": "user", "content": "привет"}]}'.encode("utf-8"))._read()
        self.assertEqual(body["messages"][0]["content"], "привет")


class _RawReader:
    def __init__(self, data):
        self.data = data

    def read(self, size=-1):
        return self.data if size is None or size < 0 else self.data[:size]


class TestCallLogging(unittest.TestCase):
    """log_call не должен ронять ответ клиента из-за диска/счётчиков."""

    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def test_utc_stamp_is_iso_without_utcnow(self):
        stamp = self.mc._utc_now_iso()
        self.assertRegex(stamp, r"^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}")
        self.assertNotIn("+00:00", stamp)

    def test_call_log_entry_has_all_audit_fields(self):
        """entry аудита пишется в logs/calls.jsonl со всеми полями.

        Проверяем через реальный LOGS: счётчики stats.json и models/ не трогаются
        (пишется одна строка лога, как и в бою)."""
        import json as _j
        original = self.mc.LOGS
        self.mc.LOGS = _TempLogs()
        try:
            self.mc._append_call_log("вопрос", "ru", "mirro-base", 12, True, tokens=7)
            written = self.mc.LOGS.calls_path.read_text("utf-8").strip()
        finally:
            self.mc.LOGS.cleanup()
            self.mc.LOGS = original
        entry = _j.loads(written)
        self.assertEqual(entry["cluster"], "ru")
        self.assertEqual(entry["tokens"], 7)
        self.assertEqual(entry["prompt_len"], 6)
        self.assertRegex(entry["ts"], r"^20\d\d-")

    def test_log_call_survives_unwritable_log_dir(self):
        core_obj = self.mc.MirroCore.__new__(self.mc.MirroCore)
        core_obj.stats = {"calls": 0, "clusters_used": {}, "total_examples": 0}
        core_obj._save_json = lambda *_a, **_k: (_ for _ in ()).throw(OSError("диск"))
        original = self.mc.LOGS
        self.mc.LOGS = _BrokenLogs()
        try:
            core_obj.log_call("вопрос", "ru", "mirro-base", 5, True)
        finally:
            self.mc.LOGS = original
        self.assertEqual(core_obj.stats["calls"], 1)


class _TempLogs:
    """Временная папка логов вне репозитория: пишет calls.jsonl и удаляется."""

    def __init__(self):
        import tempfile
        from pathlib import Path
        self.root = Path(tempfile.mkdtemp(prefix="mirro-logs-"))
        self.calls_path = self.root / "calls.jsonl"

    def mkdir(self, **_kwargs):
        return None

    def __truediv__(self, name):
        return self.root / name

    def cleanup(self):
        import shutil
        shutil.rmtree(self.root, ignore_errors=True)


class _BrokenLogs:
    """LOGS, который не даёт ни создать папку, ни открыть файл."""

    def mkdir(self, **_kwargs):
        raise OSError("нет прав")

    def __truediv__(self, name):
        return self

    def __fspath__(self):
        return "broken-log-path"

    def open(self, *_a, **_k):
        raise OSError("нет записи")


class TestHealthEndpoint(unittest.TestCase):
    """GET /health не должен падать, если индекс/граф ещё не прогрет."""

    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def _get(self, route="/health"):
        h = self.mc.MirroAPI.__new__(self.mc.MirroAPI)
        h.path = route
        sent = []
        h._json = lambda data, status=200: sent.append((status, data))
        self.mc.MirroAPI._route_GET_dispatch(h, route)
        return sent[0]

    def test_health_returns_200_and_algorithms_block(self):
        status, payload = self._get()
        self.assertEqual(status, 200)
        self.assertIn("algorithms", payload)
        self.assertIsInstance(payload["algorithms"], dict)

    def test_health_graph_block_has_full_metric_set(self):
        _status, payload = self._get()
        graph = payload["algorithms"]["knowledge_graph"]
        for key in ("nodes", "edges", "avg_dimension", "density", "edges_per_node",
                    "central_nodes", "mean_degree"):
            self.assertIn(key, graph)
        self.assertIsInstance(graph["central_nodes"], list)

    def test_health_neuromodulators_include_rhythm(self):
        _status, payload = self._get()
        nm_block = payload["algorithms"]["neuromodulators"]
        self.assertIn("rhythm", nm_block)
        self.assertIsInstance(nm_block["rhythm"], str)

    def test_health_quantum_and_immunity_blocks_always_present(self):
        _status, payload = self._get()
        self.assertIn("superposed_nodes", payload["algorithms"]["quantum"])
        for key in ("quarantined", "n_routes", "fatigued_edges"):
            self.assertIn(key, payload["algorithms"]["immunity"])

    def test_health_never_calls_immune_scan_without_graph_nodes(self):
        """Пустой граф не должен доходить до иммунного скана и засчитывать карантин."""
        calls = []
        import algos.knowledge_graph as kg_mod
        import algos.immune_sentinel as immune_mod
        original_scan = immune_mod.run_graph_immune_scan
        def spy(*args, **kwargs):
            calls.append(len(args[0].nodes))
            return original_scan(*args, **kwargs)
        immune_mod.run_graph_immune_scan = spy
        original_kg = kg_mod.kg
        kg_mod.kg = kg_mod.KnowledgeGraph()
        try:
            _status, payload = self._get()
        finally:
            immune_mod.run_graph_immune_scan = original_scan
            kg_mod.kg = original_kg
        self.assertEqual(calls, [])
        self.assertEqual(payload["algorithms"]["immunity"]["quarantined"], 0)

    def test_health_survives_broken_metric_modules(self):
        import algos.zero_dimensional as zd_mod
        original = zd_mod.dimension_of_understanding
        def boom(*_a, **_k):
            raise RuntimeError("размерность не считается")
        zd_mod.dimension_of_understanding = boom
        try:
            status, payload = self._get()
        finally:
            zd_mod.dimension_of_understanding = original
        self.assertEqual(status, 200)
        self.assertIsInstance(payload["algorithms"], dict)


class TestPostHandlers(unittest.TestCase):
    """POST-хендлеры должны отвечать всегда — без падения при не-dict теле."""

    @classmethod
    def setUpClass(cls):
        cls.mc = _get_core()

    def _handler(self, body):
        h = self.mc.MirroAPI.__new__(self.mc.MirroAPI)
        h.path = "/v1/feedback"
        h.sent = []
        h._read = lambda: body
        h._json = lambda data, status=200: h.sent.append((status, data))
        return h

    def test_feedback_with_non_dict_body_answers_500_not_raises(self):
        h = self._handler(["не", "dict"])
        h._post_feedback()
        self.assertEqual(h.sent[0][0], 500)
        self.assertEqual(h.sent[0][1]["status"], "error")

    def test_feedback_with_none_body_is_guarded(self):
        """_read() отдаёт None (сломанное/пустое тело) — список не должен падать.

        Внешний try уже ловит это и отдаёт 500, тест переименован: страховка
        цепочки фиксируется на уровне вызова.
        """
        h = self._handler(None)
        h._post_feedback()
        self.assertEqual(h.sent[0][0], 500)

    def test_feedback_with_number_like_query_does_not_raise(self):
        h = self._handler({"query": 42, "response": "ответ", "liked": True})
        h._post_feedback()
        self.assertIsInstance(h.sent[0][1], dict)


class _FakeWriter:
    def __init__(self, sink):
        self.sink = sink

    def write(self, data):
        self.sink.append(data)


if __name__ == "__main__":
    unittest.main()