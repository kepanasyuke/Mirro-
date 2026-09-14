# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 15 · Гильбертовы пространства и планковские единицы (14)
Часть 1 — гильбертовы пространства: скалярное произведение, норма,
ортонормировка (Грам-Шмидт), проекции, базисы, операторы, эрмитовость.
Часть 2 — планковские единицы: время, длина, масса, энергия, температура.
"""

import math

# ============ ПЛАНКОВСКИЕ ЕДИНИЦЫ ============

H_BAR = 1.054571817e-34   # ħ, Дж·с
G = 6.67430e-11           # гравитационная постоянная
C = 299792458.0           # скорость света
K_B = 1.380649e-23        # постоянная Больцмана


def planck_time():
    """Планковское время: t_P = sqrt(ħG/c⁵)."""
    return math.sqrt(H_BAR * G / C ** 5)


def planck_length():
    """Планковская длина: l_P = sqrt(ħG/c³)."""
    return math.sqrt(H_BAR * G / C ** 3)


def planck_mass():
    """Планковская масса: m_P = sqrt(ħc/G)."""
    return math.sqrt(H_BAR * C / G)


def planck_energy():
    """Планковская энергия: E_P = m_P·c²."""
    return planck_mass() * C ** 2


def planck_temperature():
    """Планковская температура: T_P = E_P / k_B."""
    return planck_energy() / K_B


def planck_charge():
    """Планковский заряд: q_P = sqrt(ħc·4πε₀) — как sqrt(ħc)."""
    import math
    return math.sqrt(H_BAR * C * 4 * math.pi * 8.854187817e-12) if False else math.sqrt(H_BAR * C)


def reduced_compton_wavelength(m):
    """Приведённая комптоновская длина волны частицы массы m."""
    return H_BAR / (m * C)


def quantum_uncertainty(dx, dp):
    """Проверка соотношения неопределённостей: Δx·Δp ≥ ħ/2."""
    return (dx * dp) >= H_BAR / 2


def de_broglie_energy_wavelength(m, v):
    """Длина волны де Бройля и энергия частицы."""
    wl = H_BAR * 2 * math.pi / (m * v)
    return wl


# ============ ГИЛЬБЕРТОВЫ ПРОСТРАНСТВА ============
# Работаем в C^n как списках комплексных чисел (a, b) или вещественных.


def inner_product(u, v):
    """Скалярное произведение: Σ u_i*·v_i. Входы — вещественные списки."""
    return sum(a * b for a, b in zip(u, v))


def complex_inner(u, v):
    """Скалярное произведение с сопряжением первой компоненты.
    u, v — списки пар (re, im)."""
    s = 0 + 0j
    for (re1, im1), (re2, im2) in zip(u, v):
        s += (re1 - im1 * 1j) * (re2 + im2 * 1j)
    return s


def vector_norm(v):
    """Евклидова норма вектора."""
    return math.sqrt(sum(x * x for x in v))


def normalize_vector(v):
    """Нормировка вектора к единице."""
    n = vector_norm(v)
    return [x / n for x in v] if n else v[:]


def gram_schmidt(vecs):
    """Ортонормировка Грам–Шмидта: список векторов → ортонормальный базис."""
    basis = []
    for v in vecs:
        w = v[:]
        for b in basis:
            coef = inner_product(v, b)  # предполагаем |b|=1
            w = [x - coef * y for x, y in zip(w, b)]
        n = vector_norm(w)
        if n > 1e-12:
            basis.append([x / n for x in w])
    return basis


def projection(v, basis):
    """Проекция вектора на подпространство с ортонормальным базисом."""
    out = [0.0] * len(v)
    for b in basis:
        coef = inner_product(v, b)
        out = [x + coef * y for x, y in zip(out, b)]
    return out


def cauchy_schwarz(u, v):
    """Неравенство Коши–Шварца: |<u,v>| ≤ ||u||·||v||."""
    return abs(inner_product(u, v)), vector_norm(u) * vector_norm(v)


def is_orthogonal(u, v):
    """Ортогональны ли векторы."""
    return abs(inner_product(u, v)) < 1e-9


def outer_product(u, v):
    """Внешнее произведение: матрица u_i·v_j."""
    return [[u[i] * v[j] for j in range(len(v))] for i in range(len(u))]


def matrix_apply(M, v):
    """Умножение матрицы на вектор."""
    return [sum(row[i] * v[i] for i in range(len(v))) for row in M]


def hermitian_conjugate(M):
    """Эрмитово сопряжение: транспонирование + комплексное сопряжение."""
    n, m = len(M), len(M[0])
    return [[M[j][i] for j in range(n)] for i in range(m)]


def is_hermitian(M):
    """Проверка эрмитовости матрицы (вещественная симметрия)."""
    n = len(M)
    for i in range(n):
        for j in range(n):
            if abs(M[i][j] - M[j][i]) > 1e-9:
                return False
    return True


def commutator(A, B):
    """Коммутатор операторов: [A,B] = AB - BA."""
    n = len(A)
    AB = [[sum(A[i][k] * B[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    BA = [[sum(B[i][k] * A[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    return [[AB[i][j] - BA[i][j] for j in range(n)] for i in range(n)]


def unitary_check(M):
    """Проверка унитарности: M†M = I."""
    n = len(M)
    Mt = [[M[j][i] for j in range(n)] for i in range(n)]  # вещественное сопряжение = транспонирование
    prod = [[sum(Mt[i][k] * M[k][j] for k in range(n)) for j in range(n)] for i in range(n)]
    for i in range(n):
        for j in range(n):
            want = 1.0 if i == j else 0.0
            if abs(prod[i][j] - want) > 1e-9:
                return False
    return True


if __name__ == "__main__":
    print("Планковское время:", planck_time(), "с")
    print("Планковская длина:", planck_length(), "м")
    print("Планковская масса:", planck_mass(), "кг")
    print("Планковская энергия:", planck_energy(), "Дж")
    print("Планковская температура:", planck_temperature(), "К")

    u = [1, 0, 0]
    v = [1, 1, 0]
    print("\nнорма v:", round(vector_norm(v), 3))
    basis = gram_schmidt([[1, 1, 0], [1, 0, 1]])
    print("ортонорм. базис:", basis)
    print("проекция v на базис:", [round(x, 3) for x in projection(v, basis)])
    print("эрмитова?", is_hermitian([[2, 1], [1, 3]]))
    print("унитарная?", unitary_check([[0, 1], [1, 0]]))