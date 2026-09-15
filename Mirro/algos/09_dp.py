# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 09 · Динамическое программирование (10 алгоритмов)
"""


def fib_dp(n):
    "Число Фибоначчи через ДП (табуляция)."
    if n < 2:
        return n
    dp = [0] * (n + 1)
    dp[1] = 1
    for i in range(2, n + 1):
        dp[i] = dp[i - 1] + dp[i - 2]
    return dp[n]


def knapsack(weights, values, capacity):
    """Рюкзак 0/1: максимум ценности при вместимости."""
    n = len(weights)
    dp = [[0] * (capacity + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        w, v = weights[i - 1], values[i - 1]
        for c in range(capacity + 1):
            if w <= c:
                dp[i][c] = max(dp[i - 1][c], dp[i - 1][c - w] + v)
            else:
                dp[i][c] = dp[i - 1][c]
    return dp[n][capacity]


def lis(a):
    """Наибольшая возрастающая подпоследовательность (длина)."""
    from bisect import bisect_left
    tails = []
    for x in a:
        i = bisect_left(tails, x)
        if i == len(tails):
            tails.append(x)
        else:
            tails[i] = x
    return len(tails)


def lcs(a, b):
    """Наибольшая общая подпоследовательность (длина)."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    return dp[n][m]


def lcs_string(a, b):
    """LCS: возвращает саму подпоследовательность."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            if a[i - 1] == b[j - 1]:
                dp[i][j] = dp[i - 1][j - 1] + 1
            else:
                dp[i][j] = max(dp[i - 1][j], dp[i][j - 1])
    # восстановление
    out, i, j = [], n, m
    while i > 0 and j > 0:
        if a[i - 1] == b[j - 1]:
            out.append(a[i - 1]); i -= 1; j -= 1
        elif dp[i - 1][j] > dp[i][j - 1]:
            i -= 1
        else:
            j -= 1
    return "".join(reversed(out))


def coin_change(coins, amount):
    """Минимум монет для суммы (или -1)."""
    INF = float("inf")
    dp = [INF] * (amount + 1)
    dp[0] = 0
    for i in range(1, amount + 1):
        for c in coins:
            if c <= i:
                dp[i] = min(dp[i], dp[i - c] + 1)
    return int(dp[amount]) if dp[amount] != INF else -1


def climb_stairs(n):
    """Сколько способов подняться по лестнице (шаги 1 или 2)."""
    a, b = 1, 2
    for _ in range(2, n):
        a, b = b, a + b
    return 1 if n == 1 else b if n >= 2 else 0


def edit_distance_dp(a, b):
    """Расстояние Левенштейна через ДП."""
    n, m = len(a), len(b)
    dp = [[0] * (m + 1) for _ in range(n + 1)]
    for i in range(n + 1):
        dp[i][0] = i
    for j in range(m + 1):
        dp[0][j] = j
    for i in range(1, n + 1):
        for j in range(1, m + 1):
            cost = 0 if a[i - 1] == b[j - 1] else 1
            dp[i][j] = min(dp[i - 1][j] + 1, dp[i][j - 1] + 1, dp[i - 1][j - 1] + cost)
    return dp[n][m]


def rod_cut(prices, n):
    """Разрезание стержня: максимальная выгода."""
    dp = [0] * (n + 1)
    for i in range(1, n + 1):
        best = 0
        for j in range(1, i + 1):
            if j <= len(prices):
                best = max(best, prices[j - 1] + dp[i - j])
        dp[i] = best
    return dp[n]


def partition_subset(nums):
    """Можно ли разбить на два подмножества с равной суммой."""
    total = sum(nums)
    if total % 2:
        return False
    half = total // 2
    dp = [False] * (half + 1)
    dp[0] = True
    for x in nums:
        for s in range(half, x - 1, -1):
            dp[s] = dp[s] or dp[s - x]
    return dp[half]


def max_subarray(a):
    """Максимальная сумма подмассива (Кадане)."""
    best = cur = a[0] if a else 0
    for x in a[1:]:
        cur = max(x, cur + x)
        best = max(best, cur)
    return best


def min_path_sum(grid):
    """Минимальная сумма пути от (0,0) до (n-1,m-1)."""
    n, m = len(grid), len(grid[0])
    dp = [[0] * m for _ in range(n)]
    dp[0][0] = grid[0][0]
    for i in range(1, n):
        dp[i][0] = dp[i - 1][0] + grid[i][0]
    for j in range(1, m):
        dp[0][j] = dp[0][j - 1] + grid[0][j]
    for i in range(1, n):
        for j in range(1, m):
            dp[i][j] = grid[i][j] + min(dp[i - 1][j], dp[i][j - 1])
    return dp[n - 1][m - 1]


if __name__ == "__main__":
    print("knap:", knapsack([2, 3, 4, 5], [3, 4, 5, 6], 5))
    print("lis:", lis([10, 9, 2, 5, 3, 7, 101, 18]))
    print("lcs:", lcs("ABCBDAB", "BDCABA"), lcs_string("ABCBDAB", "BDCABA"))
    print("coins:", coin_change([1, 2, 5], 11))
    print("stairs:", climb_stairs(5))
    print("kadane:", max_subarray([-2, 1, -3, 4, -1, 2, 1, -5, 4]))