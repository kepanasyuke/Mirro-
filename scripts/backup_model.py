# -*- coding: utf-8 -*-
"""Бэкап модели Mirro (улучшение №37).

Сохраняет состояние модели и сопутствующие данные в папку backups/ с
меткой времени. Обратимо: --restore восстанавливает последний/указанный бэкап.

Запуск:
   python scripts/backup_model.py            # создать бэкап
   python scripts/backup_model.py --restore  # восстановить последний бэкап
   python scripts/backup_model.py --list     # список бэкапов
"""
import argparse, json, shutil, sys
from datetime import datetime
from pathlib import Path

ROOT = Path(r"D:\Mirro")
MODELS = ROOT / "models"
STATE = ROOT / "core" / "stats.json"
LOGS = ROOT / "logs"
BACKUP_DIR = ROOT / "backups"

# Что бэкапим (относительные пути от ROOT)
SOURCES = [
    "models/model_state.json",
    "core/stats.json",
    "scripts/improvements.json",
]

# Большой индекс копируем опционально (--full), т.к. это ~1.6 ГБ
INDEX_SRC = "models/index_cache.pkl"


def _ts():
    return datetime.now().strftime("%Y%m%d_%H%M%S")


def create(full=False):
    BACKUP_DIR.mkdir(parents=True, exist_ok=True)
    tag = _ts()
    dirname = BACKUP_DIR / f"model_{tag}"
    dirname.mkdir(parents=True, exist_ok=True)
    copied = 0
    for rel in SOURCES:
        src = ROOT / rel
        if src.exists():
            dst = dirname / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(src, dst)
            copied += 1
    # Веса перцептрона/буст (лёгкие JSON из LIGHТ-FILES)
    for rel in ["models/index_cache.boost.json", "models/index_cache.perceptron.json"]:
        src = ROOT / rel
        if src.exists():
            shutil.copy2(src, dirname / rel)
            copied += 1
    if full:
        src = ROOT / INDEX_SRC
        if src.exists():
            shutil.copy2(src, dirname / INDEX_SRC)
            copied += 1
    meta = {"created": tag, "files": copied, "full": full}
    (dirname / "meta.json").write_text(json.dumps(meta, ensure_ascii=False, indent=2), "utf-8")
    print(f"Бэкап создан: {dirname} ({copied} файлов{' + индекс' if full else ''})")
    return dirname


def list_backups(include_full=False):
    if not BACKUP_DIR.exists():
        print("Бэкапов нет.")
        return []
    items = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir() and d.name.startswith("model_")])
    for d in reversed(items):
        tag = d.name.replace("model_", "")
        meta = {}
        mf = d / "meta.json"
        if mf.exists():
            try:
                meta = json.loads(mf.read_text("utf-8"))
            except Exception:
                pass
        has_idx = (d / INDEX_SRC).exists()
        files = meta.get("files", "?")
        print(f"{tag}  ({files} файлов" + (", +индекс" if has_idx else "") + ")")
    return items


def restore(target=None):
    if not BACKUP_DIR.exists():
        print("Бэкапов нет — восстанавливать нечего.")
        return False
    items = sorted([d for d in BACKUP_DIR.iterdir() if d.is_dir() and d.name.startswith("model_")])
    if not items:
        print("Бэкапов нет.")
        return False
    src = None
    if target:
        src = next((d for d in items if d.name == f"model_{target}"), None)
        if not src:
            print(f"Бэкап '{target}' не найден. Доступные: {', '.join(d.name for d in items)}")
            return False
    else:
        src = items[-1]  # последний
    restored = 0
    for d in src.rglob("*"):
        if d.is_file() and d.name != "meta.json":
            rel = d.relative_to(src)
            dst = ROOT / rel
            dst.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(d, dst)
            restored += 1
    print(f"Восстановлено из {src.name}: {restored} файлов")
    print("Внимание: перезапустите Mirro, чтобы изменения вступили в силу.")
    return True


def main():
    ap = argparse.ArgumentParser(description="Бэкап/восстановление модели Mirro")
    grp = ap.add_mutually_exclusive_group()
    grp.add_argument("--restore", nargs="?", const="", help="восстановить (последний или по метке)")
    grp.add_argument("--list", action="store_true", help="список бэкапов")
    grp.add_argument("--full", action="store_true", help="включить индекс (~1.6 ГБ)")
    args = ap.parse_args()

    sys.stdout.reconfigure(encoding="utf-8")
    tag = (args.restore or "").strip() if args.restore is not None else ""
    if args.restore is not None:
        restore(tag or None)
    elif args.list:
        list_backups()
    else:
        create(full=args.full)


if __name__ == "__main__":
    main()