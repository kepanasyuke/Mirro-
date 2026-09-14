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
    """Загружает модуль алгоса по имени файла (с кэшем)."""
    if name in _cache:
        return _cache[name]
    path = ALGO_DIR / f"{name}.py"
    if not path.exists():
        return None
    try:
        spec = importlib.util.spec_from_file_location(name, path)
        mod = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _cache[name] = mod
        return mod
    except Exception:
        return None


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
    m = re.search(r"(\d+[.,]?\d*)\s*%\s*(от|из|от числа)?\s*(\d+[.,]?\d*)?", q)
    if m and "процент" in q or m:
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


def _solve_quadratic(a, b, c):
    """Находит корни квадратного уравнения. Возвращает список корней."""
    import math as _m
    if a == 0:
        if b == 0:
            return []
        return [-c / b]
    D = b * b - 4 * a * c
    if D < 0:
        return []
    if D == 0:
        return [-b / (2 * a)]
    sq = _m.sqrt(D)
    return [(-b - sq) / (2 * a), (-b + sq) / (2 * a)]


def _percent_of(pct, base):
    return pct / 100 * base


def _solve_linear(a, b):
    """ax + b = 0."""
    if a == 0:
        return []
    return [(0 - b) / a]


# ================== ЯДРО «ПОДУМАТЬ» ==================

def think(query):
    """
    Главный метод: дать ответ на вопрос, используя алгоритмы.
    Возвращает dict: {answer, explanation, module, function, category, confidence}
    """
    t0 = time.time()
    result = classify(query)

    if not result:
        return {
            "answer": None,
            "explanation": "Не распознан тип задачи. Сформулируй иначе (например: "
                           "«сколько будет 2+2», «реши x²-5x+6=0», «НОД 12 и 18»).",
            "category": "unknown",
            "confidence": 0.0,
            "latency_ms": int((time.time() - t0) * 1000),
        }

    category, module, func_name, args, explanation = result

    # загружаем модуль и вызываем функцию
    mod = load_module(module)
    answer = None
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

    return {
        "answer": answer,
        "explanation": explanation,
        "module": module,
        "function": func_name,
        "category": category,
        "confidence": 0.85,
        "latency_ms": int((time.time() - t0) * 1000),
    }


# ================== ИНТЕРФЕЙС ДЛЯ ЯДРА ==================

def answer_question(query):
    """Обёртка: строка-ответ для чата."""
    r = think(query)
    if r["answer"] is None:
        return r["explanation"]
    # красивое оформление
    head = f"[{r['category']}] "
    if isinstance(r["answer"], (int, float)) and r["explanation"]:
        return head + r["explanation"]
    item = r["answer"]
    if r["explanation"] and not isinstance(r["answer"], str):
        return head + f"{r['explanation']} → {item}"
    return head + str(item)


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