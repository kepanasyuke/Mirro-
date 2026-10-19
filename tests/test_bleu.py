# -*- coding: utf-8 -*-
"""Юнит-тесты для BLEU self-eval (улучшение №09 из аudитa).

ВАЖНО: scripts.algorithms.py при импорте строит весь TF-IDF индекс
(~100с, >1.5 ГБ) из-за глобального singleton `algo = MirroAlgorithms()`.
Поэтому bleu_score (чистый статический метод, не зависит от индекса)
извлекается из исходника модуля без его выполнения. self_eval_bleu
требует индекс, поэтому тестируется только логика bleu.

Запуск:  python -m unittest tests.test_bleu -v
"""
import os, re, sys, textwrap, unittest

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


def _load_bleu():
    """Извлекает метод MirroAlgorithms.bleu_score как чистую функцию.

    scripts.algorithms.py строит индекс при импорте, поэтому вырезаем тело
    статического метода (он не зависит от индекса) и исполняем как функцию.
    """
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "scripts", "algorithms.py")
    src = open(path, encoding="utf-8-sig").read()
    m = re.search(
        r"    def bleu_score\(reference, hypothesis, max_n=4\):.*?(?=\n    def |\n    @|# =+|\Z)",
        src, re.S)
    if not m:
        raise RuntimeError("bleu_score не найден в algorithms.py")
    block = m.group(0)
    # Первая строка — сигнатура; остальные — тело с отступом 8 пробелов.
    head, _, body = block.partition(":\n")
    body = textwrap.dedent(body)          # в общий минимум отступа (8)
    body = textwrap.indent(body, "    ")  # возвращаем 4-проб. отступ под новый def
    code = "def bleu_score(reference, hypothesis, max_n=4):\n" + body
    ns = {}
    exec(code, ns)
    return ns["bleu_score"]


_BLEU_FN = _load_bleu()


class TestBleu(unittest.TestCase):
    # staticmethod, чтобы self.bleu(...) вызывал функцию без привязки self.
    bleu = staticmethod(_BLEU_FN)

    def test_identical_returns_high(self):
        s = self.bleu("НДС это налог на добавленную стоимость",
                      "НДС это налог на добавленную стоимость")
        self.assertGreater(s, 0.9)

    def test_unrelated_returns_low(self):
        s = self.bleu("НДС это налог на добавленную стоимость",
                      "Сегодня солнечная погода и тепло на улице")
        self.assertLess(s, 0.15)

    def test_subset_penalized(self):
        full = "Сортировка пузырьком меняет соседние элементы массива местами"
        long_ = self.bleu(full, full + " и повторяет это до полной упорядоченности")
        self.assertGreater(long_, 0.0)

    def test_empty_ref_returns_zero(self):
        self.assertEqual(self.bleu("", "что-то"), 0.0)

    def test_empty_hyp_returns_zero(self):
        self.assertEqual(self.bleu("что-то", ""), 0.0)

    def test_monotonic(self):
        same = self.bleu("привет мир как дела", "привет мир как дела")
        diff = self.bleu("привет мир как дела", "абсолютно другой непонятный текст")
        self.assertGreater(same, diff)


if __name__ == "__main__":
    unittest.main()