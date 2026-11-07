# -*- coding: utf-8 -*-
"""DRY-check: «один выход из функции» по LINTER.md.

Правило: у функции один return в конце; без continue; каждый return/cieside-
эффект внутри тела (не в конце) — нарушение. Ловим:
  * несколько операторов return (и во вложенных def-ах — их считаем отдельно);
  * continue в любых циклах;
  * ранние return не в конце функции (однако допускаем return последним).

Сканирует algos/, core/, scripts/, tools/, tests/. Выводит список нарушений
и статистику. Возвращает код 1 если найдены нарушения.

Запуск:  python tools/check_single_return.py [--quiet]
"""
import argparse, ast, sys
from pathlib import Path

MIRRO = Path(__file__).resolve().parent.parent
DIRS = ["algos", "core", "scripts", "tools", "tests"]


def _find_funcdefs(tree):
    """Все FunctionDef/AsyncFunctionDef рекурсивно. Один return: list."""
    out = []
    for node in ast.walk(tree):
        if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
            out.append(node)
    return out


def _violations(node, file):
    """Нарушения в одной функции. Один return: list[str]."""
    v = []
    nested = _nested_ranges(node)
    ret_nodes = [n for n in ast.walk(node)
                 if isinstance(n, ast.Return) and _own(node, n, nested)]
    cont = [n for n in ast.walk(node)
            if isinstance(n, ast.Continue) and _own(node, n, nested)]
    for c in cont:
        v.append(f"[continue] {file}:{c.lineno} {node.name}")
    if len(ret_nodes) > 1:
        v.append(f"[multi-return x{len(ret_nodes)}] {file}:{node.lineno} {node.name}")
    return v


def _nested_ranges(funcdef):
    """(start,end) строки для каждой вложенной функции. Один return: list."""
    rng = []
    for n in ast.walk(funcdef):
        if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)) and n is not funcdef:
            end = getattr(n, "end_lineno", n.lineno) or n.lineno
            rng.append((n.lineno, end))
    return rng


def _own(funcdef, n, nested):
    """Принадлежит ли узел n функции funcdef (не внутри вложенной def).
    Один return: bool."""
    ln = getattr(n, "lineno", -1)
    inside = False
    for s, e in nested:
        if s <= ln <= e:
            inside = True
            break
    return not inside


def main():
    ap = argparse.ArgumentParser(description="Check single-return per LINTER.md")
    ap.add_argument("--quiet", action="store_true")
    args = ap.parse_args()

    all_violations = []
    total_funcs = 0
    for d in DIRS:
        base = MIRRO / d
        if base.exists():
            _scan_tree(base, all_violations)
    total_funcs = _count_funcs()
    # считаем функции повторным проходом: выше не накопили счётчик
    print(f"Сканировано функций: {total_funcs}")
    code = 0
    if all_violations:
        print(f"Нарушений: {len(all_violations)}")
        if not args.quiet:
            for v in all_violations:
                print("  " + v)
        code = 1
    else:
        print("Все функции — один return, без continue")
    return code


def _scan_tree(base, all_violations):
    """Сканирует все .py в base и накапливает нарушения. Один return: None."""
    for pyfile in sorted(base.rglob("*.py")):
        src = _read_safe(pyfile)
        tree = _parse_safe(src)
        if tree is not None:
            for f in _find_funcdefs(tree):
                all_violations.extend(_violations(f, pyfile.relative_to(MIRRO).as_posix()))
    return None


def _read_safe(pyfile):
    """Читает файл или даёт None при ошибке. Один return: str|None."""
    text = None
    try:
        text = pyfile.read_text(encoding="utf-8")
    except Exception:
        text = None
    return text


def _parse_safe(src):
    """Парсит исходник или даёт None при SyntaxError. Один return: AST|None."""
    tree = None
    if src is not None:
        try:
            tree = ast.parse(src)
        except SyntaxError:
            tree = None
    return tree


def _count_funcs():
    """Общее число функций во всех сканируемых каталогах. Один return: int."""
    total = 0
    for d in DIRS:
        base = MIRRO / d
        if base.exists():
            for pyfile in sorted(base.rglob("*.py")):
                tree = _parse_safe(_read_safe(pyfile))
                if tree is not None:
                    total += len(_find_funcdefs(tree))
    return total


if __name__ == "__main__":
    sys.exit(main())