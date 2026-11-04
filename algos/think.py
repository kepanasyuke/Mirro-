# -*- coding: utf-8 -*-
"""
Mirro Think — мыслительный движок
=================================
Зоопарк алгоритмов оживает: вопрос → распознавание типа → подбор алгоритма
→ запуск → ответ с результатом и объяснением. Это и есть «думать».

Связывает текстовые вопросы пользователя с функциями из algos/*.py:
- вычисления (сколько будет 2+2, 15% от 200)
- уравнения (квадратные, линейные)
- прогрессии, комбинаторика, вероятность
- физика (энергия связи, полураспад), графы, строки
"""

import importlib.util, re, math, json, time
from pathlib import Path

ALGO_DIR = Path(r"D:\Mirro\algos")

_cache = {}


def load_module(name):
    """Загружает модуль алгоса по имени файла (с кэшем). Один return: module|None."""
    mod = _cache.get(name)
    if mod is None:
        path = ALGO_DIR / f"{name}.py"
        if path.exists():
            try:
                spec = importlib.util.spec_from_file_location(name, path)
                candidate = importlib.util.module_from_spec(spec)
                spec.loader.exec_module(candidate)
                _cache[name] = candidate
                mod = candidate
            except Exception:
                mod = None
    return mod


def all_loaded():
    """Число загруженных модулей."""
    return len(_cache)


def list_available():
    """Список всех доступных функции во всех модулях (полный реестр)."""
    registry = []
    for f in sorted(ALGO_DIR.glob("*.py")):
        name = f.stem
        if name.startswith("_"):
            continue
        mod = load_module(name)
        if mod:
            funcs = [x for x in dir(mod) if not x.startswith("_") and callable(getattr(mod, x))]
            registry.append({"module": name, "functions": funcs})
    return registry


def _numbers(text):
    """Все числа из текста (float)."""
    return [float(x.replace(",", ".")) for x in re.findall(r"-?\d+[.,]?\d*", text)]


def _int_numbers(text):
    return [int(x) for x in _numbers(text)]


# ================== РАСПОЗНАВАНИЕ ВОПРОСА ==================

def classify(query):
    """
    Возвращает (категория, модуль, функция, аргументы, объяснение) или None.
    Распознаёт типовые задачи вузов/ссузов/олимпиад.
    """
    q = query.lower().strip()

    # --- простые вычисления (не трогаем уравнения с x) ---
    has_math_words = "умнож" in q or "плюс" in q or "минус" in q or "дели" in q or "раздел" in q
    if "x" not in q and ("сколько будет" in q or re.search(r"\d+\s*[+\-*/×]\s*\d+", q) or has_math_words):
        nums = _numbers(q)
        if ("*" in q.replace("×", "*") or "умнож" in q or "умножить" in q) and len(nums) >= 2:
            if "×" in q or "*" in q or "умнож" in q or "умножить" in q:
                return ("математика", "01_stats", "product_of", None,
                        f"{nums[0]:g} × {nums[1]:g} = {nums[0]*nums[1]:.6g}")
            return ("математика", "01_stats", "product_of", None, str(nums[0] * nums[1]))
        if ("+" in q or "плюс" in q) and len(nums) >= 2:
            return ("математика", "01_stats", "sum_of", None,
                    f"{nums[0]:g} + {nums[1]:g} = {nums[0]+nums[1]:.6g}")
        if ("-" in q or "минус" in q) and len(nums) >= 2:
            return ("математика", "01_stats", "diff_of", None,
                    f"{nums[0]:g} − {nums[1]:g} = {nums[0]-nums[1]:.6g}")
        if ("/" in q or "дели" in q or "раздел" in q) and len(nums) >= 2:
            if nums[1] != 0:
                return ("математика", "01_stats", "div_of", None,
                        f"{nums[0]:g} / {nums[1]:g} = {nums[0]/nums[1]:.6g}")

    # --- проценты ---
    # Поддерживаем и символ %, и словесную форму «15 процентов от 200».
    m = re.search(
        r"(\d+[.,]?\d*)\s*(?:%|процент(?:ов|а|у|ом)?)\s*(от|из|от числа|числа)?\s*(\d+[.,]?\d*)?",
        q)
    if m:
        pct = float(m.group(1).replace(",", "."))
        if m.group(3):
            base = float(m.group(3).replace(",", "."))
            return ("математика", "16_university", "percent_of", (pct, base),
                    f"{pct:g}% от {base:g} = {pct/100*base:.6g}")

    # --- квадратное уравнение: парсим ax²+bx+c=0 с учётом неявной 1 и знаков ---
    is_quad = ("квадратн" in q or "x²" in q or "x^2" in q or "x**2" in q) and "=" in q
    if is_quad:
        # нормализуем: x² -> 1x^2, -5x -> -5x, +6 -> +6
        expr = q.replace("×", "").replace(" ", "")
        m = re.search(r"([+-]?\d*\.?\d*)?x(?:\^2|\u00b2)?\s*([+-]\d*\.?\d*)?x\s*([+-]\d+\.?\d*)?\s*=\s*0", expr)
        if m:
            a_s, b_s, c_s = m.group(1), m.group(2), m.group(3)
            a = 1.0 if a_s in (None, "", "+", "-") else (float(a_s) if a_s not in ("+", "-") else 1.0)
            if a_s in ("+", "-"):
                a = 1.0
            if a_s:
                a = 1.0 if a_s in ("+", "-") else float(a_s)
            b = 0.0
            if b_s:
                b = 1.0 if b_s in ("+", "-") else float(b_s)
            c = float(c_s) if c_s else 0.0
            roots = _solve_quadratic(a, b, c)
            return ("математика", "16_university", "solve_quadratic", (a, b, c),
                    f"{a:g}x²{'+' if b>=0 else ''}{b:g}x{'+' if c>=0 else ''}{c:g}=0 → корни: {roots}")

    # --- линейное: ax + b = 0 ---
    if ("реши" in q or "найди x" in q or "уравнен" in q) and "x" in q:
        nums = _numbers(q)
        m = re.search(r"([+-]?\d*\.?\d*)x\s*([+-]\d*\.?\d*)?\s*=\s*(-?\d+\.?\d*)", q.replace(" ", "").replace("=", " = "))
        if m and not is_quad:
            a = 1.0 if m.group(1) in (None, "", "+", "-") else float(m.group(1))
            b_lin = float(m.group(2)) if m.group(2) else 0.0
            rhs = float(m.group(3)) if m.group(3) else 0.0
            # ax + b = rhs -> ax = rhs - b
            root = (rhs - b_lin) / a if a else None
            return ("математика", "16_university", "solve_linear", (a, rhs - b_lin),
                    f"x = {(rhs - b_lin) / a:.6g}" if a else "нет решения")

    # --- комбинаторика ---
    m_c = re.match(r"c\s*\(?(\d+)\s*[;,]\s*(\d+)\)?", q)
    if m_c:
        n, k = int(m_c.group(1)), int(m_c.group(2))
        return ("комбинаторика", "10_combinatorics", "combinations_count", (n, k),
                f"C({n},{k}) = {_comb(n,k)}")
    if ("сочет" in q or "c(" in q.lower()) and len(_int_numbers(q)) >= 2:
        nums = _int_numbers(q)
        return ("комбинаторика", "10_combinatorics", "combinations_count", (nums[0], nums[1]),
                f"C({nums[0]},{nums[1]}) = {_comb(nums[0],nums[1])}")
    if ("перестанов" in q or "факториал" in q) and _int_numbers(q):
        n = _int_numbers(q)[0]
        return ("комбинаторика", "10_combinatorics", "factorial", (n,), f"{n}! = {_fact(n)}")

    # --- вероятность ---
    if "вероятн" in q and len(_numbers(q)) >= 2:
        nums = _numbers(q)[:2]
        return ("вероятность", "12_probability", "classical_probability", (nums[0], nums[1]),
                f"P = {nums[0]:g}/{nums[1]:g} = {nums[0]/nums[1]:.4f}")

    # --- физика: энергия связи / полураспад ---
    if "энерги" in q and "связ" in q and _numbers(q):
        d = _numbers(q)[0]
        return ("физика", "16_university", "binding_energy", (d,),
                f"E = {d:g}·931.5 МэВ = {d*931.5:.3g} МэВ")
    if "полураспад" in q and len(_numbers(q)) >= 3:
        n0, t, th = _numbers(q)[:3]
        return ("физика", "16_university", "half_life_remaining", (n0, t, th),
                f"N = {n0:g}·2^(-{t:g}/{th:g}) = {n0*2**(-t/th):.4g}")

    # --- геометрия ---
    if "пифагор" in q and len(_numbers(q)) >= 2:
        a, b = _numbers(q)[:2]
        return ("геометрия", "16_university", "right_triangle_sides", (a, b),
                f"гипотенуза = {math.hypot(a,b):.4g}")
    if ("герон" in q or "площадь треугольн" in q) and len(_numbers(q)) >= 3:
        a, b, c = _numbers(q)[:3]
        s = (a+b+c)/2
        area = math.sqrt(max(0, s*(s-a)*(s-b)*(s-c)))
        return ("геометрия", "16_university", "triangle_area_heron", (a, b, c),
                f"площадь = {area:.4g}")

    # --- НОД/НОК ---
    if "нод" in q or "наибольший общий" in q or "gcd" in q:
        nums = _int_numbers(q)
        if len(nums) >= 2:
            a, b = nums[:2]
            g = _gcd(a, b)
            return ("математика", "08_math", "gcd", (a, b), f"НОД({a},{b}) = {g}")
    if "нок" in q or "наименьшее общее" in q or "lcm" in q:
        nums = _int_numbers(q)
        if len(nums) >= 2:
            a, b = nums[:2]
            l = _lcm(a, b)
            return ("математика", "08_math", "lcm", (a, b), f"НОК({a},{b}) = {l}")

    # --- простое число ---
    if "прост" in q and _int_numbers(q):
        n = _int_numbers(q)[0]
        return ("математика", "08_math", "is_prime", (n,), f"{n} простое? {_isprime(n)}")

    # --- строки ---
    if "палиндром" in q or "палиндром" in q:
        return ("строки", "06_strings", "is_palindrome", (q,), None)

    # --- сортировка ---
    if "сортир" in q and _int_numbers(q):
        arr = _int_numbers(q)
        return ("алгоритмы", "05_sorts", "quick_sort", (arr,), f"сортировка: {sorted(arr)}")

    return None


# --- хелперы без импорта модулей (для мгновенных объяснений) ---
def _comb(n, k):
    k = min(k, n - k)
    r = 1
    for i in range(1, k + 1):
        r = r * (n - k + i) // i
    return r


def _fact(n):
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


def _gcd(a, b):
    a, b = abs(a), abs(b)
    while b:
        a, b = b, a % b
    return a


def _lcm(a, b):
    return abs(a * b) // _gcd(a, b) if a and b else 0


def _isprime(n):
    """Простое ли число. Один return: bool."""
    prime = True
    if n < 2:
        prime = False
    elif n < 4:
        prime = True
    elif n % 2 == 0 or n % 3 == 0:
        prime = False
    else:
        i = 5
        while i * i <= n:
            if n % i == 0 or n % (i + 2) == 0:
                prime = False
                break
            i += 6
    return prime


def _solve_linear_root(a, b):
    """Корень линейного ax+b=0 (a!=0). Один return: float."""
    return (0 - b) / a


def _solve_quadratic(a, b, c):
    """Находит корни квадратного уравнения. Один return: list корней."""
    import math as _m
    roots = []
    if a == 0:
        if b != 0:
            roots = [_solve_linear_root(b, c)]
    else:
        D = b * b - 4 * a * c
        if D < 0:
            roots = []
        elif D == 0:
            roots = [-b / (2 * a)]
        else:
            sq = _m.sqrt(D)
            roots = [(-b - sq) / (2 * a), (-b + sq) / (2 * a)]
    return roots


def _percent_of(pct, base):
    return pct / 100 * base


def _solve_linear(a, b):
    """ax + b = 0. Один return: list."""
    roots = []
    if a != 0:
        roots = [_solve_linear_root(a, b)]
    return roots


# ================== ЯДРО «ПОДУМАТЬ» ==================

def think(query):
    """
    Главный метод: дать ответ на вопрос, используя алгоритмы.
    Возвращает dict: {answer, explanation, module, function, category, confidence}
    """
    t0 = time.time()
    result = classify(query)

    category = None
    module = None
    func_name = None
    args = None
    explanation = None
    answer = None
    confidence = 0.0
    if result:
        category, module, func_name, args, explanation = result
        # загружаем модуль и вызываем функцию
        mod = load_module(module)
        if mod and hasattr(mod, func_name):
            fn = getattr(mod, func_name)
            try:
                if args is not None:
                    answer = fn(*args)
                elif func_name in ("sum_of", "product_of", "diff_of", "div_of"):
                    # эти функции-заглушки мы уже вычислили в classify
                    answer = explanation
                else:
                    answer = fn(query)
            except Exception as e:
                answer = f"ошибка вычисления: {e}"
        # для чистых числовых задач покажем объяснение
        if explanation and answer is None:
            answer = explanation
        confidence = 0.85
    else:
        explanation = ("Не распознан тип задачи. Сформулируй иначе (например: "
                       "«сколько будет 2+2», «реши x²-5x+6=0», «НОД 12 и 18»).")

    return {
        "answer": answer,
        "explanation": explanation,
        "module": module,
        "function": func_name,
        "category": category,
        "confidence": confidence,
        "latency_ms": int((time.time() - t0) * 1000),
    }


# ================== ИНТЕРФЕЙС ДЛЯ ЯДРА ==================

def answer_question(query):
    """Обёртка: строка-ответ для чата. Один return: str."""
    r = think(query)
    head = f"[{r['category']}] "
    answer_value = r["answer"]
    explanation = r["explanation"]
    text = ""
    if answer_value is None:
        text = explanation
    elif isinstance(answer_value, (int, float)) and explanation:
        text = head + explanation
    elif explanation and not isinstance(answer_value, str):
        text = head + f"{explanation} → {answer_value}"
    else:
        text = head + str(answer_value)
    return text


def catalog():
    """Каталог всех доступных алгоритмов по модулям."""
    reg = list_available()
    total = sum(len(m["functions"]) for m in reg)
    return {"modules": reg, "total_functions": total, "total_modules": len(reg)}


if __name__ == "__main__":
    tests = [
        "сколько будет 2+2",
        "15% от 200",
        "реши x²-5x+6=0",
        "C(10,3)",
        "вероятность 2 из 6",
        "энергия связи если дефект массы 0.002",
        "полураспад: 100 г, 2 периода",
        "a²+b²=c², a=3 b=4",
        "НОД 48 и 36",
        "12 простое?",
        "сортировать 5 2 8 1",
        "привет",
    ]
    for t in tests:
        r = think(t)
        print(f"Q: {t}")
        if r["answer"] is not None:
            print(f"  → {r['explanation'] or r['answer']}")
        else:
            print(f"  → {r['explanation']}")
        print()