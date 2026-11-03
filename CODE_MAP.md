# Карта кода Mirro (Code Map)

Структурный просмотр: какие функции есть, где, и что повторяется.

## Точка входа (ядро)

Файл: `core/mirro_core.py` — HTTP-сервер + маршрутизация ответов.

Цепочка ответа (`build_response` → `_try_direct_handlers`):
```
try_greetings → try_learn → try_algos_think → try_humor → try_creative
→ try_jarvis → try_dialog → try_bosova_engine → try_ai_history
→ try_knowledge_graph → try_graph_infer → try_dialogue_memory
→ try_zero_dim → try_growth
→ (fallback) try_tfidf → try_rag → try_web → try_provider
```
Каждая `try_*` возвращает либо строку-ответ (остановка), либо None (переход дальше).

## Модули algos/ (интеллектуальные алгоритмы)

| Файл | Назначение | Ключевые функции |
|---|---|---|
| `01_stats.py` | Статистика | mean, median, variance, stddev, pearson, zscore |
| `02_nlp.py` | NLP: токены, стемминг, TF-IDF, сентимент | tokenize, russian_stem, tfidf, MiniLemmatizer, sentiment |
| `03_search.py` | Поиск | binary_search, bm25, edit_distance, fuzzy_match, invert_index |
| `05_sorts.py` | Сортировки | bubble…radix, timsort |
| `06_strings.py` | Строки | reverse, palindrome, levenshtein, kmp, anagram |
| `07_graphs.py` | Графы | bfs, dfs, dijkstra, kruskal_mst, topological_sort |
| `08_math.py` | Математика | gcd, lcm, is_prime, fib, pow_mod, phi |
| `09_dp.py` | Динамика | knapsack, lcs, coin_change, LIS |
| `10_combinatorics.py` | Комбинаторика | factorial, binomial, catalan, derangements |
| `11_physics.py` | Физика | гравитация, орбиты, три тела, квант |
| `12_probability.py` | Вероятность | bayes, normal_pdf, monte_carlo, entropy, markov |
| `13_boolean.py` | Булева логика | and/or/xor, half_adder, де Морган |
| `14_quantum.py` | Квантовое | Qubit, hadamard, bell, 3-значная логика |
| `15_hilbert.py` | Планковские/гильберт | planck_*, inner_product, gram_schmidt, hermitian |
| `16_university.py` | Школьная/университет | квадратные ур-ния, ядерная физика, геометрия |
| `18_humor.py` | **Дубль** → `humor.py` | (удалён) |
| `20_reasoning.py` | **Дубль** → `reasoning.py` | (удалён) |
| `humor.py` | Юмор (канонический) | shutka, sarkazm, o_udache_i_uspehe |
| `reasoning.py` | Рассуждения (канонический) | think_about_thinking, citata_bosovy, get_scheme |
| `knowledge_graph.py` | Знаниевый граф | Node, KnowledgeGraph, add_edge, path, relation, try_knowledge_graph |
| `graph_infer.py` | Вывод через граф | infer_from_graph, try_graph_infer |
| `dialogue_memory.py` | Память диалога | DialogueMemory, try_dialogue_memory |
| `novelty.py` | Детектор новизны | Novelty, try_novelty |
| `ttl_extract.py` | Извлечение триплетов | extract, ingest_into |
| `zero_dimensional.py` | Нульмерный граф + рост размерности | field_signature, dimension_of, growth_report, try_zero_dim, try_growth |
| `knowledge_ai_history.py` | История ИИ | применить, _lookup, run_self_check |
| `bosova_engine.py` | Схемы Босовой | применить, схема_мышления, тройственность |
| `think.py` | Мыслительный движок | classify, think, answer_question |

## Выявленные повторы (на 04.11.2026)

| Группа | Что | Статус |
|---|---|---|
| `18_humor.py` / `humor.py` | Полные дубли юмора; `humor.py` богаче (есть `o_udache_i_uspehe`) | `18_humor.py` **удалён**, канон — `humor.py` |
| `20_reasoning.py` / `reasoning.py` | Идентичные (7985 байт, diff пуст) | `20_reasoning.py` **удалён**, канон — `reasoning.py` |
| `применить`/`run_self_check` в `bosova_engine` и `knowledge_ai_history` | Одинаковый паттерн (обработчик + self-check), но **разные модули**, не дубли | Оставить (разная логика) |
| `rec` внутри 07_graphs / 10_combinatorics | Одноименный вспомогательный `rec` (локальные, в разных модулях) | Не дубли — локальные |
| `de_broglie_wavelength` в 11 и 15 | Одна функция в двух модулях | **На заметку**: проверить, не стоит ли вынести в общий |

## Рекомендации

1. `de_broglie_wavelength` (11_physics и 15_hilbert) — кандидат на вынос в общий модуль физики.
2. Регулярно гонять скрипт поиска дублей по именам (`def X` в >1 файле).
3. Новые функции добавлять в канонический модуль, а не копией.