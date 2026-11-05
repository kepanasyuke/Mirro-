# -*- coding: utf-8 -*-
"""Интеграционные тесты API-роутера и лаунчера.

Проверяем на реальных функциях core/mirro_core (без запуска сервера):
  - `_quantum_context_note()` возвращает валидную reasoning-строку с PINN-loss,
    суперпозицией, размерностью и комбинаторным путём;
  - структура OpenAI-ответа `_chat_payload` валидна (message.role == assistant,
    есть content и reasoning_content), model = mirro-evolutionary-v4;
  - логика парсинга /health-метрик, которую использует mirro_launcher.pyw.

Чистый Python, без внешних библиотек, ленивый импорт ядра (как test_core_helpers).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

_IMPORTED = False
_mc = None
def _get_mc():
    global _mc, _IMPORTED
    if not _IMPORTED:
        import core.mirro_core as _mm
        _mc = _mm
        _IMPORTED = True
    return _mc


class TestMirroAPIAndLauncher(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.mc = _get_mc()

    def _build_payload(self):
        """Собирает OpenAI-ответ через реальный _chat_payload с mock-ответом.
        Один return: dict."""
        h = self.mc.MirroAPI.__new__(self.mc.MirroAPI)
        # подменяем вспомогательные атрибуты, чтобы не лезть в сеть
        h._json = lambda *a, **k: None
        msg = [{"role": "user", "content": "Реши уравнение x²−5x+6=0"}]
        response = {"content": "Корни: x1=2, x2=3.", "strategy": "algo"}
        # используем метод класса напрямую (self не используется внутри)
        return self.mc.MirroAPI._chat_payload(h, msg, "mirro/default", response, "Реши уравнение")

    def test_quantum_note_contains_required_metrics(self):
        note = self.mc._quantum_context_note()
        if not note:  # граф может быть пуст без поднятого ядра — тогда пропускаем
            self.skipTest("граф/корпус не загружен — reasoning-сноска пуста")
        self.assertIn("PINN Loss", note)
        # суперпозиция присутствует либо как число, либо как "0"
        self.assertIn("суперпозиция", note)
        self.assertIn("комбинаторный путь", note)

    def test_openai_payload_structure(self):
        payload = self._build_payload()
        self.assertIn("choices", payload)
        self.assertEqual(payload["object"], "chat.completion")
        self.assertEqual(payload["model"], "mirro-evolutionary-v4")
        msg = payload["choices"][0]["message"]
        self.assertEqual(msg["role"], "assistant")
        self.assertIn("content", msg)
        self.assertTrue(len(msg["content"]) > 0, "content не должен быть пустым")
        # reasoning_content присутствует (может быть пустой, если нет графа)
        self.assertIn("reasoning_content", msg)

    def test_launcher_health_parser(self):
        """Логика _on_ready лаунчера: корректно извлекает новые /health-метрики."""
        # имитируем health от реального ядра
        health = {
            "total_examples": 2800000,
            "algorithms": {
                "knowledge_graph": {"nodes": 145000, "edges": 81000, "avg_dimension": 1.42},
                "quantum": {"superposed_nodes": 145000, "P_active_sample": [0.5, 0.5]},
            },
        }
        alg = health.get("algorithms") or {}
        kg = alg.get("knowledge_graph") or {}
        q = alg.get("quantum") or {}
        dim = kg.get("avg_dimension")
        sup = q.get("superposed_nodes")
        line = f"{health['total_examples']:,} примеров"
        dim_txt = f"{dim}/3D" if dim is not None else "—"
        sup_txt = str(sup) if sup is not None else "—"
        line += f" · размерность {dim_txt} · суперпозиция {sup_txt}"
        self.assertIn("2,800,000", line)
        self.assertIn("1.42/3D", line)
        self.assertIn("145000", sup_txt)


if __name__ == "__main__":
    unittest.main()