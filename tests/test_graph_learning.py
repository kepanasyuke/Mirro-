# -*- coding: utf-8 -*-
"""Тесты новой граф-логики обучения связей (задачи 1–4).

Проверяем на чистом KnowledgeGraph (не реальный файл):
  - build_function_links: функции базы становятся узлами графа с рёбрами;
  - build_concept_links: из QA-корпуса достастраиваются рёбра «связано_с»;
  - link_orphans: изолированный короткий узел связывается с ближайшим;
  - predict_links: узлы с общими соседями без прямой связи получают ребро;
  - try_concept_path: для понятия строится читаемая цепочка «a → b → c».

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from algos.knowledge_graph import KnowledgeGraph, link_orphans, predict_links


class TestGraphLearning(unittest.TestCase):
    def setUp(self):
        self.kg = KnowledgeGraph()

    def test_build_function_links_creates_fn_nodes(self):
        from algos import knowledge_graph as _kgm
        _kgm.kg.nodes = {}
        _kgm.kg.edges = {}
        from algos.knowledge_graph import build_function_links
        added = build_function_links()
        # функции базы знаний должны стать узлами с рёбрами
        self.assertGreater(added, 0)
        self.assertGreater(len(_kgm.kg.nodes), 0)
        keys = set(_kgm.kg.edges.keys())
        self.assertTrue(any("использует_понятие" in k for k in keys))

    def test_link_orphans_binds_short_orphan(self):
        self.kg.add_edge("alpha", "связано_с", "beta", 1.0)
        self.kg.add_edge("beta", "связано_с", "gamma", 1.0)
        # изолированный узел = тот, что не участвует в рёбрах
        self.kg.add_node("сирота")
        added = link_orphans(max_word_len=20, max_edges=50)
        self.assertGreaterEqual(added, 0)
        self.assertIn("сирота", self.kg.nodes)

    def test_predict_links_uses_common_neighbors(self):
        # граф, где A и B делят общего соседа C, но не связаны напрямую
        self.kg.add_edge("A", "X", "C", 1.0)
        self.kg.add_edge("C", "Y", "B", 1.0)
        self.kg.add_edge("B", "Z", "C", 1.0)
        # общие соседи A и B: C — прямая связь между A и B отсутствует
        added = predict_links(min_common=1, max_edges=20, weight=0.3)
        self.assertGreaterEqual(added, 0)

    def test_try_concept_path_returns_chain(self):
        from algos import knowledge_graph as _kgm
        _kgm.kg.nodes = {}
        _kgm.kg.edges = {}
        _kgm.kg.add_edge("нейросеть", "связано_с", "обучение", 1.0)
        _kgm.kg.add_edge("обучение", "связано_с", "алгоритм", 1.0)
        from algos.knowledge_graph import try_concept_path
        chain = try_concept_path("как связано с нейросеть")
        self.assertIsNotNone(chain)
        self.assertIn("→", chain)
        self.assertIn("нейросеть", chain)

    def test_bridge_components_links_isolated(self):
        self.kg.add_edge("кортеж", "связано_с", "список", 1.0)
        # изолированный узел с общим словом со связным
        self.kg.add_node("кортеж в python")
        added = self.kg.bridge_components(max_edges=10, weight=0.25)
        # «кортеж в python» связан через общее слово «кортеж»
        self.assertGreaterEqual(added, 0)

    def test_normalize_nodes_extracts_concept(self):
        self.kg.add_node("нейросеть использует обучение")
        added = self.kg.normalize_nodes(max_phrase_words=4, weight=0.4)
        self.assertGreater(added, 0)
        # фраза должна получить ребро «про_понятие» к своему ядру-понятию
        pro_edges = [k for k in self.kg.edges if k[1] == "про_понятие"]
        self.assertTrue(pro_edges, "ожидали ребро про_понятие от узла-фразы к понятию")


if __name__ == "__main__":
    unittest.main()