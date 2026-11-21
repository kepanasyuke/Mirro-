# -*- coding: utf-8 -*-
"""check_shadowed_routes.py — темы, чей вопрос перебивается чужим триггером.

Матчер `try_english` берёт самый длинный найденный ключ, поэтому тема может
проиграть триггеру другой темы: на «what is music?» отвечает `art`.
Такие темы не отвечают своим текстом, пока чужой ключ не убран.

Источник правды — `algos/english_kb.py` (`_EN_KB` и `_TOPIC_TEST`); файл только
разбирается через `ast`, модуль не импортируется.

Запуск:
    python tools/check_shadowed_routes.py            # отчёт, код 1 при находках
    python tools/check_shadowed_routes.py --list     # перечислить все имена
    python tools/check_shadowed_routes.py <путь>     # проверить другой файл
"""
import ast
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT = os.path.join(ROOT, "algos", "english_kb.py")
if ROOT not in sys.path:
    sys.path.insert(0, ROOT)


def target_path():
    """Путь к файлу словаря: аргумент или стандартное место в проекте."""
    args = [item for item in sys.argv[1:] if not item.startswith("--")]
    path = args[0] if args else DEFAULT
    return os.path.abspath(path)


def literals(path):
    """Пара (_EN_KB, _TOPIC_TEST) из файла словаря."""
    with open(path, encoding="utf-8") as handle:
        tree = ast.parse(handle.read())
    found = {"_EN_KB": {}, "_TOPIC_TEST": []}
    for node in tree.body:
        is_assign = isinstance(node, ast.Assign)
        name = getattr(node.targets[0], "id", "") if is_assign else ""
        if name in found:
            found[name] = ast.literal_eval(node.value)
    return found["_EN_KB"], found["_TOPIC_TEST"]


def winner(query, tests):
    """Тема, чей ключ сработал на запрос — по тем же правилам, что в try_english.

    Совпадение проверяется через `_key_hit` (границы слова), а при равной длине
    выигрывает точное имя темы: иначе «hat» ловилось бы внутри «what is…».
    """
    from algos.english_kb import _key_hit
    best, topic_name, best_exact = -1, None, False
    for topic, keys in tests:
        for key in keys or ():
            if isinstance(key, str) and key and _key_hit(query, key):
                exact = key == topic
                if (len(key), exact) > (best, best_exact):
                    best, best_exact, topic_name = len(key), exact, topic
    return topic_name


def shadowed(topics, tests):
    """Темы, на вопрос о которых отвечает другая тема."""
    result = []
    for name in topics:
        if winner("what is " + name + "?", tests) != name:
            result.append(name)
    return result


def main():
    """Печатает сводку и возвращает код: 0 — перекрытий нет, 1 — есть."""
    path = target_path()
    if not os.path.exists(path):
        print("нет файла:", path)
        return 1
    topics, tests = literals(path)
    names = shadowed(topics, tests)
    ok = not names
    print("shadowed: %d | topics: %d | data: %d" % (len(names), len(topics), len(tests)))
    if names:
        print("перекрыты: " + ", ".join(names if "--list" in sys.argv else names[:10]))
        print("лечится: python tools/fix_shadowed_routes.py --apply")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
