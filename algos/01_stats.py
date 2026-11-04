# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 01 · Статистика и вероятность (10 алгоритмов)
Чистый Python, без numpy.
"""

import math, random
from collections import Counter


def mean(xs):
    """Среднее арифметическое."""
    return sum(xs) / len(xs) if xs else 0.0


def median(xs):
    """Медиана. Один return: float."""
    s = sorted(xs)
    n = len(s)
    result = 0.0
    if n:
        mid = n // 2
        result = s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2
    return result


def mode(xs):
    """Мода — самое частое значение. Один return: значение|None."""
    result = None
    if xs:
        result = Counter(xs).most_common(1)[0][0]
    return result


def variance(xs):
    """Дисперсия (несмещённая). Один return: float."""
    result = 0.0
    if len(xs) >= 2:
        m = mean(xs)
        result = sum((x - m) ** 2 for x in xs) / (len(xs) - 1)
    return result


def stddev(xs):
    """Стандартное отклонение."""
    return math.sqrt(variance(xs))


def percentile(xs, p):
    """Процентиль (0..100). Один return: float."""
    result = 0.0
    if xs:
        s = sorted(xs)
        k = (len(s) - 1) * p / 100.0
        lo = int(math.floor(k))
        hi = int(math.ceil(k))
        result = s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)
    return result


def covariance(xs, ys):
    """Ковариация двух рядов. Один return: float."""
    result = 0.0
    same_len = len(xs) == len(ys)
    if same_len and len(xs) >= 2:
        mx, my = mean(xs), mean(ys)
        result = sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - 1)
    return result


def pearson(xs, ys):
    """Корреляция Пирсона. Один return: float."""
    sx, sy = stddev(xs), stddev(ys)
    result = 0.0
    if sx and sy:
        result = covariance(xs, ys) / (sx * sy)
    return result


def normalize(xs):
    """Нормировка в [0,1] (min-max). Один return: list."""
    result = []
    if xs:
        mn, mx = min(xs), max(xs)
        rng = mx - mn
        result = [(x - mn) / rng if rng else 0.0 for x in xs]
    return result


def zscore(xs):
    """Z-оценка (стандартизация). Один return: list."""
    result = []
    if xs:
        m, s = mean(xs), stddev(xs)
        result = [(x - m) / s if s else 0.0 for x in xs]
    return result


if __name__ == "__main__":
    data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    print("mean", mean(data))
    print("median", median(data))
    print("mode", mode(data))
    print("std", round(stddev(data), 3))
    print("p90", percentile(data, 90))
    print("norm", [round(x, 2) for x in normalize(data)][:4])