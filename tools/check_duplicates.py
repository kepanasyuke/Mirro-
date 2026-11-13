# -*- coding: utf-8 -*-
"""check_duplicates.py — поиск повторяющихся функций по проекту.

Исключает заведомо ложные срабатывания:
  - дубликаты локальных помощников (rec, __init__ — случайные);
  - методы классов (__init__/__repr__ логично дублируются).
Печатает группы функций (name) определённых более чем в одном файле,
чтобы человек решил, выносить общее или нет.

Значения `main`, `setUp`/`setUpClass` (каркас тестов) — шум, не дубли.

Запуск:  python tools/check_duplicates.py [каталог] [--min-lines N]
         --min-lines N  показывать только функции длиннее N строк тела
                        (по умолчанию 0 — все).
"""
import os, re, sys
from collections import defaultdict

_DEF = re.compile(r"^(\s*)def\s+(\w+)\s*\(")
_DUP_IGNORE = {
    "__init__", "__repr__", "__str__", "rec",  # заведомо локальные
    "main", "setUp", "setUpClass", "tearDown", "tearDownClass",  # каркас запуска/тестов
}

def _load_defs(root, min_lines=0):
    """Собирает {имя_функции: [файлы]} длиной тела не меньше min_lines. Один return: dict."""
    index = defaultdict(set)
    for dirpath, _dirs, files in os.walk(root):
        skip_dir = "__pycache__" in dirpath or ".git" in dirpath
        if not skip_dir:
            for fname in files:
                if fname.endswith(".py"):
                    _scan_file(os.path.join(dirpath, fname), index, min_lines)
    return index


def _scan_file(path, index, min_lines):
    """Добавляет в index имена функций одного файла. Один return: None."""
    try:
        with open(path, "r", encoding="utf-8", errors="ignore") as fh:
            lines = fh.read().splitlines()
    except OSError:
        lines = []
    for i, line in enumerate(lines):
        m = _DEF.match(line)
        if m and not _is_ignored(m.group(2)):
            size = _body_size(lines, i, len(m.group(1)))
            if size >= min_lines:
                index[m.group(2)].add(path)
    return None


def _is_ignored(name):
    """Имя из стоп-листа (шум) — не кандидат в дубли. Один return: bool."""
    return name in _DUP_IGNORE or name.startswith("__")


def _body_size(lines, start, indent):
    """Число непустых строк тела функции от start+1 до дедента. Один return: int."""
    size = 0
    for line in lines[start + 1:]:
        stripped = line.strip()
        if stripped and (len(line) - len(line.lstrip()) <= indent):
            break
        if stripped:
            size += 1
    return size


def _duplicates(index):
    """Функции, определённые в >1 файле, исключая шум. Один return: sorted list."""
    dups = [(name, sorted(files)) for name, files in index.items() if len(files) > 1]
    dups.sort(key=lambda x: (-len(x[1]), x[0]))
    return dups


def report(dups, root=""):
    """Собирает текстовый отчёт. Один return: str."""
    out = "Дублей не найдено. Функции уникальны."
    if dups:
        lines = ["Найденные повторения функций (кандидаты на общий код):", ""]
        for name, files in dups:
            lines.append(f"  {name}  ({len(files)}):")
            for f in files:
                lines.append(f"      {_rel(f, root)}")
        lines.append("")
        lines.append("Проверь вручную: это настоящие дубли (одинаковая логика) "
                     "или одноимённые, но разные функции.")
        out = "\n".join(lines)
    return out


def _rel(path, root):
    """Путь относительно root (если возможно). Один return: str."""
    shown = path
    if root and os.path.abspath(path).startswith(os.path.abspath(root)):
        shown = os.path.relpath(path, root)
    return shown


def main():
    """Точка входа. Один return: int (код выхода)."""
    args = sys.argv[1:]
    min_lines = 0
    if "--min-lines" in args:
        pos = args.index("--min-lines")
        min_lines = int(args[pos + 1]) if len(args) > pos + 1 else 0
        del args[pos:pos + 2]
    root = args[0] if args else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index = _load_defs(root, min_lines)
    dups = _duplicates(index)
    print(report(dups, root))
    return 1 if dups else 0


if __name__ == "__main__":
    sys.exit(main())