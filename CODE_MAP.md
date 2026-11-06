# Карта кода Mirro (Code Map)

Структурный просмотр: какие функции есть, где, и что повторяется.

## Точка входа (ядро)

Файл: `core/mirro_core.py` — HTTP-сервер + маршрутизация ответов.

Ключевые функции ответа и квантово-комбинаторной интеграции:
- `_chat_payload` — OpenAI-совместимый JSON (модель `mirro-evolutionary-v4`, поле `reasoning_content`)
- `_quantum_context_note` — reasoning-сноска: PINN-loss, суперпозиция, размерность, комбинаторная пара
- `MirroAPI._handle_chat` — обработка POST /v1/chat/completions (SSE и JSON)
- `core/mirro_pinn_bridge.py` — `try_balance_quantum_pinn_state` (резонанс → прунинг → энергия → стабильность с dopamine-порогом)

Цепочка ответа (`build_response` → `_try_direct_handlers`):
```
try_greetings → try_learn → try_algos_think → try_humor → try_creative
→ try_jarvis → try_dialog → try_bosova_engine → try_ai_history
→ try_knowledge_graph → try_graph_infer → try_enrich → try_what_links
→ try_similar → try_func_kb → try_dialogue_memory → try_zero_dim
→ try_growth → try_neuromod → try_neural_elec → try_evo
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
| `10_combinatorics.py` | Комбинаторика | factorial, binomial, catalan, derangements, combinations_list, generate_combinations, evaluate_best_logical_tree |
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
| `knowledge_graph.py` | Знаниевый граф | Node, KnowledgeGraph, add_edge, path, relation, edge_weight, reward_sign, try_knowledge_graph, try_enrich, try_what_links, try_similar, try_feedback |
| `graph_infer.py` | Вывод через граф + опыт | infer_from_graph, try_graph_infer, try_get_memory_experience, generate_dynamic_inference, remember_pattern |
| `dialogue_memory.py` | Память диалога | DialogueMemory, try_dialogue_memory |
| `novelty.py` | Детектор новизны | Novelty, try_novelty |
| `ttl_extract.py` | Извлечение триплетов | extract, ingest_into |
| `zero_dimensional.py` | Нульмерный граф + рост размерности | field_signature, dimension_of, dimension_of_understanding, _node_meta_dependencies, growth_report, try_zero_dim, try_growth |
| `knowledge_ai_history.py` | История ИИ | применить, _lookup, run_self_check |
| `bosova_engine.py` | Схемы Босовой | применить, схема_мышления, тройственность |
| `think.py` | Мыслительный движок | classify, think, answer_question |
| `evolve.py` | Нейроэволюция (популяция графов) | Genome, MirroEvolver, mutate, crossover, evolve_step, try_evolve |
| `quantum_graph.py` | Квантовая суперпозиция концептов | init_quantum_states, apply_quantum_entanglement, collapse_wave_function, quantum_superposition_report, try_quantum |
| `resonance.py` | Волновой резонанс роу-связей | calculate_vector_distance, try_bridge_resonant_edges |
| `refractory.py` | Синаптическое утомление и рефрактерность | init_refractory_counters, update_refractory_states, apply_fatigue_to_weights |
| `quantum_coherence.py` | Квантовая когерентность и декогеренция | try_apply_decoherence_decay, check_phase_synchrony |
| `immune_sentinel.py` | Иммунный страж графа | run_graph_immune_scan |
| `voice_temperament.py` | Адаптивный характер ответов | determine_voice_temperament, try_apply_temperament_filters |
| `memory_crystallization.py` | Свёртывающая кристаллизация памяти | calculate_centroid_vector, try_crystallize_experience |
| `module_knowledge.py` | База знаний по функциям | FunctionKnowledge, try_function_knowledge |

### Нейробиология, мета-граф и роу-маршрутизация (детальный реестр)

Файлы: `algos/neural_electric.py`, `algos/knowledge_graph.py`, `algos/zero_dimensional.py`, `algos/graph_infer.py`, `algos/ttl_extract.py`.

| Модуль | Функция | Назначение |
|---|---|---|
| `neural_electric.py` | `compute_modulated_edges` | Проводимость рёбер как функция нейромедиаторов (ach·ser + dop) |
| `neural_electric.py` | `add_meta_route` | Регистрация роу-ссылки «ребро→ребро» с коэффициентом модуляции (mod<0 = подавление «каши») |
| `neural_electric.py` | `propagate_meta_impulses` | Направленный прогон токов по роу-ссылкам (аксо-аксональные синапсы) |
| `neural_electric.py` | `calculate_physics_loss` | PINN-цензор: отклонение квадратичной энергии от константы среды |
| `neural_electric.py` | `hebbian_update_path` | Мета-Хебб: укрепление/ослабление рёбер пути по знаку фидбека |
| `neural_electric.py` | `try_route_pipeline` | Сквозной контур: биометрия → рёбра → роу-импульсы → PINN → ответ |
| `neural_electric.py` | `try_extract_biometric_context` | Виртуальная биометрия (пульс/GSR/энергия) из текста запроса |
| `knowledge_graph.py` | `edge_weight` | Текущий активный вес связи (проводимость) |
| `knowledge_graph.py` | `reward_sign` | Хебб-обновление связи по знаку отклика (+1 усиление, −1 ослабление) |
| `knowledge_graph.py` | `try_enrich` | Обогащение ответа родственными понятиями через связи |
| `knowledge_graph.py` | `try_what_links` / `try_similar` | Умные запросы связей (что связано / что общего) |
| `zero_dimensional.py` | `dimension_of` | Мерность узла (0D изолированная → 3D мета-граф); учитывает роу-ссылки |
| `zero_dimensional.py` | `dimension_of_understanding` | Средняя мерность сети — метрика роста понимания (для /health) |
| `graph_infer.py` | `try_get_memory_experience` | Косинусное извлечение схожего прошлого опыта из памяти графа |
| `graph_infer.py` | `generate_dynamic_inference` | Смешение текущего паттерна с опытом + декодер в итоговый сигнал |
| `graph_infer.py` | `remember_pattern` | Запись успешного латентного паттерна в Базу Опыта |
| `ttl_extract.py` | `extract` / `ingest_into` | Извлечение триплетов (S→P→O) из текста и кормление графа |

## Скрипты нейроэволюции (scripts/)

| Файл | Функция | Назначение |
|---|---|---|
| `scripts/evolution.py` | `create_initial_population` | Стартовая популяция хромосом (нейрохимия ach/ser/dop + W_decoder) |
| `scripts/evolution.py` | `mutate_chromosome` | Мутация химии и весов декодера |
| `scripts/evolution.py` | `run_evolution_epoch` | Оценка через PINN Loss, селекция топ-50%, замена худших |
| `scripts/evolution.py` | `_evaluate_fitness` | PINN-loss на выборке рёбер (быстро для CLI) |
| `scripts/evolve_weights.py` | `run` / `evolve_iteration` | Эволюция собственно весов рёбер графа по fitness |
| `scripts/clean_corpus.py` | `clean_jsonl` / `clean_directory` | Токенизация, дедуп, фильтр мусора в маленьких JSONL-корпусах |
| `scripts/rag.py` | `MirroRAG.run_quantum_guided_rag` / `_guided_segments` | Направленный дисковый RAG: детерминированный (не hash()) контекст из комбинаторной пары расширяет запрос перед двухуровневым search |
| `scripts/cipher.py` | `encode` / `decode` / `expand_key` / `parse_numbers` | Десятичный поточный шифр (ключ из документа); CLI encode/decode/test |
| `scripts/cipher.py` | `try_generate_secure_key` / `try_load_secure_key` / `transform_bytes_to_cipher` | API шифра для авто-бэкапов (ключ-соль в keys/, поколение и загрузка, байт-обёртка) |
| `scripts/restore.py` | `try_find_latest_backup` / `try_restore_graph_from_backup` | Восстановление графа из свежего `backup_<ts>.mirro.enc` → расшифровка → запись в models/knowledge_graph.pkl (полный dict {nodes,edges,experience}) |
| `scripts/synaptic_plasticity.py` | `clean_weak_meta_edges` / `apply_ltp_consolidation` | LTD-прунинг слабых роу-ссылок + дофаминовое LTP-закрепление активных рёбер |

## Фронтенд: рендер мета-графа (web/meysto-neiroset.html)

| Функция | Назначение |
|---|---|
| `drawMirroMetaGraph(ctx, w, h, graphData)` | Рисует знаниевый граф + роу-ссылки изогнутыми линиями между центрами синапсов; mod<0 — красный («гасит кашу»), mod>0 — синий («усиливает») |
| `redrawMetaGraph()` | Отрисовка demo-мета-графа на `canvas#cvMeta` (вызывается в анимационном кадре) |

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