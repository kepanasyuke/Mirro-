# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 03 · Поиск и ранжирование (10 алгоритмов)
Чистый Python.
"""

import math
from collections import Counter, defaultdict


def linear_search(arr, x):
    """Линейный поиск: индекс элемента или -1."""
    for i, v in enumerate(arr):
        if v == x:
            return i
    return -1


def binary_search(arr, x):
    """Бинарный поиск в отсортированном массиве."""
    lo, hi = 0, len(arr) - 1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            return mid
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return -1


def bm25(query, docs, k1=1.5, b=0.75):
    """BM25 ранжирование документов по запросу.
    docs: список строк. Возвращает [(индекс, score)] по убыванию."""
    N = len(docs)
    toks = [d.lower().split() for d in docs]
    avgdl = sum(len(t) for t in toks) / N if N else 1
    # df
    df = {}
    for t in toks:
        for w in set(t):
            df[w] = df.get(w, 0) + 1
    q = query.lower().split()
    scores = []
    for i, t in enumerate(toks):
        score = 0.0
        tf = Counter(t)
        for w in q:
            if w in tf:
                idf = math.log((N - df.get(w, 0) + 0.5) / (df.get(w, 0) + 0.5) + 1)
                f = tf[w]
                score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * len(t) / avgdl))
        scores.append((i, score))
    return sorted(scores, key=lambda x: -x[1])


def cosine_similarity(vec_a, vec_b):
    """Косинусное сходство векторов {слово: вес}."""
    common = set(vec_a) & set(vec_b)
    if not common:
        return 0.0
    dot = sum(vec_a[w] * vec_b[w] for w in common)
    na = math.sqrt(sum(v * v for v in vec_a.values()))
    nb = math.sqrt(sum(v * v for v in vec_b.values()))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


def edit_distance(a, b):
    """Расстояние Левенштейна."""
    dp = list(range(len(b) + 1))
    for i, ca in enumerate(a, 1):
        prev = dp[0]
        dp[0] = i
        for j, cb in enumerate(b, 1):
            cur = dp[j]
            cost = 0 if ca == cb else 1
            dp[j] = min(dp[j] + 1, dp[j - 1] + 1, prev + cost)
            prev = cur
    return dp[-1]


def hamming(a, b):
    """Расстояние Хэмминга."""
    return sum(x != y for x, y in zip(a, b))


def interpolation_search(sorted_arr, x):
    """Интерполяционный поиск по отсортированному массиву."""
    lo, hi = 0, len(sorted_arr) - 1
    while lo <= hi and sorted_arr[lo] <= x <= sorted_arr[hi]:
        if sorted_arr[lo] == sorted_arr[hi]:
            return lo if sorted_arr[lo] == x else -1
        pos = lo + int((hi - lo) * (x - sorted_arr[lo]) / (sorted_arr[hi] - sorted_arr[lo]))
        if sorted_arr[pos] == x:
            return pos
        if sorted_arr[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return -1


def fuzzy_match(query, candidates, max_dist=2):
    """Нечёткий поиск: возвращает кандидатов с расстоянием <= max_dist."""
    out = []
    for c in candidates:
        d = edit_distance(query.lower(), c.lower())
        if d <= max_dist:
            out.append((c, d))
    return sorted(out, key=lambda x: x[1])


def invert_index(docs):
    """Инвертированный индекс: {слово: [док_индексы]}."""
    idx = defaultdict(list)
    for i, d in enumerate(docs):
        for w in set(d.lower().split()):
            idx[w].append(i)
    return dict(idx)


def most_common_n(docs, n=3):
    """Самые частые слова в наборе документов."""
    c = Counter()
    for d in docs:
        c.update(d.lower().split())
    return c.most_common(n)


if __name__ == "__main__":
    arr = [1, 3, 5, 7, 9, 11]
    print("binary:", binary_search(arr, 7))
    docs = ["python программирование язык", "python код скрипт", "нейросеть обучение модель"]
    print("bm25:", bm25("python", docs)[:2])
    a = {"word": 2, "code": 1}
    b = {"word": 1, "code": 3}
    print("cos:", round(cosine_similarity(a, b), 3))
    print("edit:", edit_distance("кот", "кода"))
    print("fuzzy:", fuzzy_match("питон", ["python", "питона", "пайтон", "солнце"]))