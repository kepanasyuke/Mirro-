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
    """Медиана."""
    s = sorted(xs)
    n = len(s)
    if n == 0:
        return 0.0
    mid = n // 2
    return s[mid] if n % 2 else (s[mid - 1] + s[mid]) / 2


def mode(xs):
    """Мода — самое частое значение."""
    if not xs:
        return None
    return Counter(xs).most_common(1)[0][0]


def variance(xs):
    """Дисперсия."""
    if len(xs) < 2:
        return 0.0
    m = mean(xs)
    return sum((x - m) ** 2 for x in xs) / (len(xs) - 1)


def stddev(xs):
    """Стандартное отклонение."""
    return math.sqrt(variance(xs))


def percentile(xs, p):
    """Процентиль (0..100)."""
    if not xs:
        return 0.0
    s = sorted(xs)
    k = (len(s) - 1) * p / 100.0
    lo = int(math.floor(k))
    hi = int(math.ceil(k))
    return s[lo] if lo == hi else s[lo] + (s[hi] - s[lo]) * (k - lo)


def covariance(xs, ys):
    """Ковариация двух рядов."""
    if len(xs) != len(ys) or len(xs) < 2:
        return 0.0
    mx, my = mean(xs), mean(ys)
    return sum((x - mx) * (y - my) for x, y in zip(xs, ys)) / (len(xs) - 1)


def pearson(xs, ys):
    """Корреляция Пирсона."""
    sx, sy = stddev(xs), stddev(ys)
    if sx == 0 or sy == 0:
        return 0.0
    return covariance(xs, ys) / (sx * sy)


def normalize(xs):
    """Нормировка в [0,1] (min-max)."""
    if not xs:
        return []
    mn, mx = min(xs), max(xs)
    rng = mx - mn
    return [(x - mn) / rng if rng else 0.0 for x in xs]


def zscore(xs):
    """Z-оценка (стандартизация)."""
    if not xs:
        return []
    m, s = mean(xs), stddev(xs)
    return [(x - m) / s if s else 0.0 for x in xs]


if __name__ == "__main__":
    data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    print("mean", mean(data))
    print("median", median(data))
    print("mode", mode(data))
    print("std", round(stddev(data), 3))
    print("p90", percentile(data, 90))
    print("norm", [round(x, 2) for x in normalize(data)][:4])