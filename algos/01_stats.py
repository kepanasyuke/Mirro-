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


def range_stat(xs):
    """Размах выборки (max − min). 0 на пустом списке. Один return: float."""
    result = 0.0
    if xs:
        result = max(xs) - min(xs)
    return result


def midrange(xs):
    """Середина размаха ((min + max)/2). 0 на пустом/нечисловом.
    Один return: float."""
    result = 0.0
    if xs:
        try:
            nums = [float(x) for x in xs]
            result = (min(nums) + max(nums)) / 2
        except Exception:
            result = 0.0
    return result


def percentile(xs, p):
    """Процентиль (0..100). p за пределами диапазона клампится.
    Один return: float."""
    result = 0.0
    if xs:
        p = max(0.0, min(100.0, float(p)))
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
    """Корреляция Пирсона. 0 при разной длине рядов или вырожденном сигм.
    Один return: float."""
    sx, sy = stddev(xs), stddev(ys)
    result = 0.0
    if sx and sy and len(xs) == len(ys):
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


def winsorize(xs, low=0.05, high=0.05):
    """Обрезает выбросы: значения ниже нижнего и выше верхнего процентиля
    заменяются на границы. Один return: list."""
    result = []
    if xs:
        s = sorted(xs)
        n = len(s)
        lo_i = max(0, int(round(low * n)) - 1)
        hi_i = min(n - 1, int(round((1 - high) * n)) - 1)
        cmin, cmax = s[lo_i], s[hi_i]
        result = [max(cmin, min(cmax, x)) for x in xs]
    return result


def geometric_mean(xs):
    """Среднее геометрическое (произведение в степени 1/n).
    0, если есть неположительные элементы или список пуст. Один return: float."""
    result = 0.0
    if xs and all(x > 0 for x in xs):
        result = math.exp(sum(math.log(x) for x in xs) / len(xs))
    return result


def harmonic_mean(xs):
    """Среднее гармоническое (n / сумма обратных).
    0 при пустом списке или нулевых элементах. Один return: float."""
    result = 0.0
    if xs and all(x > 0 for x in xs):
        result = len(xs) / sum(1.0 / x for x in xs)
    return result


if __name__ == "__main__":
    data = [3, 1, 4, 1, 5, 9, 2, 6, 5, 3, 5]
    print("mean", mean(data))
    print("median", median(data))
    print("mode", mode(data))
    print("std", round(stddev(data), 3))
    print("p90", percentile(data, 90))
    print("norm", [round(x, 2) for x in normalize(data)][:4])