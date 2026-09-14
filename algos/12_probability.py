# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 12 · Теория вероятностей (14 алгоритмов)
Часть 1 — простые: классическая вероятность, сложение/умножение, Байес.
Часть 2 — сложные: распределения (биномиальное, Пуассона, нормальное),
наиб. правдоподобие, марковские цепи, Монте-Карло, ожидание, дисперсия.
"""

import math, random
from collections import Counter


# ===================== ЧАСТЬ 1 · ПРОСТЫЕ =====================

def classical_probability(favorable, total):
    """Классическая вероятность: P = благоприятные / все."""
    if total <= 0:
        return 0.0
    return favorable / total


def prob_not(p):
    """Вероятность противоположного события."""
    return 1 - p


def prob_union(p_a, p_b, p_intersect=0.0):
    """Вероятность объединения: P(A∪B)."""
    return p_a + p_b - p_intersect


def prob_intersect_independent(p_a, p_b):
    """Пересечение независимых событий."""
    return p_a * p_b


def prob_conditional(p_a_and_b, p_b):
    """Условная вероятность P(A|B)."""
    if p_b == 0:
        return 0.0
    return p_a_and_b / p_b


def bayes(p_a, p_b_given_a, p_b_given_not_a):
    """Теорема Байеса: P(A|B) = P(A)P(B|A) / (P(A)P(B|A) + P(¬A)P(B|¬A))."""
    p_not_a = 1 - p_a
    denom = p_a * p_b_given_a + p_not_a * p_b_given_not_a
    if denom == 0:
        return 0.0
    return p_a * p_b_given_a / denom


def prob_at_least_one(p_each, n):
    """Вероятность хотя бы одного события из n независимых (одинаковая p)."""
    return 1 - (1 - p_each) ** n


def expected_value(values, probs=None):
    """Математическое ожидание."""
    if probs is None:
        return sum(values) / len(values)
    return sum(v * p for v, p in zip(values, probs))


def bernoulli_trial(p):
    """Один бросок Бернулли (1 с вероятностью p)."""
    return 1 if random.random() < p else 0


# ===================== ЧАСТЬ 2 · СЛОЖНЫЕ =====================

def binomial_pmf(n, k, p):
    """Биномиальное распределение: C(n,k) p^k (1-p)^(n-k)."""
    def comb(nn, kk):
        r = 1
        kk = min(kk, nn - kk)
        for i in range(1, kk + 1):
            r = r * (nn - kk + i) // i
        return r

    return comb(n, k) * (p ** k) * ((1 - p) ** (n - k))


def poisson_pmf(k, lam):
    """Распределение Пуассона: P(X=k) = λ^k e^-λ / k!."""
    return math.exp(-lam) * (lam ** k) / math.factorial(k)


def normal_pdf(x, mu=0.0, sigma=1.0):
    """Плотность нормального распределения."""
    return (1 / (sigma * math.sqrt(2 * math.pi))) * math.exp(-((x - mu) ** 2) / (2 * sigma * sigma))


def normal_cdf(x, mu=0.0, sigma=1.0, steps=2000):
    """Приближённая функция распределения (численное интегрирование трапеций)."""
    lo = mu - 8 * sigma
    z = (x - lo) / (2 * 8 * sigma)
    n = steps
    h = (x - lo) / n
    s = 0.0
    for i in range(n):
        x1 = lo + i * h
        x2 = lo + (i + 1) * h
        s += (normal_pdf(x1, mu, sigma) + normal_pdf(x2, mu, sigma)) * h / 2
    return max(0.0, min(1.0, s))


def zscore_probability_piecewise(z, mu=0.0, sigma=1.0):
    """P(X <= x) для нормального через CDF."""
    x = mu + z * sigma
    return normal_cdf(x, mu, sigma)


def mle_normal(data):
    """Оценка максимального правдоподобия для нормального распределения."""
    n = len(data)
    mu = sum(data) / n
    var = sum((x - mu) ** 2 for x in data) / n
    return mu, math.sqrt(var)


def markov_predict(transitions, start, steps):
    """
    Марковская цепь: распределение вероятностей после `steps` шагов.
    transitions: dict {state: {next_state: prob}}.
    """
    dist = {start: 1.0}
    for _ in range(steps):
        new = {}
        for s, p in dist.items():
            if s not in transitions:
                new[s] = new.get(s, 0) + p
                continue
            for ns, np_ in transitions[s].items():
                new[ns] = new.get(ns, 0) + p * np_
        dist = new
    return dist


def monte_carlo_pi(samples=10000):
    """Число Пи методом Монте-Карло."""
    inside = 0
    for _ in range(samples):
        x, y = random.random(), random.random()
        if x * x + y * y <= 1:
            inside += 1
    return 4 * inside / samples


def monte_carlo_integrate(f, a, b, samples=10000):
    """Определённый интеграл методом Монте-Карло."""
    total = 0.0
    for _ in range(samples):
        x = random.uniform(a, b)
        total += f(x)
    return (b - a) * total / samples


def variance_prob(values, probs=None):
    """Дисперсия распределения."""
    mu = expected_value(values, probs)
    if probs is None:
        return sum((v - mu) ** 2 for v in values) / len(values)
    return sum(p * (v - mu) ** 2 for v, p in zip(values, probs))


def law_of_large_numbers(p, trials=10000):
    """Проверка ЗБЧ: частота события стремится к вероятности."""
    wins = sum(bernoulli_trial(p) for _ in range(trials))
    return wins / trials


def central_limit_demo(size=30, samples=1000):
    """ЦЛТ: среднее из выборок распределено нормально.
    Возвращает (среднее средних, ст. отклонение средних)."""
    means = []
    for _ in range(samples):
        data = [random.random() for _ in range(size)]
        means.append(sum(data) / size)
    mu = sum(means) / len(means)
    s = math.sqrt(sum((m - mu) ** 2 for m in means) / len(means))
    return mu, s


def entropy(probs):
    """Энтропия Шеннона (в битах)."""
    return -sum(p * math.log2(p) for p in probs if p > 0)


def expected_with_interest(p):  # небольшой помощник — нет, заменю ниже
    pass


if __name__ == "__main__":
    print("[простые]")
    print("классич:", classical_probability(2, 6))
    print("не:", prob_not(0.3))
    print("объединение:", prob_union(0.3, 0.5, 0.1))
    print("Байес:", round(bayes(0.02, 0.98, 0.01), 4))
    print("хотя бы один:", round(prob_at_least_one(0.1, 3), 4))
    print("ожидание:", expected_value([1, 2, 3], [0.2, 0.3, 0.5]))
    print("[сложные]")
    print("бином P(5,2,0.5):", round(binomial_pmf(5, 2, 0.5), 4))
    print("Пуассон λ=2 k=3:", round(poisson_pmf(3, 2), 4))
    print("норм CDF(1.96):", round(normal_cdf(1.96), 4))
    print("MLE:", mle_normal([1, 2, 3, 4, 5]))
    print("марков:", markov_predict({"a": {"a": 0.7, "b": 0.3}, "b": {"a": 0.4, "b": 0.6}}, "a", 5))
    print("Монте-Карло π:", round(monte_carlo_pi(20000), 4))