# -*- coding: utf-8 -*-
"""normalize_english_kb.py — приведение part-файлов базы знаний к срезам реестра.

Источник правды по темам — algos/english_kb.py (_EN_KB и _TOPIC_TEST).
Файлы algos/english_kb_part*.py должны быть срезами: NAMES + выборка из
реестра, без второй копии определений. Скрипт ловит и лечит три дрейфа:

  * часть снова стала модулем-данными (TOPICS = {...});
  * в реестре нет темы, объявленной в части-данных;
  * срез собран не по канону (порядок TOPIC_TEST не совпадает с NAMES).

Запуск:
    python tools/normalize_english_kb.py            # привести к канону
    python tools/normalize_english_kb.py --check    # только отчёт, код 1 при дрейфе
"""
import importlib
import io
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ALGOS = os.path.join(ROOT, "algos")
REGISTRY = os.path.join(ALGOS, "english_kb.py")

SLICE = '''# -*- coding: utf-8 -*-
"""{title}

Каркас будущего разбиения базы. Источник правды — algos/english_kb.py:
здесь только срез реестра по своим темам, чтобы не держать вторую копию
определений (они уже разошлись с основной базой и не читались никем).
"""
from algos.english_kb import _TOPIC_TEST as _ALL_TRIGGERS
from algos.english_kb import _EN_KB

NAMES = (
{names})

TOPICS = {{name: _EN_KB[name] for name in NAMES}}

_KEYS = dict(_ALL_TRIGGERS)

TOPIC_TEST = [(name, _KEYS[name]) for name in NAMES]

del _ALL_TRIGGERS, _KEYS
'''


def _wrap(text, width=100):
    """Режет строку по словам под ширину строки. Один return: list."""
    chunks = []
    current = ""
    for word in text.split():
        candidate = (current + " " + word).strip()
        fits = len(candidate) <= width
        if fits:
            current = candidate
        else:
            if current:
                chunks.append(current)
            current = word
    if current:
        chunks.append(current)
    return chunks


def _dict_lines(key, value):
    """Строки словаря реестра для одной темы. Один return: list."""
    chunks = _wrap(value)
    lines = ['    "%s": (' % key]
    for index, chunk in enumerate(chunks):
        tail = " " if index < len(chunks) - 1 else ""
        lines.append('        "%s%s"' % (chunk.replace('"', '\\"'), tail))
    lines.append("    ),")
    return lines


def _test_lines(key, keywords):
    """Строка списка триггеров для одной темы. Один return: list."""
    inner = ", ".join('"%s"' % word.replace('"', '\\"') for word in keywords)
    return ['    ("%s", (%s)),' % (key, inner)]


def _slice_text(title, names):
    """Текст среза для набора тем. Один return: str."""
    block = "".join('    "%s",\n' % name for name in names)
    return SLICE.format(title=title, names=block)


def _part_files():
    """Все файлы частей базы. Один return: list."""
    return sorted(name for name in os.listdir(ALGOS)
                  if name.startswith("english_kb_part") and name.endswith(".py"))


def _module(stem):
    """Импорт модуля части. Один return: module."""
    return importlib.import_module("algos.%s" % stem)


def _title(module):
    """Первая строка docstring модуля. Один return: str."""
    doc = (module.__doc__ or "").strip().splitlines()
    return doc[0] if doc else "English KB part"


def _drift(module):
    """Что не так с частью: 'data', 'mismatch', 'order' или None. Один return: str|None."""
    problem = None
    if not hasattr(module, "NAMES"):
        problem = "data"
    elif [name for name, _ in module.TOPIC_TEST] != list(module.TOPICS):
        problem = "order"
    return problem


def _registry_mismatches(module, registry):
    """Темы части, которых нет в реестре или они расходились. Один return: list."""
    return [key for key, value in (getattr(module, "TOPICS", {}) or {}).items()
            if registry.get(key) != value]


def _insert(text, close_marker, new_lines, reverse_index):
    """Вставляет строки перед закрывающей скобкой раздела. Один return: str."""
    lines = text.split("\r\n")
    position = lines.index(close_marker) if reverse_index == 0 else len(lines) - 1 - lines[::-1].index(close_marker)
    merged = lines[:position] + new_lines + lines[position:]
    return "\r\n".join(merged)


def _port(registry, parts):
    """Добавляет недостающие темы частей-данных в реестр. Один return: tuple."""
    known = set(registry)
    text = io.open(REGISTRY, encoding="utf-8", newline="").read()
    new_defs = []
    new_tests = []
    for module in parts:
        for key, value in (getattr(module, "TOPICS", {}) or {}).items():
            if key not in known:
                known.add(key)
                new_defs.extend(_dict_lines(key, value))
        for key, keywords in (getattr(module, "TOPIC_TEST", []) or []):
            if key not in known:
                new_tests.extend(_test_lines(key, keywords))
    if new_tests:
        text = _insert(text, "]", new_tests, 1)
    if new_defs:
        text = _insert(text, "}", new_defs, 0)
    if new_defs or new_tests:
        io.open(REGISTRY, "w", encoding="utf-8", newline="").write(text)
    return len(new_defs), len(new_tests)


def main(argv):
    """Точка входа. Один return: int (код выхода)."""
    check_only = "--check" in argv
    sys.path.insert(0, ROOT)
    kb = importlib.import_module("algos.english_kb")
    registry = kb._EN_KB
    modules = [(stem, _module(stem)) for stem in (name[:-3] for name in _part_files())]
    data_parts = [module for _, module in modules if _drift(module) == "data"]
    problems = [(stem, _drift(module)) for stem, module in modules if _drift(module)]
    mismatches = [(stem, _registry_mismatches(module, registry))
                  for stem, module in modules if _registry_mismatches(module, registry)]
    code = 0
    if check_only:
        print("parts:", len(modules), "| data:", len(data_parts),
              "| drift:", len(problems), "| registry mismatches:", len(mismatches))
        for stem, problem in problems[:10]:
            print("  drift:", stem, problem)
        for stem, keys in mismatches[:10]:
            print("  mismatch:", stem, keys[:3])
        code = 1 if (problems or mismatches) else 0
    else:
        ported = _port(registry, data_parts)
        print("ported definitions/triggers:", ported)
        for stem, module in modules:
            fresh = _module(stem) if _drift(module) else module
            title = _title(fresh)
            names = list(getattr(fresh, "TOPICS", {}) or {})
            path = os.path.join(ALGOS, stem + ".py")
            with io.open(path, "w", encoding="utf-8", newline="\r\n") as handle:
                handle.write(_slice_text(title, names))
        print("slices written:", len(modules))
    return code


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
