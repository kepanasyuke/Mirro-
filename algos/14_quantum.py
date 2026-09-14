# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 14 · Квантовая логика и трёхзначная логика (12 алгоритмов)
Кубиты: суперпозиция, амплитуды, измерения, гейты (Hadamard, X, Z).
Трёхзначная логика: Лукасевича и Клини (истина/ложь/неизвестно).
Одночастичные квантовые состояния и их вероятности.
"""

import math, random
from fractions import Fraction


# ============ КВАНТОВЫЕ КУБИТЫ ============

class Qubit:
    """Кубит: амплитуды alpha|0> + beta|1> (α²+β²=1)."""

    def __init__(self, alpha=1.0, beta=0.0):
        norm = math.sqrt(alpha * alpha + beta * beta) or 1
        self.alpha = alpha / norm
        self.beta = beta / norm

    def measure(self):
        """Измерение: возвращает 0 или 1 по вероятностям."""
        p1 = self.beta * self.beta
        return 1 if random.random() < p1 else 0

    def prob(self):
        return (self.alpha * self.alpha, self.beta * self.beta)

    def __repr__(self):
        return f"Qubit(α={self.alpha:.3f}, β={self.beta:.3f})"


def qubit_hadamard(q):
    """Гейт Адамара H: |0>→(|0>+|1>)/√2, |1>→(|0>-|1>)/√2."""
    s = 1 / math.sqrt(2)
    a = s * (q.alpha + q.beta)
    b = s * (q.alpha - q.beta)
    return Qubit(a, b)


def qubit_pauli_x(q):
    """Гейт X (NOT): меняет амплитуды местами."""
    return Qubit(q.beta, q.alpha)


def qubit_pauli_z(q):
    """Гейт Z: фаза β меняет знак."""
    return Qubit(q.alpha, -q.beta)


def qubit_phase(q, theta):
    """Фазовый гейт: β → β·e^{iθ} (вещественная аппроксимация)."""
    return Qubit(q.alpha, q.beta * math.cos(theta))


def bloch_angles(q):
    """Углы Блоха θ, φ кубита."""
    theta = 2 * math.acos(max(-1, min(1, q.alpha)))
    phi = math.atan2(q.beta, q.alpha) if abs(q.alpha) > 1e-9 else math.pi / 2
    return theta, phi


def entangled_pair():
    """Запутанная пара Белла: (|00>+|11>)/√2 (как два кубита)."""
    s = 1 / math.sqrt(2)
    return Qubit(s, 0), Qubit(0, s)


def bell_measure(qa, qb):
    """Совместное измерение Белла (упрощённо, с учётом корреляции)."""
    r1, r2 = qa.measure(), qb.measure()
    return r1, r1 ^ r2  # запутанность: при |00>,|11> биты равны


# ============ ТРЁХЗНАЧНАЯ ЛОГИКА ============
# значения: 1 = истина, 0 = ложь, 0.5 = неизвестно

def three_valued_and(a, b):
    """Конъюнкция (Лукасевич): min(a,b)."""
    return min(a, b)


def three_valued_or(a, b):
    """Дизъюнкция: max(a,b)."""
    return max(a, b)


def three_valued_not(a):
    """Отрицание: 1-a."""
    return 1 - a


def three_valued_implication(a, b):
    """Импликация Лукасевича: min(1, 1-a+b)."""
    return min(1, 1 - a + b)


def three_valued_kleene_and(a, b):
    """Сильная конъюнкция Клини: учитывает неизвестность."""
    if a == 0 or b == 0:
        return 0
    if a == 1 and b == 1:
        return 1
    return 0.5  # неизвестно


def three_valued_kleene_or(a, b):
    if a == 1 or b == 1:
        return 1
    if a == 0 and b == 0:
        return 0
    return 0.5


def three_valued_table():
    """Таблица истинности трёхзначной логики (AND/OR/NOT)."""
    out = []
    for a in (1, 0.5, 0):
        for b in (1, 0.5, 0):
            out.append((a, b, three_valued_and(a, b), three_valued_or(a, b),
                        three_valued_not(a)))
    return out


def three_valued_equivalence(a, b):
    """Эквивалентность Лукасевича: 1 - |a - b|."""
    return 1 - abs(a - b)


def truth_degree(model_fn):
    """Степень истинности формулы по трёхзначной оценке (0..1)."""
    return model_fn()


def quantum_tsp_states():
    """
    «Трёхчастные состояния» — упрощённая модель 3-частичной
    суперпозиции (например, ГХЦ-состояние |000>+|111>).
    Возвращает список амплитуд по классическим конфигурациям.
    """
    s = 1 / math.sqrt(2)
    return {"000": (s, 0 + 0j), "111": (s, 0 + 0j)}


def quantum_probability(amplitude):
    """Вероятность из амплитуды (борновское правило)."""
    real, imag = amplitude if isinstance(amplitude, tuple) else (amplitude, 0)
    return real * real + imag * imag


def superposition_measure(counts):
    """Симуляция измерения суперпозиции: частоты исходов."""
    from collections import Counter
    states = ["|0>", "|1>"]
    probs = [0.5, 0.5]
    c = Counter(random.choices(states, weights=probs, k=counts))
    return dict(c)


if __name__ == "__main__":
    q = Qubit(1, 0)
    h = qubit_hadamard(q)
    print("кубит после H:", h, "вероятности:", h.prob())
    print("измерен:", h.measure())
    print("Блох:", bloch_angles(q))
    qa, qb = entangled_pair()
    print("Белл-пара:", qa, qb, "совместное измерение:", bell_measure(qa, qb))
    print("3-значное AND(1, 0.5):", three_valued_and(1, 0.5))
    print("3-значная импликация(0.5, 0):", three_valued_implication(0.5, 0))
    print("ГХЦ:", quantum_tsp_states())