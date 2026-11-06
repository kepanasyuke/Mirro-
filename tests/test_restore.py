# -*- coding: utf-8 -*-
"""Юнит-тесты восстановления графа из зашифрованных бэкапов.

Проверяем на реальных функциях (совместимый формат полного графа):
  - try_find_latest_backup находит самый свежий бэкап по временной метке;
  - полный цикл: backup (core) -> latest -> restore (scripts/restore.py)
    -> десериализация без потерь (nodes/edges/experience).

Чистый Python, без внешних библиотек, атомарно (по LINTER.md).
"""
import os, sys, pickle, unittest, tempfile, shutil
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.restore import try_find_latest_backup, try_restore_graph_from_backup
from core.mirro_core import try_create_encrypted_backup


class TestMirroRestore(unittest.TestCase):
    def setUp(self):
        self._tmp = tempfile.mkdtemp(prefix="mirro_bak_")
        self.backup_dir = os.path.join(self._tmp, "backups")
        os.makedirs(self.backup_dir, exist_ok=True)
        self.out_path = os.path.join(self._tmp, "knowledge_graph.pkl")
        self.graph = {"nodes": {"n_test": {"w": 1.0}}, "edges": {}, "experience": [0.5, 0.7]}

    def tearDown(self):
        shutil.rmtree(self._tmp, ignore_errors=True)

    def _write_mock_backup_with_ts(self, ts):
        """Создаёт файл backup_<ts>.<номер>.mirro.enc с содержимым ts (для проверки поиска)."""
        path = os.path.join(self.backup_dir, f"backup_{ts}.000.mirro.enc")
        with open(path, "w", encoding="utf-8") as f:
            f.write(str(ts))
        return path

    def test_find_latest_by_timestamp(self):
        self._write_mock_backup_with_ts(1000)
        late = self._write_mock_backup_with_ts(9999)
        latest = try_find_latest_backup(backup_dir=self.backup_dir)
        self.assertEqual(latest, late, "должен выбираться бэкап с наибольшей меткой")

    def test_full_backup_restore_cycle(self):
        res_backup = try_create_encrypted_backup(self.graph, backup_dir=self.backup_dir)
        self.assertEqual(res_backup["status"], "success")
        latest = try_find_latest_backup(backup_dir=self.backup_dir)
        self.assertEqual(latest, res_backup["path"])
        res_restore = try_restore_graph_from_backup(latest, output_graph_path=self.out_path)
        self.assertEqual(res_restore["status"], "success")
        with open(self.out_path, "rb") as f:
            restored = pickle.load(f)
        self.assertIn("nodes", restored)
        self.assertIn("edges", restored)
        self.assertEqual(restored["nodes"], self.graph["nodes"])
        self.assertEqual(restored["experience"], self.graph["experience"])


if __name__ == "__main__":
    unittest.main()