# -*- coding: utf-8 -*-
"""Mirro Algorithms — База знаний по функциям (module knowledge)

Каждая тематическая функция алгоритмов получает встроенное знание:
тема, что она делает, формула или пример. Mirro отвечает на вопрос
«что делает функция X? / объясни алгоритм Y» из этой карты.

Описание — это КОРОТКАЯ формула/суть, понятная и без запуска кода.
Один файл знаний, без внешних библиотек.
"""
import re as _re

# (псевдоним*: имя функции) -> dict(module, topic, what, ex)
# Псевдонимы позволяют находить по русскому или краткому имени.
_KNOWLEDGE = {
    # ---------------- статистика (01) ----------------
    "mean": {"module": "01_stats", "topic": "среднее арифметическое",
             "what": "сумма всех значений, делённая на их число", "ex": "mean([1,2,3,4])=2.5"},
    "median": {"module": "01_stats", "topic": "медиана",
               "what": "серединное значение отсортированного ряда", "ex": "median([1,3,9])=3"},
    "mode": {"module": "01_stats", "topic": "мода",
             "what": "самое частое значение в выборке", "ex": "mode([1,1,2,3])=1"},
    "variance": {"module": "01_stats", "topic": "дисперсия",
                 "what": "средний квадрат отклонений от среднего; мера разброса", "ex": "variance([1,2,3])=0.67"},
    "stddev": {"module": "01_stats", "topic": "среднеквадратичное отклонение",
               "what": "корень из дисперсии; типичный разброс вокруг среднего", "ex": "stddev = sqrt(variance)"},
    "percentile": {"module": "01_stats", "topic": "перцентиль",
                   "what": "значение, ниже которого лежит p% выборки", "ex": "percentile(90) — порог 90% данных"},
    "covariance": {"module": "01_stats", "topic": "ковариация",
                   "what": "совместное отклонение двух рядов от своих средних", "ex": "cov>0 — рост вместе, <0 — наоборот"},
    "pearson": {"module": "01_stats", "topic": "корреляция Пирсона",
                "what": "нормализованная ковариация, от -1 до 1", "ex": "pearson(x,y)=cov/(σx·σy)"},
    "zscore": {"module": "01_stats", "topic": "z-оценка",
               "what": "сколько с.к.о. значение отстоит от среднего", "ex": "z=(x-μ)/σ"},
    "normalize": {"module": "01_stats", "topic": "нормализация",
                  "what": "приведение ряда к диапазону 0..1", "ex": "(x-min)/(max-min)"},
    # ---------------- НЛП (02) ----------------
    "tokenize": {"module": "02_nlp", "topic": "токенизация",
                 "what": "разбиение текста на слова-токены", "ex": "tokenize('Привет мир')=['привет','мир']"},
    "ngrams": {"module": "02_nlp", "topic": "n-граммы",
               "what": "последовательности из n подряд идущих слов/символов", "ex": "bigrams('аб')={'аб'}"},
    "russian_stem": {"module": "02_nlp", "topic": "русский стеммер",
                     "what": "отсечение окончаний: слова сводятся к основе", "ex": "леса/лесу→лес"},
    "tfidf": {"module": "02_nlp", "topic": "TF-IDF",
              "what": "вес слова = частота в документе × обратная частота по корпусу", "ex": "редкие несущие слова важнее"},
    "sentiment": {"module": "02_nlp", "topic": "тональность",
                  "what": "оценка эмоциональной окраски текста (+/-)", "ex": "'отлично'→+1, 'ужасно'→-1"},
    "similarity_jaccard": {"module": "02_nlp", "topic": "коэффициент Жаккара",
                           "what": "доля общих элементов к объединению", "ex": "J(A,B)=|A∩B|/|A∪B|"},
    # ---------------- поиск (03) ----------------
    "linear_search": {"module": "03_search", "topic": "линейный поиск",
                      "what": "перебор всех элементов; O(n)", "ex": "находит первое совпадение"},
    "binary_search": {"module": "03_search", "topic": "бинарный поиск",
                      "what": "поиск в отсортированном массиве делением пополам; O(log n)", "ex": "быстро, массив обязан быть отсортирован"},
    "bm25": {"module": "03_search", "topic": "BM25",
             "what": "ранжирование документов по релевантности запросу", "ex": "основа поиска в полнотекстовых базах"},
    "cosine_similarity": {"module": "03_search", "topic": "косинусная близость",
                          "what": "косинус угла между векторами документов", "ex": "1 — похожи, 0 — нет"},
    "edit_distance": {"module": "03_search", "topic": "расстояние Левенштейна",
                      "what": "мин. число вставок/удалений/замен", "ex": "'кат'→'кот' = 1"},
    "hamming": {"module": "03_search", "topic": "расстояние Хэмминга",
                "what": "число различающихся позиций в строках равной длины", "ex": "'101' и '100' = 1"},
    "fuzzy_match": {"module": "03_search", "topic": "нечёткое совпадение",
                    "what": "поиск близких по написанию строк", "ex": "исправление опечаток"},
    "invert_index": {"module": "03_search", "topic": "инвертированный индекс",
                     "what": "слово → список документов, где оно есть", "ex": "быстрый полнотекстовый поиск"},
    # ---------------- сортировки (05) ----------------
    "bubble_sort": {"module": "05_sorts", "topic": "пузырьковая сортировка",
                    "what": "соседние элементы меняются так, что больший «всплывает»", "ex": "O(n²), учебная"},
    "merge_sort": {"module": "05_sorts", "topic": "сортировка слиянием",
                   "what": "делим массив пополам и сливаем отсортированные части", "ex": "O(n log n), устойчивая"},
    "quick_sort": {"module": "05_sorts", "topic": "быстрая сортировка",
                   "what": "опорный элемент делит массив на меньшие и большие", "ex": "в среднем O(n log n)"},
    "heap_sort": {"module": "05_sorts", "topic": "пирамидальная сортировка",
                  "what": "строит кучу и извлекает максимумы", "ex": "O(n log n), на месте"},
    "counting_sort": {"module": "05_sorts", "topic": "сортировка подсчётом",
                      "what": "считает вхождения ключей из малого диапазона", "ex": "O(n+k)"},
    "radix_sort": {"module": "05_sorts", "topic": "поразрядная сортировка",
                   "what": "сортирует по разрядам чисел/строк", "ex": "O(d·n)"},
    "timsort": {"module": "05_sorts", "topic": "Timsort",
                "what": "гибрид слияния и вставок, использует упорядоченные подмассивы", "ex": "сортировка Python по умолчанию"},
    # ---------------- строки (06) ----------------
    "is_palindrome": {"module": "06_strings", "topic": "палиндром",
                      "what": "строка, читающаяся одинаково с обеих сторон", "ex": "'анна' — палиндром"},
    "levenshtein": {"module": "06_strings", "topic": "расстояние Левенштейна",
                    "what": "мин. число правок для превращения одной строки в другую", "ex": "через динамическое программирование"},
    "anagram": {"module": "06_strings", "topic": "анаграмма",
                "what": "слова из одного набора букв", "ex": "'кот' и 'ток'"},
    "atbash": {"module": "06_strings", "topic": "шифр Атбаш",
               "what": "буква заменяется на симметричную в алфавите", "ex": "а→я, б→ю"},
    "caesar": {"module": "06_strings", "topic": "шифр Цезаря",
               "what": "сдвиг каждой буквы на k позиций", "ex": "сдвиг на 3: 'абв'→'где'"},
    "substring_kmp": {"module": "06_strings", "topic": "поиск подстроки КМП",
                      "what": "линейный поиск подстроки через префикс-функцию", "ex": "O(n+m)"},
    # ---------------- графы (07) ----------------
    "bfs": {"module": "07_graphs", "topic": "обход в ширину",
            "what": "обход графа по уровням от стартовой вершины", "ex": "кратчайшие пути в невзвешенном графе"},
    "dfs": {"module": "07_graphs", "topic": "обход в глубину",
            "what": "идёт вглубь по ветке до упора, затем назад", "ex": "поиск циклов, топологич. порядок"},
    "topological_sort": {"module": "07_graphs", "topic": "топологическая сортировка",
                         "what": "порядок вершин ациклического графа, рёбра — только вперёд", "ex": "порядок задач"},
    "dijkstra": {"module": "07_graphs", "topic": "алгоритм Дейкстры",
                 "what": "кратчайшие пути с неотрицательными весами", "ex": "маршруты на карте"},
    "kruskal_mst": {"module": "07_graphs", "topic": "остовное дерево Крускала",
                    "what": "минимальное связующее дерево жадным выбором рёбер", "ex": "соединить города дёшево"},
    "has_cycle_directed": {"module": "07_graphs", "topic": "поиск цикла",
                           "what": "проверяет, есть ли в графе ориентированный цикл", "ex": "DFS + цвета вершин"},
    "bipartite_check": {"module": "07_graphs", "topic": "двудольность",
                        "what": "можно ли раскрасить граф в 2 цвета без конфликтов", "ex": "граф без нечётных циклов"},
    "connected_components": {"module": "07_graphs", "topic": "компоненты связности",
                             "what": "сколько кусков связности в графе", "ex": "острова на карте"},
    # ---------------- математика (08) ----------------
    "gcd": {"module": "08_math", "topic": "наибольший общий делитель",
            "what": "наибольшее число, делящее оба", "ex": "НОД(12,18)=6; алгоритм Евклида"},
    "lcm": {"module": "08_math", "topic": "наименьшее общее кратное",
            "what": "наименьшее число, кратное обоим", "ex": "НОК(a,b)=a·b/НОД(a,b)"},
    "is_prime": {"module": "08_math", "topic": "проверка простоты",
                 "what": "число имеет ровно два делителя: 1 и само", "ex": "проверка до √n"},
    "sieve": {"module": "08_math", "topic": "решето Эратосфена",
              "what": "вычёркивание составных чисел до n", "ex": "все простые до n за O(n log log n)"},
    "factorize": {"module": "08_math", "topic": "факторизация",
                  "what": "разложение числа на простые множители", "ex": "12 = 2²·3"},
    "pow_mod": {"module": "08_math", "topic": "быстрое возведение в степень",
                "what": "a^b mod p за O(log b) бинарным возведением", "ex": "криптография, RSA"},
    "modular_inverse": {"module": "08_math", "topic": "обратное по модулю",
                        "what": "число x: a·x ≡ 1 (mod m)", "ex": "деление в модулярной арифметике"},
    "phi": {"module": "08_math", "topic": "функция Эйлера",
            "what": "сколько чисел до n взаимно просты с n", "ex": "φ(10)=4"},
    "fib": {"module": "08_math", "topic": "числа Фибоначчи",
            "what": "ряд, где каждый член — сумма двух предыдущих", "ex": "1,1,2,3,5,8…"},
    "fib_fast": {"module": "08_math", "topic": "быстрый Фибоначчи",
                 "what": "вычисление n-го числа через матричное возведение / золотое сечение", "ex": "O(log n)"},
    # ---------------- ДП (09) ----------------
    "knapsack": {"module": "09_dp", "topic": "задача о рюкзаке",
                 "what": "максимум ценности при ограничении веса", "ex": "DP по весу, O(n·W)"},
    "lis": {"module": "09_dp", "topic": "наибольшая возрастающая подпоследовательность",
            "what": "самая длинная подпосл., элементы растут", "ex": "DP или бинарный поиск"},
    "lcs": {"module": "09_dp", "topic": "наибольшая общая подпоследовательность",
            "what": "самые длинные общие символы с сохранением порядка", "ex": "diff-инструменты"},
    "coin_change": {"module": "09_dp", "topic": "размен монет",
                    "what": "минимальное число монет для суммы", "ex": "жадность не всегда, нужен DP"},
    "max_subarray": {"module": "09_dp", "topic": "максимальный подмассив",
                     "what": "подмассив с наибольшей суммой", "ex": "алгоритм Кадане, O(n)"},
    "rod_cut": {"module": "09_dp", "topic": "отрезок стержня",
                "what": "максимальный доход от распила стержня", "ex": "классическое ДП"},
    "edit_distance_dp": {"module": "09_dp", "topic": "редакционное расстояние ДП",
                         "what": "минимальные правки строк через таблицу", "ex": "O(n·m)"},
    "partition_subset": {"module": "09_dp", "topic": "разбиение на равные суммы",
                         "what": "можно ли разбить массив на два с равной суммой", "ex": "DP по сумме"},
    # ---------------- комбинаторика (10) ----------------
    "factorial": {"module": "10_combinatorics", "topic": "факториал",
                  "what": "произведение всех чисел от 1 до n", "ex": "5!=120"},
    "binomial": {"module": "10_combinatorics", "topic": "биномиальный коэффициент",
                 "what": "число способов выбрать k из n", "ex": "C(5,2)=10"},
    "combinations_count": {"module": "10_combinatorics", "topic": "число сочетаний",
                           "what": "количество выборок без учёта порядка", "ex": "C(n,k)=n!/(k!(n-k)!)"},
    "permutations_count": {"module": "10_combinatorics", "topic": "число перестановок",
                           "what": "количество упорядочиваний n элементов", "ex": "P(n)=n!"},
    "catalan": {"module": "10_combinatorics", "topic": "числа Каталана",
                "what": "число правильных скобочных структур", "ex": "C4=14; C(n)=C(2n,n)/(n+1)"},
    "stirling_second": {"module": "10_combinatorics", "topic": "числа Стирлинга 2-го рода",
                        "what": "число разбиений n элементов на k непустых подмножеств", "ex": "S(3,2)=3"},
    "bell": {"module": "10_combinatorics", "topic": "числа Белла",
             "what": "число всех разбиений n-элем. множества", "ex": "B3=5"},
    "derangements": {"module": "10_combinatorics", "topic": "беспорядки",
                     "what": "перестановки, где ни один элемент не на своём месте", "ex": "D(n)=(n-1)(D(n-1)+D(n-2))"},
    "with_repetition_comb": {"module": "10_combinatorics", "topic": "сочетания с повторениями",
                             "what": "выбор k из n с повтором", "ex": "C(n+k-1, k)"},
    "permutations_list": {"module": "10_combinatorics", "topic": "список перестановок",
                          "what": "генерация всех перестановок", "ex": "n! вариантов"},
    "subsets": {"module": "10_combinatorics", "topic": "подмножества",
                "what": "все 2ⁿ подмножеств множества", "ex": "битовые маски"},
    "nck_mod": {"module": "10_combinatorics", "topic": "сочетания по модулю",
                "what": "C(n,k) mod p для больших n", "ex": "теорема Люка, факториалы mod p"},
    # ---------------- физика (11) ----------------
    "gravitational_force": {"module": "11_physics", "topic": "закон тяготения",
                            "what": "сила притяжения двух масс", "ex": "F=G·m1·m2/r²"},
    "orbital_period": {"module": "11_physics", "topic": "орбитальный период",
                       "what": "время полного оборота по орбите", "ex": "закон Кеплера/Ньютона"},
    "escape_velocity": {"module": "11_physics", "topic": "вторая космическая скорость",
                        "what": "скорость ухода от планеты без возврата", "ex": "v=√(2GM/r)"},
    "kinetic_energy": {"module": "11_physics", "topic": "кинетическая энергия",
                       "what": "энергия движения", "ex": "E=½·m·v²"},
    "potential_energy_grav": {"module": "11_physics", "topic": "потенциальная энергия",
                              "what": "энергия положения в поле тяжести", "ex": "E=m·g·h"},
    "free_fall_time": {"module": "11_physics", "topic": "время свободного падения",
                       "what": "время падения с высоты h", "ex": "t=√(2h/g)"},
    "pendulum_period": {"module": "11_physics", "topic": "период маятника",
                        "what": "время одного колебания маятника", "ex": "T=2π√(L/g)"},
    "photon_energy_from_wavelength": {"module": "11_physics", "topic": "энергия фотона",
                                      "what": "энергия кванта света", "ex": "E=hc/λ"},
    "de_broglie_wavelength": {"module": "11_physics", "topic": "длина волны де Бройля",
                              "what": "волна для частицы с импульсом p", "ex": "λ=h/p"},
    "hydrogen_level_energy": {"module": "11_physics", "topic": "уровни энергии атома водорода",
                              "what": "энергии стационарных уровней", "ex": "E_n=-13.6/n² эВ"},
    # ---------------- вероятность (12) ----------------
    "bayes": {"module": "12_probability", "topic": "теорема Байеса",
              "what": "обновление вероятности гипотезы по данным", "ex": "P(A|B)=P(B|A)P(A)/P(B)"},
    "prob_conditional": {"module": "12_probability", "topic": "условная вероятность",
                         "what": "вероятность B при условии A", "ex": "P(B|A)=P(A∩B)/P(A)"},
    "expected_value": {"module": "12_probability", "topic": "математическое ожидание",
                       "what": "средневзвешенное значение случайной величины", "ex": "E=Σx·P(x)"},
    "binomial_pmf": {"module": "12_probability", "topic": "биномиальное распределение",
                     "what": "вероятность k успехов в n испытаниях", "ex": "C(n,k)·p^k·(1-p)^(n-k)"},
    "poisson_pmf": {"module": "12_probability", "topic": "распределение Пуассона",
                    "what": "число событий за интервал при редких событиях", "ex": "P(k)=e^(-λ)·λ^k/k!"},
    "normal_pdf": {"module": "12_probability", "topic": "нормальное распределение",
                   "what": "колоколообразная плотность вероятности", "ex": "p(x)=1/(σ√2π)·e^(-(x-μ)²/2σ²)"},
    "monte_carlo_pi": {"module": "12_probability", "topic": "Монте-Карло для π",
                       "what": "оценка π бросанием случайных точек в круг", "ex": "доля внутри = π/4"},
    "entropy": {"module": "12_probability", "topic": "энтропия Шеннона",
                "what": "мера неопределённости/информации", "ex": "H=-Σp·log(p)"},
    "law_of_large_numbers": {"module": "12_probability", "topic": "закон больших чисел",
                             "what": "среднее выборки стремится к мат. ожиданию", "ex": "при большом n"},
    "mle_normal": {"module": "12_probability", "topic": "оценка по максимум правдоподобия",
                   "what": "подбор параметров распределения по данным", "ex": "μ=среднее, σ²=дисперсия"},
    # ---------------- булева логика (13) ----------------
    "bool_and": {"module": "13_boolean", "topic": "ЛОГИЧЕСКОЕ И",
                 "what": "истинно только когда оба операнда истинны", "ex": "1∧0=0"},
    "bool_or": {"module": "13_boolean", "topic": "ЛОГИЧЕСКОЕ ИЛИ",
                "what": "истинно, если хотя бы один операнд истинен", "ex": "0∨1=1"},
    "bool_not": {"module": "13_boolean", "topic": "ЛОГИЧЕСКОЕ НЕ",
                 "what": "инвертирует значение", "ex": "¬1=0"},
    "bool_xor": {"module": "13_boolean", "topic": "исключающее ИЛИ",
                 "what": "истинно, когда операнды различаются", "ex": "1⊕1=0, 1⊕0=1"},
    "bool_nand": {"module": "13_boolean", "topic": "Штрих Шеффера (И-НЕ)",
                  "what": "отрицание И; функционально полна", "ex": "¬(a∧b)"},
    "bool_nor": {"module": "13_boolean", "topic": "стрелка Пирса (ИЛИ-НЕ)",
                 "what": "отрицание ИЛИ; функционально полна", "ex": "¬(a∨b)"},
    "implication": {"module": "13_boolean", "topic": "импликация",
                    "what": "a→b ложна только при истинном a и ложном b", "ex": "1→0=0, иначе 1"},
    "equivalence": {"module": "13_boolean", "topic": "эквивалентность",
                    "what": "истинна при совпадении операндов", "ex": "a↔b = ¬(a⊕b)"},
    "truth_table": {"module": "13_boolean", "topic": "таблица истинности",
                    "what": "все значения функции при всех комбинациях входов", "ex": "2ⁿ строк"},
    "half_adder": {"module": "13_boolean", "topic": "полусумматор",
                   "what": "суммирует 2 бита: сумма + перенос", "ex": "XOR для суммы, AND для переноса"},
    "full_adder": {"module": "13_boolean", "topic": "полный сумматор",
                   "what": "суммирует 3 бита (с учётом переноса)", "ex": "основа арифметики процессора"},
    "de_morgan_and": {"module": "13_boolean", "topic": "законы де Моргана",
                      "what": "отрицание И = ИЛИ отрицаний", "ex": "¬(a∧b)=¬a∨¬b"},
    "gray_code": {"module": "13_boolean", "topic": "код Грея",
                  "what": "соседние числа отличаются одним битом", "ex": "0,1,3,2,6,7,5,4"},
    "bitcount": {"module": "13_boolean", "topic": "число единичных битов",
                 "what": "сколько 1 в двоичной записи", "ex": "bitcount(13)=3 (1101)"},
    "hamming_weight": {"module": "13_boolean", "topic": "вес Хэмминга",
                       "what": "число ненулевых битов = bitcount", "ex": "для кодов с исправлением ошибок"},
    # ---------------- кванты (14) ----------------
    "qubit_hadamard": {"module": "14_quantum", "topic": "гейт Адамара",
                       "what": "переводит кубит в суперпозицию 50/50", "ex": "|0⟩→(|0⟩+|1⟩)/√2"},
    "qubit_pauli_x": {"module": "14_quantum", "topic": "гейт Паули-X",
                      "what": "квантовый NOT: переворачивает кубит", "ex": "|0⟩↔|1⟩"},
    "qubit_pauli_z": {"module": "14_quantum", "topic": "гейт Паули-Z",
                      "what": "меняет фазу |1⟩ на минус", "ex": "|1⟩→-|1⟩, |0⟩ без изменений"},
    "qubit_phase": {"module": "14_quantum", "topic": "фазовый сдвиг",
                    "what": "поворот фазы кубита на угол φ", "ex": "|1⟩→e^(iφ)|1⟩"},
    "entangled_pair": {"module": "14_quantum", "topic": "запутанность",
                       "what": "связь кубитов: состояние одного задаёт другой", "ex": "пара Белла"},
    "bell_measure": {"module": "14_quantum", "topic": "измерение Белла",
                     "what": "разрушает запутанность, даёт вероятности исходов", "ex": "коррелированные результаты"},
    "superposition_measure": {"module": "14_quantum", "topic": "суперпозиция",
                              "what": "кубит в смеси состояний до измерения", "ex": "вероятности |α|², |β|²"},
    "quantum_probability": {"module": "14_quantum", "topic": "квантовая вероятность",
                            "what": "квадрат модуля амплитуды = вероятность", "ex": "p=|α|²"},
    # ---------------- университет (16) — ключевые ----------------
    "derivative_numerical": {"module": "16_university", "topic": "численная производная",
                             "what": "оценка производной через приращение", "ex": "(f(x+h)-f(x))/h"},
    "integral_riemann": {"module": "16_university", "topic": "интеграл Римана",
                         "what": "площадь под кривой суммированием", "ex": "предел сумм"},
    "taylor_series": {"module": "16_university", "topic": "ряд Тейлора",
                      "what": "приближение функции многочленом в точке", "ex": "eˣ=Σxⁿ/n!"},
    "matrix_multiply": {"module": "16_university", "topic": "умножение матриц",
                        "what": "произведение матриц по правилу строка×столбец", "ex": "C_ij=ΣA_ik·B_kj"},
    "determinant": {"module": "16_university", "topic": "определитель",
                    "what": "число, отражающее «объём» и обратимость матрицы", "ex": "det≠0 → обратима"},
    "eigenvalue": {"module": "16_university", "topic": "собственные значения",
                   "what": "λ: A·v=λ·v — как матрица растягивает векторы", "ex": "важны в PCA, физике"},
    "linear_equations": {"module": "16_university", "topic": "системы линейных уравнений",
                         "what": "решение Ax=b методом Гаусса", "ex": "прямой и обратный ход"},
    # ---- общие понятия (связные определения своими словами) ----
    "_нейросеть": {"topic": "нейросеть",
                    "what": "математическая модель, обучаемая на данных: находит закономерности и применяет их для ответов", "ex": "похожа на сеть связанных нейронов"},
    "_ии": {"topic": "искусственный интеллект",
            "what": "система, решающая задачи, которые обычно требуют человеческого ума: распознавание, понимание, обучение", "ex": "чат-боты, распознавание речи, умные подсказки"},
    "_питон": {"topic": "язык программирования Python",
               "what": "популярный язык программирования: простой синтаксис, огромное сообщество, широкие библиотеки", "ex": "на нём написана сама Mirro",
               "tags": ["питон", "python"]},
    "_граф": {"topic": "граф",
              "what": "структура из вершин (точек) и рёбер (связей между ними)", "ex": "граф знаний Mirro — понятия и их связи"},
    "_алгоритм": {"topic": "алгоритм",
                  "what": "чёткая последовательность шагов для решения задачи", "ex": "рецепт: по шагам приходим к результату"},
    "_память": {"topic": "память",
                "what": "способность сохранять и воспроизводить информацию, опыт, знания", "ex": "у Mirro есть база опыта — память о успешных ответах"},
    "_связь": {"topic": "связь",
               "what": "отношение между понятиями, которое говорит, как они связаны", "ex": "«нейрон — принадлежит — мозг»"},
    "_интерфейс": {"topic": "интерфейс",
                   "what": "способ взаимодействия человека с программой: экран, окна, кнопки, чат", "ex": "веб-чат Mirro — это интерфейс"},
    "_данные": {"topic": "данные",
                "what": "сведения в форме, пригодной для обработки: числа, текст, изображения", "ex": "Mirro обучается на 2.8 млн примеров данных"},
}


class FunctionKnowledge:
    """База знаний по функциям алгоритмов. Один return: строки отчёта."""
    def __init__(self):
        self.data = _KNOWLEDGE
        # индекс по имени и по модулю
        self._by_name = {}
        self._by_module = {}
        for key, info in self.data.items():
            self._by_name[key] = info
            mod = info.get("module")
            if mod:
                self._by_module.setdefault(mod, []).append(key)

    def topic_of(self, name):
        """Возвращает словарь-знание по имени функции. Один return: dict/None."""
        return self._by_name.get(self._norm_key(name))

    def knowledge_for(self, name):
        """Человекочитаемая строка знания про функцию. Один return: str or None."""
        info = self.topic_of(name)
        text = None
        if info:
            mod = info.get("module", "")
            label = f" ({mod})" if mod else ""
            text = (f"{name}{label} — {info['topic']}.\n"
                    f"Что делает: {info['what']}.\nПример: {info['ex']}.")
        return text

    def module_names(self, module):
        """Имена функций модуля. Один return: list."""
        return self._by_module.get(module, [])

    def count(self):
        return len(self._by_name)

    def _norm_key(self, name):
        k = _re.sub(r"[^a-zа-яё0-9_]", "", (name or "").lower())
        key = k
        if k in self._by_name:
            key = k
        else:
            # допускаем суффикс «()» или «функция»
            for variant in (k.rstrip("()"), k.replace("функция", "")):
                if variant in self._by_name:
                    key = variant
                    break
        return key


# синглтон
fk = FunctionKnowledge()


def _norm_q(q):
    """Нормализует строку для поиска по теме. Один return: str."""
    return _re.sub(r"[^а-яёa-z0-9]+", " ", (q or "").lower()).strip()


_RU_SUFFIXES = ("оты", "оте", "ие", "ый", "ое", "ый", "ов", "ев", "ий", "ые",
                "ое", "ая", "ей", "его", "ому", "ыми", "сть", "сти", "ется",
                "ются", "ами", "ых", "нем", "тию", "ция", "ции", "ии", "ия",
                "оя", "ы")

_STEM_EXC = {
    "человек": "человек", "люди": "человек", "человека": "человек",
    "ребенок": "ребенок", "ребёнок": "ребенок", "дети": "ребенок",
    "время": "врем", "времени": "врем", "временем": "врем",
    "я": "я", "она": "он", "оно": "он", "они": "они",
}


def _stem_ru(word):
    """Грубый русский стеммер для сравнения словоформ (с исключениями-основами).
    Один return: str."""
    w = word.lower()
    stem = _STEM_EXC.get(w)
    if stem is None:
        stem = w
        for suf in _RU_SUFFIXES:
            if len(w) > len(suf) + 3 and w.endswith(suf):
                stem = w[:-len(suf)]
                break
    return stem


def _match_by_topic(q):
    """Ищет функцию, тема/описание которой совпадает со словами запроса,
    с учётом словоформ (стем). Главный приоритет — ЧИСЛО слов запроса, которые
    функция покрывает, затем качество совпадения. Пустой запрос → None.
    Один return: str/None."""
    if not (q or "").strip():
        return None
    words = [_stem_ru(w) for w in _norm_q(q).split() if len(w) > 2]
    scored = []
    for name, info in (fk._by_name or {}).items():
        if not isinstance(info, dict):
            continue
        topic_tokens = {_stem_ru(t) for t in _norm_q(info.get("topic", "")).split()}
        what_tokens = {_stem_ru(t) for t in _norm_q(info.get("what", "")).split()}
        name_norm = _norm_q(name)
        hit_words = 0
        quality = 0.0
        for w in words:
            if w in topic_tokens:
                hit_words += 1
                quality += 1.0
            elif w in what_tokens:
                hit_words += 1
                quality += 0.7
            elif w in name_norm:
                quality += 0.4
            elif w in _norm_q(info.get("topic", "")) or w in _norm_q(info.get("what", "")):
                quality += 0.2
        if hit_words or quality >= 0.4:
            # полное совпадение по теме — сильный признак
            exact_topic = bool(words and set(words) <= topic_tokens)
            scored.append((hit_words, quality, exact_topic, name))
    best_name = None
    if scored:
        # сперва точное попадание по теме, затем покрытие и качество
        scored.sort(key=lambda x: (-x[2], -x[0], -x[1]))
        best_name = scored[0][3]
    return best_name


def _is_inventory_q(q):
    """Запрос про «сколько/список функций»? Один return: bool."""
    return any(w in q for w in ("сколько", "список", "все функции", "какие",
                                "перечисли", "каталог", "перечень"))


def _has_function_term(q):
    """Есть ли в запросе явный термин, про который стоит рассказывать про
    функцию (сигнальный глагол вопроса о функции/алгоритме). Пустые бытовые
    реплики («можно тебя спросить», «как дела») не считаются функциональными.
    Один return: bool."""
    signal = any(w in q for w in ("что такое", "что делает", "расскажи про",
                                  "как работает", "объясни", "что за", "про функцию",
                                  "про алгоритм", "какой алгоритм", "какая функция",
                                  "напиши ", "как реализовать", "что значит",
                                  "в чём суть", "зачем нужен", "зачем нужна",
                                  "опиши", "как устроен", "принцип работы",
                                  "какой принцип", "в чём идея"))
    term = any(w in q for w in ("сортировк", "граф", "алгоритм", "функци", "модул",
                                "сложност", "бинар", "пузырьк", "ейлер", "быстр",
                                "степанове", "связ", "подграф", "поиск", "стек",
                                "очередь", "массив", "хеш", "дерево", "фибоначчи",
                                "бит", "перцептрон", "нейрон"))
    return bool(signal or term)


def try_function_knowledge(query):
    """Отвечает про функцию/алгоритм по имени из запроса.
    Пустой запрос → None. Один return: str or None."""
    ans = None
    q = (query or "").lower().strip()
    if not q:
        return None
    # пустые бытовые реплики («можно тебя спросить», «как дела») не должны
    # перехватываться базой функций — требуется явный термин/сигнал
    if _has_function_term(q):
        # инвентарь функций — раньше подбора по словам («сколько функций» не должно
        # перехватывать «функция Эйлера: сколько чисел...»)
        if _is_inventory_q(q) and ("функци" in q or "алгоритм" in q or "модул" in q):
            mods = sorted(getattr(fk, "_by_module", {}) or {})
            lines = [f"Знаний по функциям: {fk.count()}."]
            for m in mods:
                lines.append(f"{m}: {', '.join(fk.module_names(m))}")
            ans = "\n".join(lines)
        else:
            # ищем имя функции: точное вхождение слова или совпадение по стему
            # (распознает «бинарь», «сортировка пузырьком», падежные формы)
            q_names = _norm_q(q).split()
            q_stems = {_stem_ru(w) for w in q_names if len(w) > 2}
            best = []
            for name in fk._by_name or {}:
                if not isinstance(name, str) or len(name) <= 2:
                    continue
                if name in (" " + q + " . , ? ! ()"):
                    best.append((2, len(name), name))
                else:
                    name_stem = _stem_ru(name)
                    if name_stem in q_stems:
                        best.append((1, len(name), name))
            found = None
            if best:
                best.sort(key=lambda x: (-x[0], -x[1]))
                found = best[0][2]
            if found:
                ans = fk.knowledge_for(found)
            else:
                # по теме описания (с учётом словоформ)
                by_topic = _match_by_topic(q)
                if by_topic:
                    ans = fk.knowledge_for(by_topic)
    return ans


def try_definition(query):
    """Отвечает связным определением для ОБЩИХ ПОНЯТИЙ (нейросеть, ИИ, питон,
    граф, алгоритм и т.п.) своими словами — раньше сырого графа.
    Ищет понятие (ключ с префиксом «_») по совпадению термина в запросе.
    Пустой запрос → None. Один return: str|None."""
    ans = None
    q = (query or "").lower().strip()
    if not q:
        return None
    # понятия — это ключи в _KNOWLEDGE, начинающиеся с «_»
    best = []
    for key in (fk._by_name or {}):
        if key.startswith("_"):
            info = fk._by_name[key]
            if not isinstance(info, dict):
                continue
            # матчим по первому слову topic, полному topic, явным tags
            # и по стему (чтобы распознавать падежи: «нейросетью», «граф_ом»)
            terms = [str(info.get("topic", "")).split()[0].lower()]
            full = str(info.get("topic", "")).lower()
            tags = [t.lower() for t in (info.get("tags") or [])]
            q_words = _norm_q(q).split()
            q_stems = {_stem_ru(w) for w in q_words if len(w) > 2}
            hit = None
            for t in terms:
                if t and t in q:
                    hit = len(t)
                    break
                if t and _stem_ru(t) in q_stems:
                    hit = max(hit or 0, len(t))
            if hit is None and full in q:
                hit = len(full)
            if hit is None:
                for t in tags:
                    if t and t in q:
                        hit = len(t)
                        break
                    if t and _stem_ru(t) in q_stems:
                        hit = max(hit or 0, len(t))
            if hit:
                best.append((hit, info["topic"], info["what"], info["ex"]))
    if best:
        best.sort(key=lambda x: -x[0])
        _, topic, what, ex = best[0]
        topic = topic or "это"
        what = what or "некое понятие"
        ans = f"{topic[0].upper() + topic[1:]} — это {what}."
        # если примера нет — не печатаем «Например: пусто»
        if ex and str(ex).strip():
            ans += f" Например: {ex}."
    return ans


if __name__ == "__main__":
    print("функций в базе:", fk.count())
    for probe in ("что делает binary_search", "объясни gcd", "kinetic_energy", "квант запутанность"):
        print("-", probe, "->", (try_function_knowledge(probe) or "None")[:80])