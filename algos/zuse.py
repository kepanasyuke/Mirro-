# -*- coding: utf-8 -*-
"""Конрад Цузе: релейная логика, двоичная плавающая точка, вычислительное пространство.

Три вещи, которые Цузе дал раньше других и которые нужны Мирро как «механике»:
  * схема из реле — булева логика, собранная из именованных элементов (Z1–Z3);
  * двоичное представление с плавающей точкой — как машина хранит числа;
  * «Rechnender Raum»: клеточный автомат, где пространство само считает,
    шаг за шагом, только по локальному правилу.

Один return на функцию, без побочных эффектов.
"""
import math

OPERATIONS = {
    "and": lambda values: int(all(values)),
    "or": lambda values: int(any(values)),
    "not": lambda values: int(not values[0]) if values else 0,
    "xor": lambda values: sum(int(value) for value in values) % 2,
}


def relay_circuit(plan, inputs):
    """Вычисляет схему реле: plan — список (имя, операция, [аргументы])."""
    signals = {name: int(value) for name, value in (inputs or {}).items()}
    for name, operation, arguments in plan or ():
        values = [signals.get(argument, 0) for argument in arguments or ()]
        signals[name] = OPERATIONS.get(operation, OPERATIONS["and"])(values)
    return signals


def half_adder(first, second):
    """Полусумматор из реле: (сумма, перенос)."""
    signals = relay_circuit([("sum", "xor", ["a", "b"]),
                             ("carry", "and", ["a", "b"])],
                            {"a": first, "b": second})
    return signals["sum"], signals["carry"]


def add_binary(first, second):
    """Сложение двоичных чисел, записанных строками: результат строкой."""
    total = int(str(first or "0"), 2) + int(str(second or "0"), 2)
    return bin(total)[2:]


def to_binary_float(value):
    """Двоичная плавающая точка: (знак, экспонента, биты мантиссы после точки)."""
    result = (0, 0, "0")
    if isinstance(value, (int, float)) and value == value and abs(value) != float("inf"):
        if value != 0:
            fraction, exponent = math.frexp(abs(float(value)))
            mantissa = fraction * 2 - 1.0
            bits = []
            for _ in range(24):
                mantissa *= 2
                bit = int(mantissa)
                bits.append(str(bit))
                mantissa -= bit
            result = (0 if value > 0 else 1, exponent - 1, "".join(bits))
    return result


def from_binary_float(sign, exponent, mantissa):
    """Обратный перевод: (знак, экспонента, биты) -> число."""
    fraction = 1.0
    for index, bit in enumerate(str(mantissa or "")):
        fraction += int(bit) * 2 ** (-(index + 1))
    value = fraction * (2 ** int(exponent))
    return -value if int(sign) else value


def cellular_step(cells, rule):
    """Один шаг одномерного клеточного автомата: правило 0..255, окрестность 3."""
    source = [1 if cell else 0 for cell in cells or ()]
    result = []
    for index in range(len(source)):
        left = source[index - 1] if index > 0 else 0
        middle = source[index]
        right = source[index + 1] if index + 1 < len(source) else 0
        pattern = left * 4 + middle * 2 + right
        result.append((int(rule) >> pattern) & 1)
    return result


def run_cellular(cells, rule, steps=1):
    """Несколько шагов автомата: история состояний."""
    history = [list(1 if cell else 0 for cell in cells or ())]
    current = list(history[0])
    for _ in range(max(int(steps), 0)):
        current = cellular_step(current, rule)
        history.append(current)
    return history


def cellular_density(cells):
    """Доля единиц в состоянии — грубая мера «заполненности»."""
    source = list(cells or ())
    result = sum(1 for cell in source if cell) / len(source) if source else 0.0
    return result


def parity_program(values):
    """Программа в духе Plankalkül: план вычисления без циклов, только шаги."""
    stack = []
    for value in values or ():
        stack.append(int(value) % 2)
    total = 0
    for bit in stack:
        total = (total + bit) % 2
    return total
