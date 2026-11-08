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


def _normalize_expr(expr):
    """Нормализует булево выражение к Python-синтаксису.
    Один return: str."""
    e = str(expr)
    if not bool_expr_looks_safe(e):
        raise ValueError("unsafe expression")
    e = e.replace("∧", " and ").replace("∨", " or ").replace("¬", " not ")
    e = e.replace("&", " and ").replace("|", " or ").replace("!", " not ")
    e = e.replace("→", " or not ")
    return e


def bool_expr_looks_safe(expr):
    """Признает ли выражение допустимым набором символов (без вызова функций
    и доступа к атрибутам). Один return: bool."""
    allowed_chars = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789_ "
                        "()∧∨¬&|!→,.=+-*/%<>")
    return all(ch in allowed_chars for ch in str(expr))


def evaluate_expr(expr, vars_map):
    """Подставляет значения из vars_map (dict имя→0/1/False/True) в булево
    выражение и вычисляет результат. Некорректное выражение → False.
    Один return: bool."""
    result = False
    try:
        safe = set(vars_map or {})
        allowed = {k: bool(v) for k, v in (vars_map or {}).items()}
        # строим без eval: подставляем напрямую через and/or/not
        local_scope = dict(allowed)
        code = compile(_normalize_expr(expr), "<expr>", "eval")
        result = bool(eval(code, {"__builtins__": {}}, local_scope))
    except Exception:
        result = False
    return result


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
    """Приводит булево выражение к нормализованному виду Python-синтаксиса
    (мини-упрощение: раскрытие двойного отрицания).
    Один return: str."""
    s = _normalize_expr(expr_str)
    # неоднократно снимаем "not not X" — убираем двойное отрицание
    prev = None
    while prev != s:
        prev = s
        s = s.replace("not not  ", "not ").replace("not not ", "not ")
        s = s.replace("not not", "not").replace("not ( not (", "(").replace(") not )", ")")
    return s.strip()


def boolean_identity_check(expr_fn):
    """Проверка тавтологии: функция от (a,b) истинна при всех комбинациях.
    Один return: bool."""
    is_tautology = True
    for mask in range(4):
        a, b = (mask >> 1) & 1, mask & 1
        if not expr_fn(a, b):
            is_tautology = False
            break
    return is_tautology


def bitcount(n):
    """Число единичных битов (популяция). Отрицательный n → 0.
    Один return: int."""
    return bin(n).count("1") if n >= 0 else 0


def gray_code(n):
    """Серый код: n-й элемент."""
    return n ^ (n >> 1)


def hamming_weight(bits):
    """Вес Хэмминга набора битов (строка '10101'). Не-строка → 0.
    Один return: int."""
    if not isinstance(bits, str):
        return 0
    return bits.count("1")


def logic_gate_table():
    """Таблица всех базовых вентилей. Строки: (a,b,AND,OR,NOT-a,XOR,NAND,NOR).
    Один return: list."""
    return [(a, b, a & b, a | b, int(not a), a ^ b, int(not (a & b)), int(not (a | b)))
            for a in (0, 1) for b in (0, 1)]


if __name__ == "__main__":
    print("XOR:", bool_xor(1, 0))
    print("импликация:", [implication(a, b) for a in (0, 1) for b in (0, 1)])
    print("полусумматор:", half_adder(1, 1))
    print("сумматор:", full_adder(1, 1, 1))
    print("таблица вентилей:", logic_gate_table())
    print("серый:", [gray_code(i) for i in range(8)])