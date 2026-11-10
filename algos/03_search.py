# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 03 · Поиск и ранжирование (10 алгоритмов)
Чистый Python.
"""

import math
from collections import Counter, defaultdict


def linear_search(arr, x):
    """Линейный поиск: индекс элемента или -1. Один return: int."""
    result = -1
    for i, v in enumerate(arr):
        if v == x:
            result = i
            break
    return result


def binary_search(arr, x):
    """Бинарный поиск в отсортированном массиве. Один return: int."""
    lo, hi = 0, len(arr) - 1
    result = -1
    while lo <= hi:
        mid = (lo + hi) // 2
        if arr[mid] == x:
            result = mid
            break
        if arr[mid] < x:
            lo = mid + 1
        else:
            hi = mid - 1
    return result


def bm25(query, docs, k1=1.5, b=0.75):
    """BM25 ранжирование документов по запросу.
    docs: список строк. Возвращает [(индекс, score)] по убыванию."""
    N = len(docs)
    if N == 0 or not (query or "").strip():
        return []
    toks = [str(d).lower().split() for d in docs]
    avgdl = sum(len(t) for t in toks) / N
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
                dw = df.get(w, 0)
                idf = math.log((N - dw + 0.5) / (dw + 0.5) + 1)
                f = tf[w]
                score += idf * (f * (k1 + 1)) / (f + k1 * (1 - b + b * len(t) / avgdl))
        scores.append((i, score))
    return sorted(scores, key=lambda x: -x[1])


def cosine_similarity(vec_a, vec_b):
    """Косинусное сходство векторов {слово: вес}. Один return: float."""
    common = set(vec_a) & set(vec_b)
    score = 0.0
    if common:
        dot = sum(vec_a[w] * vec_b[w] for w in common)
        na = math.sqrt(sum(v * v for v in vec_a.values()))
        nb = math.sqrt(sum(v * v for v in vec_b.values()))
        if na and nb:
            score = dot / (na * nb)
    return score


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
    """Расстояние Хэмминга; строки разной длины считаются с учётом
    всех различающихся символов по длине большей. Один return: int."""
    a, b = str(a), str(b)
    if len(a) < len(b):
        a, b = b, a
    # лишние символы более длинной строки считаются отличиями
    return sum(x != y for x, y in zip(a, b)) + (len(a) - len(b))


def interpolation_search(sorted_arr, x):
    """Интерполяционный поиск по отсортированному массиву.
    Пустой массив → -1. Один return: int."""
    if not sorted_arr:
        return -1
    lo, hi = 0, len(sorted_arr) - 1
    result = -1
    while lo <= hi and sorted_arr[lo] <= x <= sorted_arr[hi]:
        if sorted_arr[lo] == sorted_arr[hi]:
            result = lo if sorted_arr[lo] == x else -1
            break
        pos = lo + int((hi - lo) * (x - sorted_arr[lo]) / (sorted_arr[hi] - sorted_arr[lo]))
        if sorted_arr[pos] == x:
            result = pos
            break
        if sorted_arr[pos] < x:
            lo = pos + 1
        else:
            hi = pos - 1
    return result


def fuzzy_match(query, candidates, max_dist=2):
    """Нечёткий поиск: возвращает кандидатов с расстоянием <= max_dist.
    Пустой список кандидатов → []. Один return: list."""
    out = []
    q = str(query or "").lower()
    for c in candidates or []:
        d = edit_distance(q, c.lower())
        if d <= max_dist:
            out.append((c, d))
    return sorted(out, key=lambda x: (x[1], str(x[0])))


def invert_index(docs):
    """Инвертированный индекс: {слово: [док_индексы]}.
    Не учитывает пустые/не-строковые документы. Один return: dict."""
    idx = defaultdict(list)
    for i, d in enumerate(docs or []):
        if not d:
            continue
        for w in set(str(d).lower().split()):
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