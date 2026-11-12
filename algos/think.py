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

# путь к каталогу алгосов — от текущего файла, а не жёстко прописанный
# (кроссплатформенность: работает и на Windows, и на Linux)
ALGO_DIR = Path(__file__).resolve().parent

_cache = {}


def load_module(name):
    """Загружает модуль алгоса по имени файла (с кэшем).
    Битый/несуществующий модуль не кэшируется (позволяет повторную попытку).
    Один return: module|None."""
    mod = _cache.get(name)
    if mod is not None:
        return mod
    path = ALGO_DIR / f"{name}.py"
    if not path.exists():
        return None
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
    """Число загруженных модулей. Один return: int."""
    return len(_cache)


def list_available():
    """Список всех доступных функции во всех модулях (полный реестр).
    Один return: list."""
    registry = []
    for f in sorted(ALGO_DIR.glob("*.py")):
        name = f.stem
        if not name.startswith("_") and name != "think":
            mod = load_module(name)
            if mod:
                funcs = [x for x in dir(mod) if not x.startswith("_") and callable(getattr(mod, x))]
                registry.append({"module": name, "functions": funcs})
    return registry


def _numbers(text):
    """Все числа из текста (float). Некорректные пропускаются.
    Один return: list."""
    out = []
    try:
        src = str(text or "")
    except Exception:
        src = ""
    for x in re.findall(r"-?\d+[.,]?\d*", src.replace("\u2212", "-")):
        try:
            out.append(float(x.replace(",", ".")))
        except Exception:
            continue
    return out


def _int_numbers(text):
    """Целые числа из текста (только те, что без дробной части). Один return: list."""
    out = []
    for x in _numbers(text):
        try:
            if float(x).is_integer():
                out.append(int(x))
        except Exception:
            continue
    return out


# ================== РАСПОЗНАВАНИЕ ВОПРОСА ==================

def classify(query):
    """
    Возвращает (категория, модуль, функция, аргументы, объяснение) или None.
    Распознаёт типовые задачи вузов/ссузов/олимпиад.
    Пустой/None-запрос → None.
    """
    if query is None or not isinstance(query, str) or not query.strip():
        return None
    q = query.lower().strip()
    if len(q) > 2000:
        # очень длинный «вопрос» — не задача, а текст; не разбираем регулярами
        return None
    result = None
    if result is None:
        result = _c_simple_math(q)
    if result is None:
        result = _c_percent(q)
    if result is None:
        result = _c_quadratic(q)
    if result is None:
        result = _c_linear(q)
    if result is None:
        result = _c_combinatorics(q)
    if result is None:
        result = _c_probability(q)
    if result is None:
        result = _c_physics(q)
    if result is None:
        result = _c_geometry(q)
    if result is None:
        result = _c_gcd_lcm_prime(q)
    if result is None:
        result = _c_strings_sorts(q)
    return result


def _c_simple_math(q):
    """Простая арифметика: сколько будет / x+y, x-y, x*y, x/y.
    Поддерживает длинные тире (–, —) как минус. Не путает с уравнениями
    (есть x) и новыми датами (год не считает). Один return: tuple|None."""
    has_math_words = "умнож" in q or "плюс" in q or "минус" in q or "дели" in q or "раздел" in q
    out = None
    # не считаем одиночное число без операции (даты, телефоны, номера)
    has_op = any(op in q for op in ("+", "-", "–", "—", "*", "/", "×"))
    if not has_op and not has_math_words:
        return out
    if "x" not in q and ("сколько будет" in q or re.search(r"\d+\s*[+\-*/×]\s*\d+", q) or has_math_words):
        nums = _numbers(q)
        is_mult = bool("*" in q.replace("×", "*") or "умнож" in q or "умножить" in q)
        has_symbol_mult = bool("×" in q or "*" in q or "умнож" in q or "умножить" in q)
        if is_mult and len(nums) >= 2:
            if has_symbol_mult:
                out = ("математика", "01_stats", "product_of", None,
                       f"{nums[0]:g} × {nums[1]:g} = {nums[0]*nums[1]:.6g}")
            else:
                out = ("математика", "01_stats", "product_of", None, str(nums[0] * nums[1]))
        elif ("+" in q or "плюс" in q or "минус" in q or "–" in q or "—" in q) and len(nums) >= 2:
            if "+" in q or "плюс" in q:
                out = ("математика", "01_stats", "sum_of", None,
                       f"{nums[0]:g} + {nums[1]:g} = {nums[0]+nums[1]:.6g}")
            else:
                out = ("математика", "01_stats", "diff_of", None,
                       f"{nums[0]:g} − {nums[1]:g} = {nums[0]-nums[1]:.6g}")
        elif ("/" in q or "дели" in q or "раздел" in q) and len(nums) >= 2 and nums[1] != 0:
            out = ("математика", "01_stats", "div_of", None,
                   f"{nums[0]:g} / {nums[1]:g} = {nums[0]/nums[1]:.6g}")
    return out


def _c_percent(q):
    """Проценты: «X% от Y» / «X процентов от Y». Один return: tuple|None."""
    out = None
    # Поддерживаем и символ %, и словесную форму «15 процентов от 200».
    m = re.search(
        r"(\d+[.,]?\d*)\s*(?:%|процент(?:ов|а|у|ом)?)\s*(от|из|от числа|числа)?\s*(\d+[.,]?\d*)?",
        q)
    if m and m.group(3) and m.group(1):
        try:
            pct = float(m.group(1).replace(",", "."))
            base = float(m.group(3).replace(",", "."))
        except Exception:
            return None
        if pct < 0 or base < 0:
            return None
        result = pct / 100 * base
        out = ("математика", "16_university", "percent_of", (pct, base),
               f"{pct:g}% от {base:g} = {result:.6g}")
    return out


def _c_quadratic(q):
    """Квадратное уравнение ax²+bx+c=0. Один return: tuple|None."""
    out = None
    is_quad = ("квадратн" in q or "x²" in q or "x^2" in q or "x**2" in q) and "=" in q
    if is_quad:
        expr = q.replace("×", "").replace(" ", "")
        m = re.search(r"([+-]?\d*\.?\d*)?x(?:\^2|\u00b2)?\s*([+-]?\d*\.?\d*)?x\s*([+-]\d*\.?\d*)?\s*=\s*0", expr)
        if m:
            try:
                a_s, b_s, c_s = m.group(1), m.group(2), m.group(3)
                a = -1.0 if a_s == "-" else (float(a_s) if a_s not in (None, "") else 1.0)
                b = 1.0 if b_s == "+" else (-1.0 if b_s == "-" else (float(b_s) if b_s not in (None, "") else 0.0))
                c = 1.0 if c_s == "+" else (-1.0 if c_s == "-" else (float(c_s) if c_s not in (None, "") else 0.0))
            except Exception:
                return None
            roots = _solve_quadratic(a, b, c)
            out = ("математика", "16_university", "solve_quadratic", (a, b, c),
                   f"{a:g}x²{'+' if b>=0 else ''}{b:g}x{'+' if c>=0 else ''}{c:g}=0 → корни: {roots}")
    return out


def _c_linear(q):
    """Линейное ax + b = rhs. Один return: tuple|None."""
    out = None
    if ("реши" in q or "найди x" in q or "уравнен" in q) and "x" in q:
        is_quad = ("квадратн" in q or "x²" in q or "x^2" in q or "x**2" in q) and "=" in q
        m = re.search(r"([+-]?\d*\.?\d*)x\s*([+-]\d*\.?\d*)?\s*=\s*(-?\d+\.?\d*)", q.replace(" ", "").replace("=", " = "))
        if m and not is_quad:
            a = 1.0 if m.group(1) in (None, "", "+", "-") else float(m.group(1))
            b_lin = float(m.group(2)) if m.group(2) else 0.0
            rhs = float(m.group(3)) if m.group(3) else 0.0
            if a != 0:
                out = ("математика", "16_university", "solve_linear", (a, rhs - b_lin),
                       f"x = {(rhs - b_lin) / a:.6g}")
    return out


def _c_combinatorics(q):
    """Комбинаторика: C(n,k), сочетания, перестановки/факториал.
    Один return: tuple|None."""
    out = None
    m_c = re.match(r"c\s*\(?(\d+)\s*[;,]\s*(\d+)\)?", q)
    if m_c:
        n, k = int(m_c.group(1)), int(m_c.group(2))
        if k <= n and n <= 2000:
            out = ("комбинаторика", "10_combinatorics", "combinations_count", (n, k),
                   f"C({n},{k}) = {_comb(n,k)}")
        else:
            out = ("комбинаторика", "10_combinatorics", "combinations_count", (n, k),
                   f"C({n},{k}) — некорректное значение")
    elif re.search(r"\d+\s*!", q):
        m_fact = re.search(r"(\d+)\s*!", q)
        n = int(m_fact.group(1))
        if 0 <= n <= 1000:
            out = ("комбинаторика", "10_combinatorics", "factorial", (n,), f"{n}! = {_fact(n)}")
        else:
            out = ("комбинаторика", "10_combinatorics", "factorial", (n,),
                   f"{n}! — слишком большое значение")
    elif ("сочет" in q or "c(" in q.lower()) and len(_int_numbers(q)) >= 2:
        nums = _int_numbers(q)
        n, k = nums[0], nums[1]
        if n > 2000 or k > n or (n >= 0 and k < 0):
            out = ("комбинаторика", "10_combinatorics", "combinations_count", (n, k),
                   f"C({n},{k}) — некорректное значение")
        else:
            out = ("комбинаторика", "10_combinatorics", "combinations_count", (n, k),
                   f"C({n},{k}) = {_comb(n,k)}")
    elif ("перестанов" in q or "факториал" in q) and _int_numbers(q):
        nums = _int_numbers(q)
        n = nums[0]
        if n < 0:
            out = ("комбинаторика", "10_combinatorics", "factorial", (n,),
                   f"{n}! не определён для отрицательных чисел")
        elif 0 <= n <= 1000:
            out = ("комбинаторика", "10_combinatorics", "factorial", (n,), f"{n}! = {_fact(n)}")
        else:
            out = ("комбинаторика", "10_combinatorics", "factorial", (n,),
                   f"{n}! — слишком большое значение")
    return out


def _c_probability(q):
    """Классическая вероятность. Один return: tuple|None."""
    out = None
    nums = _numbers(q)
    if ("вероятн" in q or "шанс" in q) and len(nums) >= 2:
        nums = nums[:2]
        if (nums[1] != 0 and 0 <= nums[0] <= nums[1]
                and nums[0] == nums[0] and nums[1] == nums[1]):
            out = ("вероятность", "12_probability", "classical_probability", (nums[0], nums[1]),
                   f"P = {nums[0]:g}/{nums[1]:g} = {nums[0]/nums[1]:.4f}")
    return out


def _c_physics(q):
    """Физика: энергия связи / полураспад. Один return: tuple|None."""
    out = None
    nums = _numbers(q)
    if "энерги" in q and "связ" in q and nums:
        d = nums[0]
        if 0 < d <= 1e6:
            out = ("физика", "16_university", "binding_energy", (d,),
                   f"E = {d:g}·931.5 МэВ = {d*931.5:.3g} МэВ")
    elif "полураспад" in q and len(nums) >= 3:
        n0, t, th = nums[:3]
        # защита от деления на ноль и отрицательного периода (физически невозможен)
        if th <= 0 or th != th:
            th = 1.0
        if t != t or n0 != n0:
            out = None
        elif n0 >= 0:
            ratio = t / th
            if ratio > 1000 or ratio != ratio:
                ratio = 1000.0
            out = ("физика", "16_university", "half_life_remaining", (n0, t, th),
                   f"N = {n0:g}·2^(-{t:g}/{th:g}) = {n0*2**(-ratio):.4g}")
    return out


def _c_geometry(q):
    """Геометрия: Пифагор / Герон. Один return: tuple|None."""
    out = None
    nums = _numbers(q)
    if "пифагор" in q and len(nums) >= 2:
        a, b = nums[:2]
        if a != a or b != b or a < 0 or b < 0 or (a == 0 and b == 0) or max(abs(a), abs(b)) > 1e12:
            out = None
        else:
            out = ("геометрия", "16_university", "right_triangle_sides", (a, b),
                   f"гипотенуза = {math.hypot(a,b):.4g}")
    elif ("герон" in q or "площадь треугольн" in q) and len(nums) >= 3:
        a, b, c = nums[:3]
        if a != a or b != b or c != c or a <= 0 or b <= 0 or c <= 0:
            out = None
        elif max(a, b, c) > 1e9:
            out = None
        # неравенство треугольника: стороны должны образовывать треугольник
        elif a + b <= c or a + c <= b or b + c <= a:
            out = ("геометрия", "16_university", "triangle_area_heron", (a, b, c),
                   "не треугольник: нарушено неравенство треугольника")
        else:
            s = (a + b + c) / 2
            radic = s * (s - a) * (s - b) * (s - c)
            if radic != radic:
                radic = 0.0
            if radic < 0:
                radic = 0.0
            if radic > 1e18:
                radic = 0.0
            area = math.sqrt(radic)
            out = ("геометрия", "16_university", "triangle_area_heron", (a, b, c),
                   f"площадь = {area:.4g}")
    return out


def _c_gcd_lcm_prime(q):
    """НОД/НОК/простое число. Один return: tuple|None."""
    out = None
    if ("нод" in q or "наибольший общий" in q or "gcd" in q) and len(_int_numbers(q)) >= 2:
        nums = _int_numbers(q)
        a, b = nums[0], nums[1]
        if a == b == 0:
            out = ("математика", "08_math", "gcd", (0, 0), "НОД(0,0) = 0")
        elif a != 0 and b != 0 and abs(a) * abs(b) <= 10**12:
            out = ("математика", "08_math", "gcd", (a, b), f"НОД({a},{b}) = {_gcd(a, b)}")
        elif (a == 0) != (b == 0):
            nonzero = a if b == 0 else b
            out = ("математика", "08_math", "gcd", (a, b),
                   f"НОД({a},{b}) = {abs(nonzero)}")
    elif ("нок" in q or "наименьшее общее" in q or "lcm" in q) and len(_int_numbers(q)) >= 2:
        nums = _int_numbers(q)
        a, b = nums[0], nums[1]
        if a == b == 0:
            out = ("математика", "08_math", "lcm", (0, 0), "НОК(0,0) = 0")
        elif a != 0 and b != 0 and abs(a) * abs(b) <= 10**12:
            out = ("математика", "08_math", "lcm", (a, b), f"НОК({a},{b}) = {_lcm(a, b)}")
    elif "прост" in q and _int_numbers(q):
        nums_p = _int_numbers(q)
        n = nums_p[0]
        if n == 0 or n == 1:
            out = ("математика", "08_math", "is_prime", (n,), f"{n} не простое (по определению)")
        elif n > 1:
            out = ("математика", "08_math", "is_prime", (n,), f"{n} простое? {_isprime(n)}")
    return out


def _c_strings_sorts(q):
    """Палиндром / сортировка. Один return: tuple|None."""
    out = None
    if "палиндром" in q:
        if len(q) > 5000:
            q = q[:5000]
        out = ("строки", "06_strings", "is_palindrome", (q,), None)
    elif "сортир" in q:
        arr = _int_numbers(q)
        if len(arr) > 1000:
            arr = arr[:1000]
        if arr:
            shown = sorted(arr)[:20]
            out = ("алгоритмы", "05_sorts", "quick_sort", (arr,),
                   f"сортировка: {shown}")
        else:
            out = ("алгоритмы", "05_sorts", "quick_sort", (arr,),
                   "нечего сортировать: числа не найдены")
    return out


# --- хелперы без импорта модулей (для мгновенных объяснений) ---
def _comb(n, k):
    try:
        n, k = int(n), int(k)
    except Exception:
        return 0
    if n < 0 or k < 0 or k > n:
        return 0
    if n > 2000:
        return 0  # не считаем гигантские сочетания (предотвращает переполнение)
    k = min(k, n - k)
    if k == 0:
        return 1
    r = 1
    for i in range(1, k + 1):
        r = r * (n - k + i) // i
    return r


def _fact(n):
    try:
        n = int(n)
    except Exception:
        return 1
    if n < 0 or n > 10000:
        return 1
    r = 1
    for i in range(2, n + 1):
        r *= i
    return r


def _gcd(a, b):
    try:
        a, b = abs(int(a)), abs(int(b))
    except Exception:
        return 0
    while b:
        a, b = b, a % b
    return a


def _lcm(a, b):
    try:
        a, b = int(a), int(b)
    except Exception:
        return 0
    return abs(a * b) // _gcd(a, b) if a and b else 0


def _isprime(n):
    """Простое ли число (только неотрицательные целые вне bool).
    Не-целое/отрицательное/слишком большое (>2^31) → False. Один return: bool."""
    if isinstance(n, bool) or not isinstance(n, int) or n < 0 or n > 2 ** 31:
        return False
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
    """Корень линейного ax+b=0 (a!=0; a==0 → None). Один return: float|None."""
    try:
        a = float(a)
        b = float(b)
    except Exception:
        return None
    if a == 0 or a != a or b != b:
        return None
    if abs(a) < 1e-15:
        return None
    return -b / a


def _solve_quadratic(a, b, c):
    """Находит корни квадратного уравнения. Не-числовые коэффициенты → [].
    Один return: list корней."""
    import math as _m
    try:
        a, b, c = float(a), float(b), float(c)
    except Exception:
        return []
    if a != a or b != b or c != c or abs(a) > 1e12 or abs(b) > 1e12 or abs(c) > 1e12:
        return []
    roots = []
    if a == 0:
        if b != 0:
            r = _solve_linear_root(b, c)
            roots = [r] if r is not None else []
    else:
        D = b * b - 4 * a * c
        if D != D or D in (float("inf"), float("-inf")):
            return []
        if D < 0:
            roots = []
        elif D == 0:
            roots = [-b / (2 * a)]
        else:
            sq = _m.sqrt(D)
            roots = [(-b - sq) / (2 * a), (-b + sq) / (2 * a)]
    return roots


def _percent_of(pct, base):
    try:
        pct = float(pct)
        base = float(base)
        return pct / 100.0 * base
    except Exception:
        return 0.0


def _solve_linear(a, b):
    """ax + b = 0. Не-числовые коэффициенты → []. Один return: list."""
    try:
        a = float(a)
        b = float(b)
    except Exception:
        return []
    if a != a or b != b:
        return []
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
    valid_result = isinstance(result, (tuple, list)) and len(result) == 5
    if not valid_result:
        result = None

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
        category = "unknown"
        module = None
        func_name = None

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
    """Обёртка: строка-ответ для чата. Пустой запрос → подсказка. Один return: str."""
    if not isinstance(query, str) or not query.strip():
        return "[unknown] Сформулируй вопрос, и я посчитаю или объясню."
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
    """Каталог всех доступных алгоритмов по модулям. Один return: dict."""
    reg = list_available() or []
    total = sum(len(m.get("functions", [])) for m in reg if isinstance(m, dict))
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