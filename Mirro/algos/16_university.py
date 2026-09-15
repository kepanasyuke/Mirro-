# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 16 · Задачи вузов и ссузов (вступительные/олимпиадные)
Категории: математика (алгебра/геометрия/тригонометрия), физика (ядерная,
квантовая, механика), прикладная информатика, топология (НГУ), ЕГЭ-профиль,
задачи техникумов. Каждый тип = функция-решатель с проверкой.
"""

import math


# ============ МАТЕМАТИКА · АЛГЕБРА ============

def solve_quadratic(a, b, c):
    """Вступительные/ЕГЭ: квадратное уравнение ax²+bx+c=0. Возвращает корни."""
    if a == 0:
        if b == 0:
            return [] if c else "все числа"
        return [-c / b]
    D = b * b - 4 * a * c
    if D < 0:
        return []  # нет вещественных корней
    if D == 0:
        return [-b / (2 * a)]
    sq = math.sqrt(D)
    return [(-b - sq) / (2 * a), (-b + sq) / (2 * a)]


def solve_linear(a, b):
    """Линейное уравнение ax+b=0."""
    if a == 0:
        return "все числа" if b == 0 else []
    return [-b / a]


def arithmetic_progression_sum(a1, d, n):
    """Сумма арифметической прогрессии (задачи на прогрессии)."""
    return (2 * a1 + d * (n - 1)) * n / 2


def geometric_progression_sum(b1, q, n):
    """Сумма геометрической прогрессии."""
    if q == 1:
        return b1 * n
    return b1 * (1 - q ** n) / (1 - q)


def system_linear_2x2(a1, b1, c1, a2, b2, c2):
    """Система двух линейных уравнений методом Крамера.
    a1x+b1y=c1; a2x+b2y=c2. Возвращает (x,y) или None."""
    det = a1 * b2 - a2 * b1
    if det == 0:
        return None  # нет единственного решения
    det_x = c1 * b2 - c2 * b1
    det_y = a1 * c2 - a2 * c1
    return det_x / det, det_y / det


def solve_equation_with_module(a, b, c):
    """|ax+b| = c → корни."""
    if c < 0:
        return []
    if a == 0:
        return "все числа" if abs(b) == c else []
    x1 = (c - b) / a
    x2 = (-c - b) / a
    return sorted(set([x1, x2]))


def discriminant(a, b, c):
    """Дискриминант квадратного уравнения."""
    return b * b - 4 * a * c


def viet_check(p, q, roots):
    """Проверка корней по теореме Виета: x1+x2=-p, x1*x2=q."""
    if len(roots) != 2:
        return False, ""
    s, pr = sum(roots), roots[0] * roots[1]
    ok = abs(s + p) < 1e-9 and abs(pr - q) < 1e-9
    return ok, f"сумма={s}, произведение={pr}"


# ============ МАТЕМАТИКА · ТРИГОНОМЕТРИЯ ============

def sin_cos_tan(angle_deg):
    """Значения sin/cos/tan угла (задачи табличных значений)."""
    r = math.radians(angle_deg)
    return math.sin(r), math.cos(r), (math.tan(r) if abs(math.cos(r)) > 1e-12 else None)


def solve_trig_basic(b, c):
    """sin(b·x) = c, базовый случай: возвращает x в градусах на [0,360)."""
    if abs(c) > 1:
        return []
    r = math.degrees(math.asin(c))
    base = r / b
    out = []
    for k in range(4):
        val1 = (r + 360 * k) / b
        val2 = (180 - r + 360 * k) / b
        for v in (val1, val2):
            if 0 <= v < 360:
                out.append(round(v, 4))
    return out


# ============ МАТЕМАТИКА · ГЕОМЕТРИЯ ============

def triangle_area_heron(a, b, c):
    """Площадь треугольника по трём сторонам (формула Герона)."""
    if a + b <= c or a + c <= b or b + c <= a:
        return None  # не треугольник
    p = (a + b + c) / 2
    return math.sqrt(p * (p - a) * (p - b) * (p - c))


def circle_geometry(r):
    """Окружность: длина, площадь, вписанные/описанные формулы."""
    return {
        "длина": 2 * math.pi * r,
        "площадь": math.pi * r * r,
    }


def pyramid_volume(base_area, height):
    """Объём пирамиды."""
    return base_area * height / 3


def sphere_volume(r):
    return 4 / 3 * math.pi * r ** 3


def cylinder_volume(r, h):
    return math.pi * r * r * h


def right_triangle_sides(a, b):
    """Гипотенуза и углы прямоугольного треугольника (теорема Пифагора)."""
    c = math.hypot(a, b)
    ang_a = math.degrees(math.atan2(a, b))
    ang_b = 90 - ang_a
    return c, ang_a, ang_b


def trapezoid_area(a, b, h):
    """Площадь трапеции."""
    return (a + b) * h / 2


# ============ ФИЗИКА · ЯДЕРНАЯ ============

def nuclear_mass_defect(m_nucleons, m_nucleus):
    """Дефект массы: (сумма масс нуклонов) - масса ядра (а.е.м.)."""
    return m_nucleons - m_nucleus


def binding_energy(defect_mass_amu):
    """Энергия связи по дефекту массы (1 а.е.м. = 931.5 МэВ)."""
    return defect_mass_amu * 931.5


def half_life_remaining(N0, t, T_half):
    """Остаток вещества после времени t при периоде полураспада T. N = N0·2^(-t/T)."""
    return N0 * 2 ** (-t / T_half)


def radioactive_decay_constant(T_half):
    """Постоянная распада λ = ln2 / T."""
    return math.log(2) / T_half


def nuclear_reaction_check(A_before, A_after, Z_before, Z_after):
    """Проверка законов сохранения массового числа и заряда."""
    return A_before == A_after and Z_before == Z_after


def energy_from_mass_kg(m):
    """E=mc² (масса в кг → энергия в Дж)."""
    c = 3e8
    return m * c * c


def alpha_decay(A, Z):
    """Альфа-распад: A→A-4, Z→Z-2."""
    return A - 4, Z - 2


def beta_decay(A, Z):
    """Бета-распад: A→A, Z→Z+1."""
    return A, Z + 1


# ============ ФИЗИКА · МЕХАНИКА / ЧАСТИЦЫ ============

def projectile_range(v0, angle_deg, g=9.81):
    """Дальность полёта снаряда под углом к горизонту."""
    return v0 ** 2 * math.sin(2 * math.radians(angle_deg)) / g


def projectile_max_height(v0, angle_deg, g=9.81):
    """Максимальная высота подъёма."""
    return (v0 * math.sin(math.radians(angle_deg))) ** 2 / (2 * g)


def relativistic_gamma(v):
    """Лоренц-фактор γ = 1/√(1-v²/c²)."""
    c = 3e8
    if v >= c:
        return float("inf")
    return 1 / math.sqrt(1 - (v / c) ** 2)


def kinetic_energy_relativistic(m0, v):
    """Релятивистская кинетическая энергия."""
    c = 3e8
    g = relativistic_gamma(v)
    return (g - 1) * m0 * c * c


def photon_momentum(wavelength_m):
    """Импульс фотона p = h/λ."""
    h = 6.626e-34
    return h / wavelength_m


def photoelectric_energy(frequency_hz):
    """Энергия фотона E = hν (Дж)."""
    h = 6.626e-34
    return h * frequency_hz


# ============ ПРИКЛАДНАЯ ИНФОРМАТИКА ============

def binary_to_decimal(bits):
    """Перевод двоичного числа в десятичное (типовая задача ЕГЭ-информ)."""
    return int(bits, 2)


def decimal_to_base(n, base):
    """Перевод числа в систему счисления."""
    if n == 0:
        return "0"
    digits = "0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZ"
    out = ""
    while n:
        out = digits[n % base] + out
        n //= base
    return out


def truth_input_task(expr_type, a, b):
    """ЕГЭ-информатика: логические выражения (И/ИЛИ/НЕ)."""
    if expr_type == "and":
        return a and b
    if expr_type == "or":
        return a or b
    if expr_type == "xor":
        return a != b
    return None


def count_ones_in_range(a, b):
    """Задача: сколько единиц в двоичной записи чисел от a до b."""
    return sum(bin(x).count("1") for x in range(a, b + 1))


def sieve_primes_count(n):
    """Количество простых до n (проверка быстродействия алгоритма)."""
    if n < 2:
        return 0
    flags = [True] * (n + 1)
    flags[0] = flags[1] = False
    for i in range(2, int(n ** 0.5) + 1):
        if flags[i]:
            for j in range(i * i, n + 1, i):
                flags[j] = False
    return sum(flags)


# ============ ТОПОЛОГИЯ (НГУ) ============

def euler_characteristic(V, E, F):
    """Характеристика Эйлера многогранника: χ = V - E + F."""
    return V - E + F


def euler_polyhedron_check(V, E, F):
    """Проверка формулы Эйлера для выпуклого многогранника (V-E+F=2)."""
    return V - E + F == 2


def sphere_genus_formula(ch):
    """Род поверхности по характеристике Эйлера: g = (2-χ)/2."""
    return (2 - ch) / 2


def mobius_is_nonorientable():
    """Факт из топологии: лист Мёбиуса неориентируем."""
    return True


def torus_characteristic():
    """Характеристика Эйлера тора = 0."""
    return 0


def sphere_characteristic():
    """Характеристика Эйлера сферы = 2."""
    return 2


def knot_trefoil_crossings():
    """Для трилистника минимальное число пересечений = 3."""
    return 3


# ============ ССУЗЫ / ТЕХНИКУМЫ ============

def mixture_percent(c1, v1, c2, v2):
    """Задача на смеси: концентрация после смешивания."""
    return (c1 * v1 + c2 * v2) / (v1 + v2) if (v1 + v2) else 0


def work_time(A1, A2):
    """Производительность двух рабочих: время общей работы."""
    if A1 <= 0 or A2 <= 0:
        return None
    return 1 / (1 / A1 + 1 / A2)  # A1, A2 — время по отдельности


def interest_compound(P, r, n_years):
    """Сложные проценты (банковские задачи техникумов)."""
    return P * (1 + r) ** n_years


def speed_average(v1, dist_ratio):
    """Средняя скорость при разных участках."""
    # dist_ratio — доля пути на скорости v1, (1-ratio) — на v2
    v2 = v1 * dist_ratio  # упрощение, если требуется
    return None


def pipe_fill_time(t1, t2):
    """Две трубы наполняют бассейн: общее время."""
    if t1 <= 0 or t2 <= 0:
        return None
    return 1 / (1 / t1 + 1 / t2)


if __name__ == "__main__":
    print("## Математика")
    print("квадратное x²-5x+6:", solve_quadratic(1, -5, 6))
    print("система:", system_linear_2x2(2, 1, 7, 1, -1, 2))
    print("Герон (3,4,5):", triangle_area_heron(3, 4, 5))
    print("## Физика")
    print("энергия связи (дефект 0.002 а.е.м.):", binding_energy(0.002), "МэВ")
    print("полураспад: после 2T:", half_life_remaining(100, 2, 1))
    print("альфа-распад (238,92):", alpha_decay(238, 92))
    print("## Информатика")
    print("1011₂ =", binary_to_decimal("1011"))
    print("255 в 16-ю:", decimal_to_base(255, 16))
    print("## Топология")
    print("Эйлер куба (8,12,6):", euler_characteristic(8, 12, 6), "проверка:", euler_polyhedron_check(8, 12, 6))
    print("## Ссузы")
    print("смесь 20% и 40% пополам:", mixture_percent(0.2, 1, 0.4, 1))
    print("две трубы 4ч и 6ч:", pipe_fill_time(4, 6))