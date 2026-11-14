# -*- coding: utf-8 -*-
"""Юнит-тесты диалоговой памяти (algos/dialogue_memory.py).

Проверяем то, что ломалось до правки в отчёте 2026-11-14/02-graph-memory:
  - вытесненные deque реплики не теряются, а уходят в резюме;
  - память восстанавливается из файла между «сессиями»;
  - на вопрос, которого в истории не было, не отвечаем «Помню: …».

Файл памяти — всегда во временном каталоге, data/ не трогается.
"""
import os
import sys
import tempfile
import unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos import dialogue_memory as dm_mod
from algos.dialogue_memory import DialogueMemory


class TestDialogueMemory(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self.path = os.path.join(self._tmp, "dm.json")

    def _memory(self, **kw):
        mem = DialogueMemory(**kw)
        mem.set_persist_path(self.path)
        return mem

    def test_evicted_turns_reach_summary(self):
        # реплики с РАЗНЫМИ словами: резюме хранит частотные слова, а не номера
        phrases = ["нейрон мозг сигнал", "граф связи узлы", "память внимание сон",
                   "python список кортеж", "вода кипит градус"]
        mem = self._memory(max_topics=8, max_context=6, summary_length=5)
        for i in range(20):
            mem.remember(phrases[i % len(phrases)], "ответ")
        # вытесненное из окна должно осесть в _pending/резюме, а не пропасть
        kept = " ".join(mem.summary) + " " + " ".join(
            " ".join(row[0]) for row in mem._pending)
        self.assertIn("нейрон", kept)

    def test_evicted_rows_are_not_silently_dropped(self):
        mem = self._memory(max_context=5, summary_length=50)
        for word in ("нейрон", "граф", "память", "список", "вода", "луна", "свет"):
            mem.remember(word + " тема понятие", "ответ")
        # ни одна реплика не должна исчезнуть без следа
        self.assertTrue(mem._pending or len(mem.context) == 7)

    def test_survives_new_session(self):
        mem = self._memory(max_context=10, summary_length=12)
        for i in range(12):
            mem.remember("термин%d слово%d метка%d" % (i, i, i), "ответ")
        fresh = self._memory(max_context=10, summary_length=12)
        fresh.load()
        self.assertGreater(len(fresh.context), 0)
        self.assertEqual(fresh.summary, mem.summary)

    def test_no_false_memory_of_unknown_topic(self):
        mem = self._memory()
        mem.remember("вода кипит градус", "ок")
        dm_mod.dm = mem
        answer = dm_mod._answer_topic("о чём мы говорили про квантовую хромодинамику")
        self.assertNotIn("Помню: мы говорили", answer)

    def test_known_topic_is_recalled(self):
        mem = self._memory()
        mem.remember("вода кипит градус", "ок")
        mem.remember("вода лёд пар", "ок")
        dm_mod.dm = mem
        answer = dm_mod._answer_topic("о чём мы говорили про вода лёд")
        self.assertIn("Помню", answer)

    def test_empty_input_ignored(self):
        mem = self._memory()
        mem.context.clear()          # изолируемся от загруженной истории
        self.assertEqual(mem.remember(""), [])
        self.assertEqual(len(mem.context), 0)


if __name__ == "__main__":
    unittest.main()
