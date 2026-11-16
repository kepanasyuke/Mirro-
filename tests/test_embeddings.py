import os
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import algos.embeddings as emb

CORPUS = [
    "кошка бежит по дороге быстро",
    "собака бежит по дороге рядом",
    "кошка любит молоко и дом",
    "собака любит мясо и дом",
    "алгоритм сортирует данные массива",
    "алгоритм решает задачу шагами",
]


class EmbeddingModelTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.model = emb.train_from_texts(CORPUS, window=2, max_vocab=50, min_count=1)

    def test_model_has_words(self):
        self.assertIn("кошка", self.model["vectors"])
        self.assertIn("алгоритм", self.model["vectors"])

    def test_neighbours_are_closer_than_strangers(self):
        pets = emb.similarity(self.model, "кошка", "собака")
        alien = emb.similarity(self.model, "кошка", "алгоритм")
        self.assertGreater(pets, alien)

    def test_empty_inputs_give_zero(self):
        self.assertEqual(emb.similarity(self.model, "", "кошка"), 0.0)
        self.assertEqual(emb.cosine({}, {"a": 1.0}), 0.0)

    def test_empty_corpus_gives_empty_model(self):
        model = emb.train_from_texts([], min_count=1)
        self.assertEqual(model["vectors"], {})

    def test_save_and_load_roundtrip(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "model.json"
            self.assertTrue(emb.save(self.model, path))
            loaded = emb.load(path)
            self.assertAlmostEqual(emb.similarity(loaded, "кошка", "собака"),
                                   emb.similarity(self.model, "кошка", "собака"), places=6)

    def test_missing_file_gives_empty_model(self):
        model = emb.load(Path(tempfile.gettempdir()) / "нет-такого-файла.json")
        self.assertEqual(model["vectors"], {})


class TokenizeTest(unittest.TestCase):
    def test_short_words_are_dropped(self):
        self.assertEqual(emb.tokenize("Я и кот"), ["кот"])

    def test_lowercase(self):
        self.assertEqual(emb.tokenize("КОШКА"), ["кошка"])


if __name__ == "__main__":
    unittest.main()
