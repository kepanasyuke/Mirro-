# -*- coding: utf-8 -*-
"""check_duplicates.py — поиск повторяющихся функций по проекту.

Исключает заведомо ложные срабатывания:
  - дубликаты локальных помощников (rec, __init__ — случайные);
  - методы классов (__init__/__repr__ логично дублируются).
Печатает группы функций (name) определённых более чем в одном файле,
чтобы человек решил, выносить общее или нет.

Запуск:  python tools/check_duplicates.py [каталог]
"""
import os, re, sys
from collections import defaultdict

_DEF = re.compile(r"^\s*def\s+(\w+)\s*\(")
_DUP_IGNORE = {"__init__", "__repr__", "__str__", "rec"}  # заведомо локальные

def _load_defs(root):
    """Собирает {имя_функции: [файлы]}. Один return: dict."""
    index = defaultdict(set)
    for dirpath, _dirs, files in os.walk(root):
        if "__pycache__" in dirpath or ".git" in dirpath:
            continue
        for fname in files:
            if not fname.endswith(".py"):
                continue
            path = os.path.join(dirpath, fname)
            try:
                with open(path, "r", encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        m = _DEF.match(line)
                        if m:
                            index[m.group(1)].add(path)
            except OSError:
                continue
    return index

def _duplicates(index):
    """Функции, определённые в >1 файле, исключая shУm-шум. Один return: sorted list."""
    dups = [(name, sorted(files)) for name, files in index.items()
            if len(files) > 1 and name not in _DUP_IGNORE]
    dups.sort(key=lambda x: (-len(x[1]), x[0]))
    return dups

def report(dups):
    """Собирает текстовый отчёт. Один return: str."""
    if not dups:
        return "Дублей не найдено. Функции уникальны."
    lines = ["Найденные повторения функций (кандидаты на общий код):", ""]
    for name, files in dups:
        lines.append(f"  {name}  ({len(files)}):")
        for f in files:
            lines.append(f"      {f}")
    lines.append("")
    lines.append("Проверь: это настоящие дубли (одинаковая логика) или одноимённые-lок-ально разные функции.")
    return "\n".join(lines)

def main():
    """Точка входа. Один return: int (код выхода)."""
    root = sys.argv[1] if len(sys.argv) > 1 else os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    index = _load_defs(root)
    dups = _duplicates(index)
    print(report(dups))
    return 1 if dups else 0

if __name__ == "__main__":
    sys.exit(main())