# -*- coding: utf-8 -*-
"""fix_shadowed_routes.py — убирает причины перекрытия тем в algos/english_kb.py.

Перекрытие (на «what is music?» отвечает `art`) возникает из-за трёх причин:
  1) у темы-победителя в триггерах стоит слово, которое является именем другой темы;
  2) в триггерах есть фраза-обвязка вида «what is so» — она ловит любой вопрос на «so…»;
  3) у темы нет собственного имени в своих триггерах.

Скрипт правит только список _TOPIC_TEST: убирает чужие имена темы-победителя,
выкидывает фразы, начинающиеся с «what is», и дописывает теме её собственное имя.
Правятся только изменившиеся записи, форматирование остального файла не трогается.
Тексты словаря, порядок тем и значения не меняются.

Запуск:
    python tools/fix_shadowed_routes.py            # показать
    python tools/fix_shadowed_routes.py --apply    # записать
"""
import ast
import os
import sys

TARGET = "_TOPIC_TEST"
BOILERPLATE = "what is"


def project_root():
    """Корень проекта: ближайший каталог вверх, где лежит algos/english_kb.py."""
    path = os.path.dirname(os.path.abspath(__file__))
    for _ in range(8):
        if os.path.exists(os.path.join(path, "algos", "english_kb.py")):
            return path
        path = os.path.dirname(path)
    return os.path.dirname(os.path.abspath(__file__))


def target_path():
    """Путь к english_kb.py: первый аргумент или стандартное место в проекте."""
    args = [item for item in sys.argv[1:] if not item.startswith("--")]
    path = args[0] if args else os.path.join(project_root(), "algos", "english_kb.py")
    return os.path.abspath(path)


def kb_and_tests(tree):
    """Словарь тем и список триггеров из дерева разбора."""
    topics, tests = {}, []
    for node in tree.body:
        is_assign = isinstance(node, ast.Assign)
        name = getattr(node.targets[0], "id", "") if is_assign else ""
        if name == "_EN_KB":
            topics = ast.literal_eval(node.value)
        if name == TARGET:
            tests = ast.literal_eval(node.value)
    return topics, tests


def element_node(tree):
    """Узел списка _TOPIC_TEST."""
    result = None
    for node in tree.body:
        if isinstance(node, ast.Assign) and getattr(node.targets[0], "id", "") == TARGET:
            result = node.value
    return result


def cleaned(entry, names):
    """Новый список ключей для одной темы."""
    topic, keys = entry
    result = []
    for key in keys or ():
        is_alien = key in names and key != topic
        is_boiler = isinstance(key, str) and key.strip().lower().startswith(BOILERPLATE)
        if not is_alien and not is_boiler:
            result.append(key)
    if topic not in result:
        result.insert(0, topic)
    return topic, tuple(result)


def line_starts(data):
    """Байтовые смещения начал строк."""
    result = [0]
    for index, byte in enumerate(data):
        if byte == 10:
            result.append(index + 1)
    return result


def rebuild(source, tree, names):
    """Текст с исправленным списком _TOPIC_TEST: меняются только изменённые записи."""
    node = element_node(tree)
    data = source.encode("utf-8")
    starts = line_starts(data)
    entries = [ast.literal_eval(ast.Expression(elt)) for elt in node.elts]
    fixed = [cleaned(entry, names) for entry in entries]
    edits = []
    for before, after, elt in zip(entries, fixed, node.elts):
        if before == after:
            continue
        begin = starts[elt.lineno - 1] + elt.col_offset
        end = starts[elt.end_lineno - 1] + elt.end_col_offset
        blob = ("(%r, %r)" % (after[0], after[1])).encode("utf-8")
        edits.append((begin, end, blob))
    result = data
    for begin, end, blob in sorted(edits, reverse=True):
        result = result[:begin] + blob + result[end:]
    return result.decode("utf-8"), len(edits)


def main():
    """Показывает или применяет правку маршрутов."""
    path = target_path()
    write = "--apply" in sys.argv
    if not os.path.exists(path):
        print("нет файла:", path)
        return 1
    source = open(path, encoding="utf-8").read()
    tree = ast.parse(source)
    topics, tests = kb_and_tests(tree)
    names = set(topics)
    names.update(topic for topic, _ in tests)
    updated, changed = rebuild(source, tree, names)
    print("файл:", path)
    print("тем в словаре:", len(topics), "записей в тестах:", len(tests))
    print("исправлено записей:", changed)
    ast.parse(updated)
    print("синтаксис: OK")
    if write:
        with open(path, "w", encoding="utf-8", newline="\n") as handle:
            handle.write(updated)
        print("записано")
    else:
        print("запись не делалась, добавьте --apply")
    return 0


if __name__ == "__main__":
    sys.exit(main())
