# -*- coding: utf-8 -*-
"""Сборка шардов english_kb: все файлы english_kb_partN.py рядом с модулем.

Шард — отдельный файл `algos/english_kb_partN.py` с переменными
TOPICS (словарь «тема -> текст») и TOPIC_TEST (список пар «тема, ключи»).
Число шардов не фиксировано: модуль сам находит part1, part2, ... по номеру.
Файлы грузятся по пути, поэтому sys.path и упаковка проекта значения не имеют.

Модуль только собирает шарды воедино и ничего не пишет на диск.
"""
import glob
import importlib.util
import os

PREFIX = "english_kb_part"


def shard_paths(folder=None):
    """Пути шардов, отсортированные по номеру в имени."""
    where = folder or os.path.dirname(os.path.abspath(__file__))
    found = []
    for path in glob.glob(os.path.join(where, PREFIX + "*.py")):
        suffix = os.path.basename(path)[:-3][len(PREFIX):]
        if suffix.isdigit():
            found.append((int(suffix), path))
    found.sort()
    return [path for _, path in found]


def load_shard(path):
    """Модуль шарда, загруженный по пути файла."""
    name = PREFIX + "_" + str(abs(hash(path)))
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def shards():
    """Список загруженных модулей-шардов."""
    return [load_shard(path) for path in shard_paths()]


def topics(items=None):
    """Словарь тем из всех шардов; при повторе ключа побеждает первый шард."""
    result = {}
    for shard in items if items is not None else shards():
        for key, text in getattr(shard, "TOPICS", {}).items():
            result.setdefault(key, text)
    return result


def test_words(items=None):
    """Список пар (тема, ключи) из всех шардов по порядку номеров."""
    result = []
    for shard in items if items is not None else shards():
        result.extend(getattr(shard, "TOPIC_TEST", ()))
    return result


def shard_stats(items=None):
    """Сколько тем и тестовых записей даёт каждый шард."""
    result = []
    for shard in items if items is not None else shards():
        name = os.path.basename(getattr(shard, "__file__", "?"))[:-3]
        result.append((name, len(getattr(shard, "TOPICS", {})),
                       len(getattr(shard, "TOPIC_TEST", ()))))
    return result
