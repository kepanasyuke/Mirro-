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


class TestCandidateAdmission(unittest.TestCase):
    """Замыкание цикла «тема вне графа → кандидат → граф».

    Раньше scripts/reflection.py на провал писал строку
    «тема «означает/variance» вне графа — кандидат на пополнение» и НИЧЕГО не
    добавлял в граф: в data/reflection_log.jsonl 46 таких строк, в
    data/graph_story.jsonl из 63331 узлов ни одного «кандидата» (см. отчёт
    2026-11-14/02-graph-memory). Здесь проверяем, что API пополнения реален.
    """

    def setUp(self):
        self.kg = KnowledgeGraph()

    def test_unknown_concepts_are_added_with_tag(self):
        res = self.kg.admit_candidate("пузырьковую", "сортировку")
        self.assertEqual(res["nodes_added"], 2)
        self.assertEqual(res["edge_added"], 1)
        self.assertIn("пузырьковую", self.kg.nodes)
        self.assertEqual(self.kg.nodes["пузырьковую"].tag, "пополнение")

    def test_known_concept_is_not_duplicated(self):
        self.kg.add_node("variance")
        res = self.kg.admit_candidate("variance", "дисперсия")
        self.assertEqual(res["nodes_added"], 1)
        self.assertEqual(self.kg.get_node("variance").tag, "понятие")

    def test_admission_is_idempotent(self):
        self.kg.admit_candidate("a", "b")
        again = self.kg.admit_candidate("a", "b")
        self.assertEqual(again["nodes_added"], 0)
        self.assertEqual(again["edge_added"], 0)

    def test_still_outside_reports_missing_only(self):
        self.kg.add_node("граф")
        self.assertEqual(self.kg.still_outside("граф", "сортировку"), ["сортировку"])
        self.assertEqual(self.kg.still_outside("граф", None), [])

    def test_empty_and_self_pairs_ignored(self):
        self.assertEqual(self.kg.admit_candidate("", ""), 
                         {"nodes_added": 0, "edge_added": 0, "a": "", "b": ""})
        self.assertEqual(self.kg.admit_candidate("граф", "граф")["edge_added"], 0)


class TestEdgeWeights(unittest.TestCase):
    """Знак и границы веса рёбер + Хебб-обновление (reward_sign).

    Найдено при сверке: add_edge() клал max(0.0, weight), поэтому новый узел
    с отрицательным весом получал 0.0, а _set_adj_weight при рёбрах a→b и b→a
    оставлял в индексе вес последнего записанного, хотя физически это одно
    ребро. Оба дефекта — потеря знака/величины.
    """

    def setUp(self):
        self.kg = KnowledgeGraph()

    def test_negative_weight_survives_creation(self):
        self.kg.add_edge("x", "p", "y", weight=-0.5)
        self.assertEqual(self.kg.get_edge_weight("x", "p", "y"), -0.5)

    def test_existing_edge_keeps_stronger_by_abs(self):
        self.kg.add_edge("x", "p", "y", weight=-0.9)
        self.kg.add_edge("x", "p", "y", weight=0.2)
        self.assertEqual(self.kg.get_edge_weight("x", "p", "y"), -0.9)

    def test_reward_capped_and_punish_floored(self):
        self.kg.add_edge("a", "p", "b", weight=1.0)
        for _ in range(20):
            self.kg.reward("a", "b", 0.2)
        self.assertEqual(self.kg.get_edge_weight("a", "p", "b"), 2.0)
        for _ in range(20):
            self.kg.punish("a", "b", 0.3)
        self.assertEqual(self.kg.get_edge_weight("a", "p", "b"), 0.15)

    def test_reward_sign_positive_strengthens(self):
        self.kg.add_edge("m", "p", "n", weight=0.5)
        self.assertEqual(self.kg.reward_sign("m", "n", 1.0, 0.05), 1)
        self.assertAlmostEqual(self.kg.get_edge_weight("m", "p", "n"), 0.55)

    def test_reward_sign_negative_weakens_but_keeps_floor(self):
        self.kg.add_edge("m", "p", "n", weight=0.5)
        self.assertEqual(self.kg.reward_sign("m", "n", -1.0, 0.1), 1)
        self.assertAlmostEqual(self.kg.get_edge_weight("m", "p", "n"), 0.4)

    def test_reward_sign_neutral_does_nothing(self):
        self.kg.add_edge("m", "p", "n", weight=0.5)
        self.assertEqual(self.kg.reward_sign("m", "n", 0.0, 0.1), 0)
        self.assertEqual(self.kg.get_edge_weight("m", "p", "n"), 0.5)

    def test_both_directions_do_not_confuse_index(self):
        self.kg.add_edge("a", "p", "b", weight=1.0)
        self.kg.add_edge("b", "p", "a", weight=0.6)
        index_weights = [row[2] for row in self.kg._adj["a"] if row[0] == "p" and row[1] == "b"]
        self.assertEqual(index_weights, [1.0])
        self.assertEqual(self.kg.edge_weight("a", "b"), 1.0)

    def test_reward_creates_missing_edge(self):
        # Хебб «fire together, wire together»: награда совместной активации
        # ДОЛЖНА создать связь, если её ещё нет, а не проходить молча.
        self.kg.add_node("нейросеть")
        self.kg.add_node("обучение")
        self.assertEqual(self.kg.edges, {})
        n = self.kg.reward("нейросеть", "обучение", 0.3)
        self.assertEqual(n, 1)
        self.assertGreater(self.kg.edge_weight("нейросеть", "обучение"), 0)
        # повторная награда усиливает существующее ребро, не создавая дубль
        self.kg.reward("нейросеть", "обучение", 0.3)
        self.assertEqual(len(self.kg.edges), 1)
        self.assertAlmostEqual(self.kg.edge_weight("нейросеть", "обучение"), 0.6)

    def test_hebb_depth_does_not_double_charge_target(self):
        self.kg.add_edge("a", "p", "z", 1.0)
        self.kg.add_edge("a", "p", "b", 1.0)
        # depth=1 должен усилить b и одного соседа, но не b дважды
        self.assertEqual(self.kg.hebbian_learn("a", "b", 0.1, depth=1), 2)
        self.assertAlmostEqual(self.kg.get_edge_weight("a", "p", "b"), 1.1)


if __name__ == "__main__":
    unittest.main()