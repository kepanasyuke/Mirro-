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


def calculate_centroid_vector(vectors_list):
    """Средний вектор (центроид-кристалл) группы паттернов. Один return: list."""
    centroid = [0.0] * len(vectors_list[0])
    for vec in vectors_list:
        for i in range(len(centroid)):
            centroid[i] += vec[i]
    return [c / len(vectors_list) for c in centroid]


def _cosine_similarity(a, b):
    """Косинусное сходство двух векторов. Один return: float."""
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    return dot / (na * nb + 1e-8)


def try_crystallize_experience(graph, similarity_threshold=0.92):
    """Сворачивает избыточный опыт (graph.experience) в центроидные кристаллы.
    Возвращает число кристаллов ПОСЛЕ сжатия. Один return: int."""
    exp_list = getattr(graph, "experience", None) or []
    merged = []
    if len(exp_list) >= 2:
        consumed = set()
        for i in range(len(exp_list)):
            if i not in consumed:
                group = [exp_list[i]]
                for j in range(i + 1, len(exp_list)):
                    if j not in consumed and _cosine_similarity(exp_list[i], exp_list[j]) > similarity_threshold:
                        group.append(exp_list[j])
                        consumed.add(j)
                merged.append(calculate_centroid_vector(group) if len(group) > 1 else list(exp_list[i]))
                consumed.add(i)
        graph.experience = merged
    return len(merged)


if __name__ == "__main__":
    class FakeGraph(object):  # облегчённая заглушка графа с атрибутом experience
        pass
    g = FakeGraph()
    g.experience = [[1.0, 0.5, 0.0], [1.0, 0.51, 0.0], [0.99, 0.5, 0.0], [0.0, 0.0, 1.0]]
    n = try_crystallize_experience(g, similarity_threshold=0.95)
    print("crystals:", n, "|", g.experience)