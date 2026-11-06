# -*- coding: utf-8 -*-
"""Восстановление графа из зашифрованных бэкапов (улучшение №37).

Находит самый свежий файл `backup_<ts>.mirro.enc` в папке бэкапов, расшифровывает
десятичным поточным шифром (scripts/cipher.py) и перезаписывает
models/knowledge_graph.pkl — кэш мыслительного движка.

Совместим с try_create_encrypted_backup (core/mirro_core.py): бэкап хранит полный
dict {nodes, edges, experience}, как KnowledgeGraph.save().

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import os, pickle


def try_find_latest_backup(backup_dir="backups/"):
    """Находит файл бэкапа с самой поздней временной меткой в названии.
    Один return: str (путь) или '' если нет."""
    latest = ""
    max_ts = -1
    try:
        for name in os.listdir(backup_dir):
            if name.startswith("backup_") and name.endswith(".mirro.enc"):
                mid = name[len("backup_"):]
                ts = mid.split(".")[0]
                if ts.isdigit():
                    tsnum = int(ts)
                    if tsnum > max_ts:
                        max_ts = tsnum
                        latest = os.path.join(backup_dir, name)
    except OSError:
        latest = ""
    return latest


def try_restore_graph_from_backup(backup_filepath, output_graph_path="models/knowledge_graph.pkl"):
    """Расшифровывает бэкап и перезаписывает pickle-кэш графа знаний.
    Один return: dict {status, message}."""
    status = {"status": "error", "message": "Restore failed"}
    try:
        import sys, os as _os
        _scripts = os.path.dirname(os.path.abspath(__file__))
        if _scripts not in sys.path:
            sys.path.insert(0, _scripts)
        from scripts.cipher import try_load_secure_key, transform_bytes_to_cipher
        with open(backup_filepath, "rb") as f:
            encrypted_bytes = f.read()
        key = try_load_secure_key()
        decrypted = transform_bytes_to_cipher(encrypted_bytes, key, decrypt=True)
        graph = pickle.loads(decrypted)
        # принимаем либо полный dict {nodes, edges, experience}, либо граф-объект
        ok_nodes = isinstance(graph, dict) and ("nodes" in graph or "edges" in graph)
        ok_obj = hasattr(graph, "nodes") and hasattr(graph, "edges")
        if ok_nodes or ok_obj:
            with open(output_graph_path, "wb") as f:
                pickle.dump(graph, f, protocol=4)
            status = {"status": "success", "message": f"Graph restored from {backup_filepath}"}
        else:
            status = {"status": "error", "message": "Structure lacks nodes/edges"}
    except Exception as e:
        status = {"status": "error", "message": str(e)}
    return status


def main():
    import argparse
    ap = argparse.ArgumentParser(description="Восстановление графа из зашифрованного бэкапа")
    ap.add_argument("--backup-dir", default="backups/", help="папка бэкапов (по умолчанию backups/)")
    ap.add_argument("--out", default="models/knowledge_graph.pkl", help="куда записать (pickle)")
    ap.add_argument("--file", default="", help="конкретный файл бэкапа (иначе — самый свежий)")
    args = ap.parse_args()
    filepath = args.file or try_find_latest_backup(args.backup_dir)
    if not filepath:
        print("Нет бэкапов для восстановления.")
        return 1
    res = try_restore_graph_from_backup(filepath, args.out)
    print(res.get("status"), "—", res.get("message", ""))
    return 0 if res.get("status") == "success" else 1


if __name__ == "__main__":
    import sys
    sys.exit(main())