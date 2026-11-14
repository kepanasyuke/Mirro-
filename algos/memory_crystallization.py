# -*- coding: utf-8 -*-
"""Mirro Algorithms — 33 · Свёртывающая кристаллизация памяти (Memory Crystallization)

База Опыта (graph.experience — атрибут графа, список латентных векторов) со
временем накапливает дублирующиеся следы успешных эпох и забивает RAM. Этот
модуль находит группы схожих (косинусно близких) векторов и «сворачивает» каждую
в единый центроид — кристалл знаний, высвобождая память без потери смысла.

Работает на graph.experience (атрибут KnowledgeGraph, не dict-поле). Функции
атомарны, без continue, по LINTER.md.
"""
import math

_EPS = 1e-8


def _is_number(x):
    """Конечное число (отсекает NaN/inf/строки). Один return: bool."""
    return isinstance(x, (int, float)) and x == x and x not in (float("inf"), float("-inf"))


def _vector_ok(vec):
    """Вектор пригоден для центроида: непустой, все элементы — конечные числа.
    Один return: bool."""
    ok = isinstance(vec, (list, tuple)) and len(vec) > 0
    if ok:
        ok = all(_is_number(x) for x in vec)
    return ok


def _is_zero_vector(vec):
    """Все координаты — нули (центроид такой группы обнулил бы кристалл).
    Один return: bool."""
    return _vector_ok(vec) and all(float(x) == 0.0 for x in vec)


def _is_numeric_vector(vec):
    """Годится ли вектор для косинуса: непустая последовательность чисел конечной
    длины. None, строки, вложенные списки → False. Один return: bool."""
    is_vector = isinstance(vec, (list, tuple)) and len(vec) > 0
    is_numeric = is_vector and all(
        isinstance(x, (int, float)) and not isinstance(x, bool) and x == x
        and abs(x) != float("inf")
        for x in vec)
    return bool(is_numeric)


def calculate_centroid_vector(vectors_list):
    """Средний вектор (центроид-кристалл) группы паттернов.

    Раньше функция падала IndexError на пустом списке и TypeError на None
    (опыт мог остаться битым после ручного восстановления). Теперь негодные
    векторы отбрасываются, а вектора разной длины дополняются нулями.
    Пустой/некорректный вход → []. Один return: list."""
    vectors = [vec for vec in (vectors_list or []) if _is_numeric_vector(vec)]
    centroid = []
    if vectors:
        width = max(len(vec) for vec in vectors)
        centroid = [0.0] * width
        for vec in vectors:
            for i, value in enumerate(vec):
                centroid[i] += float(value)
        centroid = [total / len(vectors) for total in centroid]
    return centroid


def _cosine_similarity(a, b):
    """Косинусное сходство двух векторов. Один return: float."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + _EPS)


def _similar(a, b, threshold):
    """Совпадают ли два вектора по смыслу: одинаковой длины, числовые, не
    нулевые и косинус выше порога. Нули/NaN/мусор не сворачиваются никогда —
    иначе центроид группы превратился бы в пустой вектор. Один return: bool."""
    ok = (_vector_ok(a) and _vector_ok(b) and len(a) == len(b)
          and not _is_zero_vector(a) and not _is_zero_vector(b))
    sim = 0.0
    if ok:
        sim = _cosine_similarity(a, b)
    return ok and sim == sim and sim > threshold


def _sanitized(exp_list):
    """Опыт после сжатия: элементы остаются списками, мусор не теряется.
    Один return: list."""
    return [list(vec) if isinstance(vec, (list, tuple)) else vec for vec in exp_list]


def try_crystallize_experience(graph, similarity_threshold=0.92):
    """Сворачивает избыточный опыт (graph.experience) в центроидные кристаллы.
    Битые следы (None, строки, вложенные списки) не роняют свёртку: они
    остаются в опыте как есть и не участвуют в сравнении.
    Возвращает число кристаллов ПОСЛЕ сжатия. Один return: int."""
    exp_list = getattr(graph, "experience", None) or []
    merged = []
    if isinstance(exp_list, (list, tuple)) and 2 <= len(exp_list) <= 1000:
        consumed = set()
        for i in range(len(exp_list)):
            if i not in consumed:
                group = [exp_list[i]]
                for j in range(i + 1, len(exp_list)):
                    if j not in consumed and _similar(exp_list[i], exp_list[j], similarity_threshold):
                        group.append(exp_list[j])
                        consumed.add(j)
                crystal = exp_list[i]
                if _vector_ok(exp_list[i]):
                    crystal = list(exp_list[i])
                if len(group) > 1 and all(_vector_ok(v) for v in group):
                    crystal = calculate_centroid_vector(group)
                # не сворачиваем группу в пустоту: центроид обязан быть вектором
                merged.append(crystal if _vector_ok(crystal) else group[0])
                consumed.add(i)
        graph.experience = _sanitized(merged)
    return len(merged)


if __name__ == "__main__":
    class FakeGraph(object):  # облегчённая заглушка графа с атрибутом experience
        pass
    g = FakeGraph()
    g.experience = [[1.0, 0.5, 0.0], [1.0, 0.51, 0.0], [0.99, 0.5, 0.0], [0.0, 0.0, 1.0]]
    n = try_crystallize_experience(g, similarity_threshold=0.95)
    print("crystals:", n, "|", g.experience)