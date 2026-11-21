# -*- coding: utf-8 -*-
"""Нейрон Маккаллока–Питтса: пороговая логика как основа нейросетей.

Нейрон считается так: единица, если взвешенная сумма входов не ниже порога,
иначе ноль. На этом строится вся булева логика (И, ИЛИ, НЕ), а двумя слоями
получается исключающее ИЛИ — тот самый разрыв, из которого выросли перцептрон
и многослойные сети.

Один return на функцию, без побочных эффектов.
"""


def neuron(weights, inputs, threshold=1.0):
    """Выход порогового нейрона: 1 при сумме не ниже порога, иначе 0."""
    total = sum(weight * value for weight, value in zip(weights, inputs))
    return 1 if total >= threshold else 0


def constant_weights(size, value=1.0):
    """Ровные веса заданной длины."""
    return [value] * max(int(size), 0)


def and_gate(first, second):
    """Конъюнкция: оба входа обязательны (порог 2)."""
    return neuron([1, 1], [first, second], 2)


def or_gate(first, second):
    """Дизъюнкция: достаточно одного входа (порог 1)."""
    return neuron([1, 1], [first, second], 1)


def not_gate(value):
    """Отрицание: тормозящий вес и порог 0."""
    return neuron([-1], [value], 0)


def nand_gate(first, second):
    """Штрих Шеффера: отрицание конъюнкции."""
    return neuron([-1, -1], [first, second], -1)


def xor_gate(first, second):
    """Исключающее ИЛИ двумя слоями: по скрытому нейрону на каждый случай."""
    left = neuron([1, -1], [first, second], 1)
    right = neuron([-1, 1], [first, second], 1)
    return neuron([1, 1], [left, right], 1)


def truth_table(gate, rows=None):
    """Таблица истинности для функции от двух аргументов."""
    cases = rows if rows is not None else ((0, 0), (0, 1), (1, 0), (1, 1))
    result = [((first, second), gate(first, second)) for first, second in cases]
    return result


def evaluate(weights, threshold, rows):
    """Выходы одного нейрона на наборе входных строк."""
    result = [neuron(weights, list(values), threshold) for values in rows or ()]
    return result


def is_linearly_separable(rows):
    """Проверка перебором: можно ли разделить классы одной прямой.

    Нужна, чтобы показать: XOR одним нейроном не решается, а AND/OR решаются.
    """
    points = [(first, second, label) for (first, second), label in rows or ()]
    separators = [(a, b, c) for a in range(-2, 3) for b in range(-2, 3) for c in range(-4, 5)]
    result = any(all((a * x + b * y >= c) == bool(label) for x, y, label in points)
                 for a, b, c in separators)
    return result
