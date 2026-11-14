# -*- coding: utf-8 -*-
"""Ночной аудит 2026-11-14: тесты на уязвимые места, найденные при обходе.

Проверяем то, что раньше не покрывалось и реально ломалось:
  - tools/check_duplicates.py не видит переопределение функции в ОДНОМ файле,
    а именно так в core/mirro_core.py появился затеняющий _search_best;
  - scripts/restore.py: выбор бэкапа по числовой, а не лексикографической метке;
  - scripts/restore.py: устойчивость к мусору/отсутствию файла;
  - algos/english_kb.py: ключи _TOPIC_TEST обязаны иметь ответ в _EN_KB.

Все тесты статические или на изолированных модулях: сеть не нужна,
сервер не поднимается, data/ и models/ только читаются.
"""
import ast
import os
import re
import sys
import tempfile
import unittest

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, ROOT)
sys.path.insert(0, os.path.join(ROOT, "tools"))

import check_duplicates  # noqa: E402


class TestDuplicateCheckerCatchesSameFileRedefinition(unittest.TestCase):
    """check_duplicates группирует по имени и по файлам (set) — повторное
    `def` в одном файле схлопывается в один путь и не попадает в отчёт.
    Именно так остался незамеченным второй _search_best в core/mirro_core.py."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="mirro_dup_")
        self._path = os.path.join(self._tmp, "one.py")
        with open(self._path, "w", encoding="utf-8") as handle:
            handle.write("def same():\n    pass\n\ndef same():\n    pass\n")

    def tearDown(self):
        for name in os.listdir(self._tmp):
            os.remove(os.path.join(self._tmp, name))
        os.rmdir(self._tmp)

    def test_row_count_is_one_for_single_file(self):
        index = check_duplicates._load_defs(self._tmp)
        self.assertEqual(index["same"], {self._path},
                         "путь в set схлопывается — повтор виден только по числу def")

    def test_redefinition_is_not_reported(self):
        index = check_duplicates._load_defs(self._tmp)
        names = [name for name, _files in check_duplicates._duplicates(index)]
        self.assertNotIn("same", names)

    def test_counter_records_both_definitions(self):
        index, redefinitions = self._load_with_counts(self._tmp)
        self.assertEqual(redefinitions.get("same"), 2)

    @staticmethod
    def _load_with_counts(root):
        """Повторная регистрация с подсчётом: скольких определений не хватает."""
        counter = {}
        for dirpath, _dirs, files in os.walk(root):
            for fname in files:
                if fname.endswith(".py"):
                    with open(os.path.join(dirpath, fname), encoding="utf-8") as handle:
                        for line in handle:
                            match = re.match(r"^\s*def\s+(\w+)\s*\(", line)
                            if match:
                                name = match.group(1)
                                counter[name] = counter.get(name, 0) + 1
        return check_duplicates._load_defs(root), counter


class TestMirroCoreHasNoShadowedDefinitions(unittest.TestCase):
    """Регрессия на конкретный дефект: _search_best определён дважды."""

    CORE = os.path.join(ROOT, "core", "mirro_core.py")

    def test_top_level_names_are_unique(self):
        source = open(self.CORE, encoding="utf-8").read()
        tree = ast.parse(source)
        seen = {}
        shadowed = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                if node.name in seen:
                    shadowed.append((node.name, seen[node.name], node.lineno))
                else:
                    seen[node.name] = node.lineno
        self.assertEqual(shadowed, [],
                         "повторное определение на верхнем уровне затеняет первое: %r" % (shadowed,))


class TestRestoreBackupSelection(unittest.TestCase):
    """try_find_latest_backup должен сравнивать метку как ЧИСЛО."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="mirro_bak_")

    def tearDown(self):
        for name in os.listdir(self._tmp):
            os.remove(os.path.join(self._tmp, name))
        os.rmdir(self._tmp)

    def _touch(self, name):
        path = os.path.join(self._tmp, name)
        with open(path, "w", encoding="utf-8") as handle:
            handle.write("x")
        return path

    def test_longer_timestamp_wins_over_lexicographic(self):
        from scripts.restore import try_find_latest_backup

        self._touch("backup_9.000.mirro.enc")
        latest = self._touch("backup_10.000.mirro.enc")
        self.assertEqual(try_find_latest_backup(backup_dir=self._tmp), latest,
                         "10 новее 9: сравнение строк дало бы обратный порядок")

    def test_leading_zeros_are_numeric(self):
        from scripts.restore import try_find_latest_backup

        self._touch("backup_007.000.mirro.enc")
        latest = self._touch("backup_10.000.mirro.enc")
        self.assertEqual(try_find_latest_backup(backup_dir=self._tmp), latest)

    def test_non_digit_suffix_is_ignored(self):
        from scripts.restore import try_find_latest_backup

        self._touch("backup_abc.000.mirro.enc")
        self.assertEqual(try_find_latest_backup(backup_dir=self._tmp), "",
                         "метка не число — файл не бэкап")

    def test_missing_directory_returns_empty(self):
        from scripts.restore import try_find_latest_backup

        missing = os.path.join(self._tmp, "nope")
        self.assertEqual(try_find_latest_backup(backup_dir=missing), "")


class TestRestoreRejectsBadInput(unittest.TestCase):
    """Восстановление не должно падать и не должно создавать файл из мусора."""

    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="mirro_rest_")
        self._out = os.path.join(self._tmp, "out.pkl")

    def tearDown(self):
        for name in os.listdir(self._tmp):
            os.remove(os.path.join(self._tmp, name))
        os.rmdir(self._tmp)

    def test_garbage_backup_reports_error(self):
        from scripts.restore import try_restore_graph_from_backup

        bad = os.path.join(self._tmp, "bad.enc")
        with open(bad, "wb") as handle:
            handle.write(b"not-a-cipher-stream")
        result = try_restore_graph_from_backup(bad, output_graph_path=self._out)
        self.assertEqual(result["status"], "error")

    def test_garbage_does_not_create_output(self):
        from scripts.restore import try_restore_graph_from_backup

        bad = os.path.join(self._tmp, "bad.enc")
        with open(bad, "wb") as handle:
            handle.write(b"not-a-cipher-stream")
        try_restore_graph_from_backup(bad, output_graph_path=self._out)
        self.assertFalse(os.path.exists(self._out),
                         "неудачное восстановление не должно перезаписывать граф")

    def test_missing_file_reports_error(self):
        from scripts.restore import try_restore_graph_from_backup

        result = try_restore_graph_from_backup(os.path.join(self._tmp, "absent.enc"),
                                               output_graph_path=self._out)
        self.assertEqual(result["status"], "error")


class TestEnglishKbTopicCoverage(unittest.TestCase):
    """Каждая тема _TOPIC_TEST должна отвечаться из _EN_KB (статически)."""

    KB_PATH = os.path.join(ROOT, "algos", "english_kb.py")

    def test_every_topic_key_exists_in_kb(self):
        source = open(self.KB_PATH, encoding="utf-8").read()
        tree = ast.parse(source)
        literal_keys = set()
        topics = []
        for node in tree.body:
            self._collect(node, literal_keys, topics)
        missing = [name for name in topics if name not in literal_keys]
        self.assertEqual(missing, [], "темы без ответа в _EN_KB: %r" % (missing,))

    @staticmethod
    def _collect(node, literal_keys, topics):
        """Копит литеральные ключи словаря и имена тем."""
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.Dict):
            for key in node.value.keys:
                if isinstance(key, ast.Constant) and isinstance(key.value, str):
                    literal_keys.add(key.value)
        if isinstance(node, ast.Assign) and isinstance(node.value, ast.List):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == "_TOPIC_TEST":
                    for item in node.value.elts:
                        if isinstance(item, ast.Tuple) and item.elts:
                            first = item.elts[0]
                            if isinstance(first, ast.Constant) and isinstance(first.value, str):
                                topics.append(first.value)


if __name__ == "__main__":
    unittest.main(verbosity=2)
