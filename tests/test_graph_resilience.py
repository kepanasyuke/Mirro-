# -*- coding: utf-8 -*-
"""Тесты живучести KnowledgeGraph на битых данных (pickle, пустой граф).

Дефекты, закреплённые здесь:
  - load() писал загруженное в self ДО валидации: бэкап {"nodes": None} или
    edges=None уезжал в граф, и КАЖДЫЙ следующий вызов (summary, try_*)
    падал трейсбеком вместо строки-заглушки;
  - {"nodes": ["a","b"]} превращал self.nodes в список — граф «работал» с
    нарушенным инвариантом dict и падал уже в менее очевидном месте;
  - после неудачной загрузки старые данные оставались в графе (утечка
    состояния между запросами).

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, pickle, sys, tempfile, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "algos"))

from algos.knowledge_graph import KnowledgeGraph
from algos.zero_dimensional import growth_report, dimension_of_understanding


class BrokenGraphFiles(unittest.TestCase):
    def setUp(self):
        self.tmpdir = tempfile.mkdtemp(prefix="mirro_kg_")

    def _write(self, name, payload):
        path = os.path.join(self.tmpdir, name)
        with open(path, "wb") as f:
            if isinstance(payload, bytes):
                f.write(payload)
            else:
                pickle.dump(payload, f, protocol=4)
        return path

    def test_missing_file_gives_empty_graph(self):
        graph = KnowledgeGraph()
        self.assertEqual(graph.load(os.path.join(self.tmpdir, "нет.pkl")), 0)
        self.assertEqual(graph.summary().count("0 узлов"), 1)

    def test_truncated_pickle_does_not_raise(self):
        path = self._write("cut.pkl", b"\x80\x04\x95\x20\x00\x00\x00\x00\x00\x00\x00}")
        graph = KnowledgeGraph()
        self.assertEqual(graph.load(path), 0)
        self.assertIsInstance(graph.summary(), str)

    def test_none_fields_do_not_break_summary(self):
        path = self._write("none.pkl", {"nodes": None, "edges": None})
        graph = KnowledgeGraph()
        self.assertEqual(graph.load(path), 0)
        self.assertIn("пуст", graph.summary())

    def test_list_nodes_not_accepted(self):
        path = self._write("list.pkl", {"nodes": ["a", "b"], "edges": {}})
        graph = KnowledgeGraph()
        graph.load(path)
        self.assertIsInstance(graph.nodes, dict, "инвариант nodes=dict обязан сохраняться")
        self.assertEqual(len(graph.nodes), 0)

    def test_bad_edge_keys_dropped(self):
        path = self._write("keys.pkl", {"nodes": {}, "edges": {"abc": 1.0, (1, 2): 2.0}})
        graph = KnowledgeGraph()
        self.assertEqual(graph.load(path), 0)

    def test_failed_load_clears_previous_state(self):
        graph = KnowledgeGraph()
        graph.from_triples([("вода", "кипит при", "100")])
        path = self._write("broken.pkl", {"nodes": {}, "edges": None})
        self.assertEqual(graph.load(path), 0)
        self.assertEqual(len(graph.nodes), 0, "старые данные не должны пережить битую загрузку")
        self.assertEqual(len(graph.edges), 0)

    def test_growth_report_on_empty_graph(self):
        graph = KnowledgeGraph()
        self.assertEqual(dimension_of_understanding(graph), 0.0)
        self.assertIn("0D=0", growth_report(graph))

    def test_growth_report_on_loaded_broken_backup(self):
        path = self._write("broken2.pkl", b"garbage-bytes")
        graph = KnowledgeGraph()
        graph.load(path)
        self.assertIsInstance(growth_report(graph), str)


class ValidRoundTrip(unittest.TestCase):
    def test_save_load_preserves_graph(self):
        tmpdir = tempfile.mkdtemp(prefix="mirro_kg_ok_")
        path = os.path.join(tmpdir, "g.pkl")
        source = KnowledgeGraph()
        source.from_triples([("Вода", "кипит при", "100"), ("Луна", "вращается вокруг", "Земля")])
        self.assertTrue(source.save(path))
        restored = KnowledgeGraph()
        self.assertEqual(restored.load(path), 2)
        self.assertEqual(len(restored.nodes), len(source.nodes))
        self.assertEqual(restored.neighbors("вода"), source.neighbors("вода"))

    def test_norm_handles_non_string(self):
        graph = KnowledgeGraph()
        self.assertEqual(graph.degree_of(42), 0)
        self.assertEqual(graph.neighbors(None), [])
        self.assertIsNone(graph.get_node(3.5))


if __name__ == "__main__":
    unittest.main()
