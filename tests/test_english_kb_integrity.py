# -*- coding: utf-8 -*-
"""Проверка целостности algos/english_kb.py: дубли, битая кодировка, пустоты.

Тест статический: модуль НЕ импортируется (1.5 МБ словаря дороже и шумнее),
исходник разбирается через ast, что быстро и не тянет зависимости проекта.

Запуск:
    python -m unittest tests.test_english_kb_integrity -v

Все проверки читают один и тот же разобранный файл (кеш в модульной переменной),
сеть не нужна, время работы — десятые доли секунды.
"""
import ast
import os
import re
import unittest

KB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
                       "algos", "english_kb.py")

CYRILLIC = re.compile("[\u0400-\u04FF]")
STUB = re.compile(r"\b(todo|tbd|fixme|lorem ipsum)\b", re.I)
GLUE = re.compile(r"[a-z][A-Z]")
COLLAPSE = re.compile(r"\s{2,}")

_CACHE = {}


def load_kb():
    """Один раз разбирает файл: (дерево, текст исходника)."""
    if "tree" not in _CACHE:
        with open(KB_PATH, encoding="utf-8") as handle:
            source = handle.read()
        _CACHE["source"] = source
        _CACHE["tree"] = ast.parse(source)
    return _CACHE["tree"], _CACHE["source"]


def named_dict(name):
    """Верхнеуровневый словарь по имени переменной."""
    tree, _ = load_kb()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.value, ast.Dict):
            for target in stmt.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    return stmt.value
    return None


def kb_items():
    """Пары (ключ, узел значения, строка ключа) из _EN_KB без дублей по объекту."""
    dictionary = named_dict("_EN_KB")
    if dictionary is None:
        return []
    pairs = []
    for key_node, value_node in zip(dictionary.keys, dictionary.values):
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            pairs.append((key_node.value, value_node, key_node.lineno))
    return pairs


def text_of(node):
    """Текст значения: только строковые литералы, в порядке исходника."""
    parts = []
    for sub in ast.walk(node):
        if isinstance(sub, ast.Constant) and isinstance(sub.value, str):
            parts.append(sub.value)
    return "".join(parts)


def top_key_lines():
    """Все литеральные ключи _EN_KB и их строки, включая повторные."""
    dictionary = named_dict("_EN_KB")
    if dictionary is None:
        return {}
    lines = {}
    for key_node in dictionary.keys:
        if isinstance(key_node, ast.Constant) and isinstance(key_node.value, str):
            lines.setdefault(key_node.value, []).append(key_node.lineno)
    return lines


def topic_names():
    """Имена тем из _TOPIC_TEST."""
    tree, _ = load_kb()
    for stmt in tree.body:
        if isinstance(stmt, ast.Assign) and isinstance(stmt.targets[0], ast.Name):
            if stmt.targets[0].id == "_TOPIC_TEST":
                try:
                    return [name for name, _ in ast.literal_eval(stmt.value)]
                except (ValueError, SyntaxError):
                    return []
    return []


class TestEnglishKbIntegrity(unittest.TestCase):
    """Инварианты словаря английского режима."""

    def test_kb_exists_and_is_large(self):
        pairs = kb_items()
        self.assertGreater(len(pairs), 1000, "_EN_KB подозрительно мал")

    def test_no_duplicate_literal_keys(self):
        """Повторный литеральный ключ молча перезаписывает предыдущий ответ."""
        duplicated = {key: lines for key, lines in top_key_lines().items() if len(lines) > 1}
        report = "\n".join(f"  {key!r}: строки {lines}" for key, lines in sorted(duplicated.items()))
        self.assertEqual(duplicated, {},
                         f"{len(duplicated)} продублированных ключей в _EN_KB:\n{report}")

    def test_no_empty_values(self):
        empty = [(key, line) for key, node, line in kb_items() if not text_of(node).strip()]
        self.assertEqual(empty, [], f"пустые ответы: {empty}")

    def test_no_stub_values(self):
        stubs = [(key, line) for key, node, line in kb_items() if STUB.search(text_of(node))]
        self.assertEqual(stubs, [], f"заглушки вместо ответов: {stubs}")

    def test_values_are_english_only(self):
        """Кириллица в английском ответе — признак mojibake или копипасты."""
        broken = [(key, line, CYRILLIC.findall(text_of(node))[:5])
                  for key, node, line in kb_items() if CYRILLIC.search(text_of(node))]
        self.assertEqual(broken, [], f"кириллица в ответах: {broken[:10]}")

    def test_no_glued_words(self):
        glued = [(key, line) for key, node, line in kb_items() if GLUE.search(text_of(node))]
        self.assertEqual(glued, [], f"склейки без пробела: {glued[:10]}")

    def test_no_collapsed_whitespace(self):
        collapsed = [(key, line) for key, node, line in kb_items() if COLLAPSE.search(text_of(node))]
        self.assertEqual(collapsed, [], f"двойные пробелы: {collapsed[:10]}")

    def test_values_end_with_punctuation(self):
        bad = [(key, line) for key, node, line in kb_items()
               if not text_of(node).strip().endswith((".", "!", "?", '"', ")"))]
        self.assertEqual(bad, [], f"оборванные значения: {bad[:10]}")

    def test_every_topic_has_answer(self):
        """Тема из _TOPIC_TEST без значения в _EN_KB даёт ответ None."""
        keys = set(top_key_lines())
        missing = [name for name in topic_names() if name not in keys]
        self.assertEqual(missing, [], f"темы без значения в _EN_KB: {missing}")

    def test_no_uppercase_or_padded_keys(self):
        bad = [key for key in top_key_lines() if key != key.strip() or key != key.lower()]
        self.assertEqual(bad, [], f"ключи с пробелами по краям или заглавными: {bad[:10]}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
