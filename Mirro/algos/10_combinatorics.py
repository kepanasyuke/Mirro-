# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 10 · Комбинаторика (12 алгоритмов)
Перестановки, сочетания, размещения, числа Каталана, Стирлинга, Белла,
биномиальные коэффициенты, генерация множеств и др.
"""

import math
from itertools import permutations as _perm


def factorial(n):
    """Факториал (итеративно, для больших n)."""
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


def binomial(n, k):
    """Биномиальный коэффициент C(n, k) без факториалов."""
    if k < 0 or k > n:
        return 0
    k = min(k, n - k)
    r = 1
    for i in range(1, k + 1):
        r = r * (n - k + i) // i
    return r


def permutations_count(n, k=None):
    """Число перестановок из n по k (P(n,k), по умолчанию n!)."""
    k = n if k is None else k
    if k < 0 or k > n:
        return 0
    return factorial(n) // factorial(n - k)


def combinations_count(n, k):
    """Число сочетаний C(n,k)."""
    return binomial(n, k)


def arrangements_count(n, k):
    """Число размещений A(n,k) = n!/(n-k)! — равно P(n,k)."""
    return permutations_count(n, k)


def with_repetition_perm(n, k):
    """Перестановки с повторениями: n^k."""
    return n ** k


def with_repetition_comb(n, k):
    """Сочетания с повторениями: C(n+k-1, k)."""
    return binomial(n + k - 1, k)


def catalan(n):
    """Числа Каталана: C_n = C(2n,n)/(n+1)."""
    return binomial(2 * n, n) // (n + 1)


def stirling_second(n, k):
    """Числа Стирлинга 2-го рода: S(n,k) — разбиения на k непустых подмножеств."""
    if n == k == 0:
        return 1
    if n == 0 or k == 0 or k > n:
        return 0
    # S(n,k) = k*S(n-1,k) + S(n-1,k-1)
    dp = [[0] * (k + 1) for _ in range(n + 1)]
    dp[0][0] = 1
    for i in range(1, n + 1):
        for j in range(1, min(i, k) + 1):
            dp[i][j] = j * dp[i - 1][j] + dp[i - 1][j - 1]
    return dp[n][k]


def bell(n):
    """Числа Белла: разбиения n-элементного множества = sum S(n,k)."""
    return sum(stirling_second(n, k) for k in range(n + 1))


def derangements(n):
    """Число беспорядков (!n)."""
    if n == 0:
        return 1
    a, b = 0, 1
    for i in range(2, n + 1):
        a, b = b, (i - 1) * (a + b)
    return b


def permutations_list(items):
    """Все перестановки списка (как кортежи)."""
    return list(_perm(items))


def subsets(items):
    """Все подмножества (масками)."""
    out = []
    n = len(items)
    for mask in range(1 << n):
        out.append([items[i] for i in range(n) if mask & (1 << i)])
    return out


def combinations_list(items, k):
    """Все сочетания по k (рекурсивно)."""
    out = []

    def rec(start, cur):
        if len(cur) == k:
            out.append(cur[:])
            return
        for i in range(start, len(items)):
            cur.append(items[i])
            rec(i + 1, cur)
            cur.pop()

    rec(0, [])
    return out


def compositions(n, parts=None):
    """Композиции числа n (разбиения с учётом порядка) на положительные части."""
    parts = list(range(1, n + 1)) if parts is None else parts
    out = []

    def rec(rem, cur):
        if rem == 0:
            out.append(cur[:])
            return
        for p in parts:
            if p <= rem:
                cur.append(p)
                rec(rem - p, cur)
                cur.pop()

    rec(n, [])
    return out


def nck_mod(n, k, mod):
    """C(n,k) по модулю (через факториалы и обратные)."""
    if k < 0 or k > n:
        return 0

    def powmod(a, b):
        r = 1
        while b:
            if b & 1:
                r = r * a % mod
            a = a * a % mod
            b >>= 1
        return r

    fact = [1] * (n + 1)
    for i in range(1, n + 1):
        fact[i] = fact[i - 1] * i % mod
    inv_fact_nk = powmod(fact[n - k], mod - 2) if n - k >= 0 else 1
    inv_fact_k = powmod(fact[k], mod - 2) if k >= 0 else 1
    return fact[n] * inv_fact_nk % mod * inv_fact_k % mod


if __name__ == "__main__":
    print("C(10,3):", binomial(10, 3))
    print("P(5,2):", permutations_count(5, 2))
    print("Каталан(5):", catalan(5))
    print("Стирлинг(5,2):", stirling_second(5, 2))
    print("Белл(5):", bell(5))
    print("Беспорядки(4):", derangements(4))
    print("Подмножества [1,2]:", subsets([1, 2]))
    print("Сочетания [1,2,3] по 2:", combinations_list([1, 2, 3], 2))