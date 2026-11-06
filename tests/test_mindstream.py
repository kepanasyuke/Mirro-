# -*- coding: utf-8 -*-
"""Юнит-тесты внутреннего сознания (algos/mindstream.py).

Проверяем «думать самой» в четырёх направлениях:
  - инициатива: pick_topic/draft_thought порождают тему и мысль без вопроса;
  - рассуждение: reasoning_steps даёт видимую цепочку;
  - самообучение: learn_new_pair сохраняет пару и закрепляет тему в графе;
  - метапознание: try_metacognition отвечает на вопросы о собственном состоянии.

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.mindstream import MindStream, try_metacognition
from algos.knowledge_graph import KnowledgeGraph


class TestMindStream(unittest.TestCase):
    def setUp(self):
        self.ms = MindStream()

    def test_extract_topic_strips_wrapper(self):
        got = self.ms.extract_topic("расскажи что такое нейросеть и как она работает")
        self.assertIn("нейросеть", got)
        self.assertNotIn("расскажи", got)

    def test_pick_topic_falls_back_to_seed(self):
        picked = self.ms.pick_topic()
        self.assertIsInstance(picked, str)
        self.assertTrue(picked)

    def test_draft_thought_is_nonempty(self):
        thought = self.ms.draft_thought("нейросеть")
        self.assertIsInstance(thought, str)
        self.assertTrue(thought)

    def test_reasoning_steps_are_visible(self):
        steps = self.ms.reasoning_steps("нейросеть")
        self.assertGreaterEqual(len(steps), 3)
        self.assertTrue(all(isinstance(s, str) and s for s in steps))

    def test_learn_new_pair_persists(self):
        self.ms._kg = KnowledgeGraph()
        ok = self.ms.learn_new_pair("что такое нейросеть",
                                    "Нейросеть — модель, обучаемая на данных")
        self.assertTrue(ok)

    def test_metacognition_answers_self(self):
        self.ms.observe("пользователь спросил про сознание")
        ans = try_metacognition("осознаёшь ли ты себя")
        self.assertIsNotNone(ans)
        self.assertTrue(ans)


if __name__ == "__main__":
    unittest.main()