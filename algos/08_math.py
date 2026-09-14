# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 08 · Математика (10+ алгоритмов)
"""

import math


def gcd(a, b):
    """Наибольший общий делитель (Евклид)."""
    while b:
        a, b = b, a % b
    return abs(a)


def lcm(a, b):
    """Наименьшее общее кратное."""
    return abs(a * b) // gcd(a, b) if a and b else 0


def is_prime(n):
    if n < 2:
        return False
    if n < 4:
        return True
    if n % 2 == 0 or n % 3 == 0:
        return False
    i = 5
    while i * i <= n:
        if n % i == 0 or n % (i + 2) == 0:
            return False
        i += 6
    return True


def sieve(n):
    """Сито Эратосфена: все простые до n."""
    if n < 2:
        return []
    flags = [True] * (n + 1)
    flags[0] = flags[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            for j in range(i * i, n + 1, i):
                flags[j] = False
    return [i for i, ok in enumerate(flags) if ok]


def factorize(n):
    """Разложение на простые множители: [(множитель, степень)]."""
    f = []
    d = 2
    while d * d <= n:
        if n % d == 0:
            c = 0
            while n % d == 0:
                n //= d
                c += 1
            f.append((d, c))
        d += 1 if d == 2 else 2
        if d == 3:
            d -= 1
    if n > 1:
        f.append((n, 1))
    return f


def fib(n):
    """Число Фибоначчи (итеративно)."""
    a, b = 0, 1
    for _ in range(n):
        a, b = b, a + b
    return a


def fib_fast(n):
    """Фибоначчи матричным возведением (быстро)."""
    def mul(A, B):
        return (
            A[0] * B[0] + A[1] * B[2], A[0] * B[1] + A[1] * B[3],
            A[2] * B[0] + A[3] * B[2], A[2] * B[1] + A[3] * B[3])

    M = (1, 1, 1, 0)
    R = (1, 0, 0, 1)
    while n:
        if n & 1:
            R = mul(R, M)
        M = mul(M, M)
        n >>= 1
    return R[1]


def pow_mod(a, b, m):
    """Быстрое возведение в степень по модулю."""
    r = 1
    a %= m
    while b:
        if b & 1:
            r = r * a % m
        a = a * a % m
        b >>= 1
    return r


def modular_inverse(a, m):
    """Обратное по модулю (расширенный Евклид)."""
    if gcd(a, m) != 1:
        return None
    t, new_t = 0, 1
    r, new_r = m, a
    while new_r:
        q = r // new_r
        t, new_t = new_t, t - q * new_t
        r, new_r = new_r, r - q * new_r
    return t % m


def divisors(n):
    """Все делители числа."""
    out = []
    i = 1
    while i * i <= n:
        if n % i == 0:
            out.append(i)
            if i != n // i:
                out.append(n // i)
        i += 1
    return sorted(out)


def prime_factors_count(n):
    """Количество простых множителей (с кратностью)."""
    total, d = 0, 2
    while d * d <= n:
        while n % d == 0:
            n //= d
            total += 1
        d += 1
    if n > 1:
        total += 1
    return total


def phi(n):
    """Функция Эйлера: количество чисел < n взаимно простых с n."""
    r = n
    d = 2
    while d * d <= n:
        if n % d == 0:
            while n % d == 0:
                n //= d
            r -= r // d
        d += 1
    if n > 1:
        r -= r // n
    return r


def digits_sum(n):
    return sum(int(ch) for ch in str(abs(n)))


def is_perfect(n):
    """Совершенное ли число (сумма делителей = n)."""
    return n > 0 and sum(d for d in divisors(n) if d != n) == n


if __name__ == "__main__":
    print("gcd:", gcd(48, 36))
    print("prime:", [x for x in range(30) if is_prime(x)])
    print("sieve:", sieve(30))
    print("factorize:", factorize(84))
    print("fib10:", fib(10), fib_fast(10))
    print("pow_mod:", pow_mod(2, 10, 1000))
    print("phi(12):", phi(12))