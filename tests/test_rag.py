# -*- coding: utf-8 -*-
"""Юнит-тесты для двухуровневого RAG-поиска (scripts/rag.py).

Работают на временных синтетических сегментах: боевой корпус (data/corpus_big,
models/rag_index) не нужен и не трогается. Пути CORPUS_DIR/INDEX_DIR
подменяются на временный каталог, поэтому pickle-файлы не попадают в дерево.
"""
import json
import os
import pickle
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "scripts"))

import rag as rag_mod


ROWS = [
    {"instruction": "Сколько будет 245 плюс 178", "output": "423"},
    {"instruction": "Что такое НДС простыми словами", "output": "Налог на добавленную стоимость."},
    {"instruction": "Реши уравнение три икс плюс пять", "output": "Икс равен семи."},
]


class _RagCase(unittest.TestCase):
    """Общая подготовка: временный корпус из двух сегментов."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp()
        self._old_corpus = rag_mod.CORPUS_DIR
        self._old_index = rag_mod.INDEX_DIR
        root = Path(self._tmp)
        rag_mod.CORPUS_DIR = root / "corpus_big"
        rag_mod.CORPUS_DIR.mkdir()
        rag_mod.INDEX_DIR = root / "rag_index"
        self._write_segment("corpus-000.jsonl", ROWS)
        self._write_segment("corpus-001.jsonl", [
            {"instruction": "Что такое фотосинтез", "output": "Процесс в растениях."},
        ])

    def tearDown(self):
        rag_mod.CORPUS_DIR = self._old_corpus
        rag_mod.INDEX_DIR = self._old_index
        for f in Path(self._tmp).rglob("*"):
            if f.is_file():
                os.chmod(f, 0o666)
        import shutil
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write_segment(self, name, rows):
        path = rag_mod.CORPUS_DIR / name
        with open(path, "w", encoding="utf-8") as fh:
            for row in rows:
                fh.write(json.dumps(row, ensure_ascii=False) + "\n")
        return path

    def _rag(self):
        return rag_mod.MirroRAG()


class TestSegmentIndex(_RagCase):
    def test_empty_segment_does_not_crash(self):
        # сегмент из одних пустых строк ранее падал UnboundLocalError (doc_id)
        self._write_segment("corpus-001.jsonl", [])
        index = self._rag()
        index.build_segment_index(1)
        with open(rag_mod.INDEX_DIR / "seg_000001.pkl", "rb") as fh:
            data = pickle.load(fh)
        self.assertEqual(data["n_docs"], 0)
        self.assertEqual(data["words"], {})

    def test_blank_lines_do_not_shift_doc_ids(self):
        path = rag_mod.CORPUS_DIR / "corpus-001.jsonl"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("\n")
            fh.write(json.dumps(ROWS[0], ensure_ascii=False) + "\n")
            fh.write("   \n")
        index = self._rag()
        index.build_segment_index(1)
        with open(rag_mod.INDEX_DIR / "seg_000001.pkl", "rb") as fh:
            data = pickle.load(fh)
        # пустая строка — тоже позиция в файле, поэтому документ на строке 1
        self.assertEqual(data["n_docs"], 3)
        self.assertEqual(list(data["words"]["сколько"].keys()), [1])
        self.assertEqual(index._read_doc(1, 1), ("Сколько будет 245 плюс 178", "423"))

    def test_broken_json_line_is_skipped_not_fatal(self):
        path = rag_mod.CORPUS_DIR / "corpus-001.jsonl"
        with open(path, "w", encoding="utf-8") as fh:
            fh.write("{битый json\n")
            fh.write(json.dumps(ROWS[1], ensure_ascii=False) + "\n")
        index = self._rag()
        index.build_segment_index(1)
        with open(rag_mod.INDEX_DIR / "seg_000001.pkl", "rb") as fh:
            data = pickle.load(fh)
        self.assertEqual(data["n_docs"], 2)
        self.assertNotIn("битый", data["words"])

    def test_corrupt_pickle_is_rebuilt(self):
        index = self._rag()
        index.build_segment_index(0)
        pfile = rag_mod.INDEX_DIR / "seg_000000.pkl"
        with open(pfile, "wb") as fh:      # обрезанный pickle
            fh.write(b"\x80\x04garbage")
        data = index._load_segment(0)
        self.assertEqual(data["n_docs"], 3)
        self.assertTrue(data["words"])

    def test_legacy_pickle_without_version_is_rebuilt(self):
        index = self._rag()
        index.build_segment_index(0)
        pfile = rag_mod.INDEX_DIR / "seg_000000.pkl"
        with open(pfile, "wb") as fh:
            pickle.dump({"words": {"фантом": {0: 1}}, "n_docs": 1}, fh)
        data = index._load_segment(0)
        self.assertNotIn("фантом", data["words"])

    def test_global_index_survives_segment_list_change(self):
        index = self._rag()
        index.build_tier1()
        self.assertIn("фотосинтез", index.global_index)
        self._write_segment("corpus-002.jsonl", [
            {"instruction": "Что такое инфляция", "output": "Рост цен."},
        ])
        # монотонный поиск: корпус вырос, индекс перечитан, старые слова на месте
        self.assertEqual(len(index.segments), 3)
        self.assertIn("фотосинтез", index.global_index)


class TestLocalIdf(unittest.TestCase):
    def test_idf_never_negative(self):
        # df == ndocs раньше давал отрицательный вес и штрафовал частые слова
        local = {"слово": {1: 1, 2: 1, 3: 1}}
        self.assertGreater(rag_mod.MirroRAG._local_idf(local, 3, "слово"), 0.0)

    def test_idf_never_negative_when_counts_desync(self):
        # счётчик документов отстал от индекса: вес упирается в 0, а не уходит в минус
        local = {"слово": {i: 1 for i in range(10)}}
        self.assertGreaterEqual(rag_mod.MirroRAG._local_idf(local, 2, "слово"), 0.0)

    def test_rare_word_weighs_more_than_common(self):
        local = {"частый": {i: 1 for i in range(10)}, "редкий": {0: 1}}
        rare = rag_mod.MirroRAG._local_idf(local, 10, "редкий")
        common = rag_mod.MirroRAG._local_idf(local, 10, "частый")
        self.assertGreater(rare, common)


class TestSearch(_RagCase):
    def test_search_finds_answer_from_corpus(self):
        index = self._rag()
        index.build_tier1()
        hits = index.search("сколько будет 245 плюс 178", top_k=1)
        self.assertEqual(len(hits), 1)
        self.assertEqual(hits[0][2], "423")

    def test_empty_query_returns_nothing(self):
        index = self._rag()
        index.build_tier1()
        self.assertEqual(index.search("", top_k=3), [])

    def test_unknown_query_returns_nothing(self):
        index = self._rag()
        index.build_tier1()
        self.assertEqual(index.search("абракадабра зюзька", top_k=3), [])

    def test_guided_search_uses_stable_hint(self):
        index = self._rag()
        index.build_tier1()
        first = index.run_quantum_guided_rag("фотосинтез", ("биология", "растения"), top_k=1)
        second = index.run_quantum_guided_rag("фотосинтез", ("биология", "растения"), top_k=1)
        self.assertEqual(first, second)
        self.assertTrue(first)


class TestIndexDirLazy(unittest.TestCase):
    def test_import_does_not_create_index_dir(self):
        # модуль больше не создаёт models/rag_index при импорте: каталог
        # появляется только при сборке индекса (_ensure_index_dir)
        src = Path(rag_mod.__file__).read_text("utf-8")
        init_block = src.split("class MirroRAG", 1)[0]
        self.assertNotIn("INDEX_DIR.mkdir(parents=True, exist_ok=True)\n\nSEG", init_block)
        self.assertNotIn("INDEX_DIR.mkdir(parents=True, exist_ok=True)\n\nGLOBAL", init_block)


if __name__ == "__main__":
    unittest.main()
