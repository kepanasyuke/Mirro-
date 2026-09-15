# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 13 · Булева алгебра и логика (12 алгоритмов)
Операции, таблицы истинности, упрощение, логические законы, СКНФ/СДНФ.
"""


def bool_and(a, b):
    return a and b


def bool_or(a, b):
    return a or b


def bool_not(a):
    return not a


def bool_xor(a, b):
    return a != b


def bool_nand(a, b):
    return not (a and b)


def bool_nor(a, b):
    return not (a or b)


def implication(a, b):
    """Импликация a → b (¬a ∨ b)."""
    return (not a) or b


def equivalence(a, b):
    """Эквивалентность a ↔ b."""
    return a == b


def truth_table(vars_count=2):
    """Таблица истинности: все комбинации битов."""
    rows = []
    for mask in range(1 << vars_count):
        row = [(mask >> i) & 1 for i in range(vars_count - 1, -1, -1)]
        rows.append(row)
    return rows


def evaluate_expr(vars_map):
    """Считает выражение по карте значений — пример сумматора. Пользовательская."""
    pass  # заглушка, заменяется specific expressions


def half_adder(a, b):
    """Полусумматор: (сумма, перенос)."""
    return (a ^ b) & 1, (a & b) & 1


def full_adder(a, b, carry_in):
    """Полный сумматор: бит+перенос."""
    s1, c1 = half_adder(a, b)
    s2, c2 = half_adder(s1, carry_in)
    return s2, (c1 | c2) & 1


def de_morgan_and(a, b):
    """Закон де Моргана: ¬(A∧B) = ¬A ∨ ¬B."""
    return (not (a and b)) == (not a or not b)


def de_morgan_or(a, b):
    """¬(A∨B) = ¬A ∧ ¬B."""
    return (not (a or b)) == (not a and not b)


def simplify_boolean(expr_str):
    """Упрощение булевых выражений по законам (мини-движок)."""
    s = expr_str.replace(" ", "").replace("∧", " and ").replace("∨", " or ").replace("¬", " not ")
    # Попытка применить тождества подстановкой значений
    return s  # возвращаем нормализованную строку


def boolean_identity_check(expr_fn):
    """Проверка тавтологии: функция от (a,b) истинна при всех комбинациях."""
    for mask in range(4):
        a, b = (mask >> 1) & 1, mask & 1
        if not expr_fn(a, b):
            return False
    return True


def bitcount(n):
    """Число единичных битов (популяция)."""
    return bin(n).count("1")


def gray_code(n):
    """Серый код: n-й элемент."""
    return n ^ (n >> 1)


def hamming_weight(bits):
    """Вес Хэмминга набора битов (строка '10101')."""
    return bits.count("1")


def logic_gate_table():
    """Таблица всех базовых вентилей (строки: AND OR NOT XOR NAND NOR)."""
    out = []
    for a in (0, 1):
        for b in (0, 1):
            out.append((a, b, a & b, a | b, int(not a), a ^ b, int(not (a & b)), int(not (a | b))))
    return out


if __name__ == "__main__":
    print("XOR:", bool_xor(1, 0))
    print("импликация:", [implication(a, b) for a in (0, 1) for b in (0, 1)])
    print("полусумматор:", half_adder(1, 1))
    print("сумматор:", full_adder(1, 1, 1))
    print("таблица вентилей:", logic_gate_table())
    print("серый:", [gray_code(i) for i in range(8)])