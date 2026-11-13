# Карта кода Mirro (Code Map)

Структурный просмотр: какие функции есть, где, и что повторяется.
Сверено с кодом на 14.11.2026 (база `abd9981`).

## Точка входа (ядро)

Файл: `core/mirro_core.py` — HTTP-сервер + маршрутизация ответов.

Ключевые функции ответа и квантово-комбинаторной интеграции:
- `_chat_payload` — OpenAI-совместимый JSON (модель `mirro-evolutionary-v4`, поле `reasoning_content`)
- `_quantum_context_note` — reasoning-сноска: PINN-loss, суперпозиция, размерность, комбинаторная пара
- `MirroAPI._handle_chat` — обработка POST /v1/chat/completions (SSE и JSON)
- `core/mirro_pinn_bridge.py` — `try_balance_quantum_pinn_state` (резонанс → прунинг → энергия → стабильность с dopamine-порогом)

⚠️ `_combinatoric_pair()` импортирует `algos.combinatorics`, которого в репозитории
нет (реальная функция `evaluate_best_logical_tree` лежит в `algos/10_combinatorics.py`).
Импорт обёрнут в `try/except`, поэтому сервер не падает, но пара концептов всегда
пустая: в `_quantum_context_note` печатается «нет устойчивой пары», а `try_rag`
всегда идёт обычным `rag.search`, без `run_quantum_guided_rag`.

Цепочка ответа (`build_response` → `_try_direct_handlers`):
```
[уточнение _clarify_guess] → [фильтр _moderation_gate] →
try_greetings → try_learn → try_algos_think → try_humor → try_creative
→ try_jarvis → try_dialog → try_steps → try_bosova_engine → try_ai_history
→ try_knowledge_graph → try_graph_infer → try_full_explanation → try_definition
→ try_enrich → try_what_links → try_similar → try_metacognition
→ try_function_knowledge → try_evo → try_quantum → try_dialogue_memory
→ try_zero_dim → try_growth → try_neuromod → try_neural_elec
→ try_user_profile → try_english → try_empathy (только наблюдает, ответа не даёт)
```
Порядок задан списком `handlers` в `_try_direct_handlers` (core/mirro_core.py:1064).
Каждая `try_*` возвращает либо строку-ответ (остановка), либо None (переход дальше).
Если ни одна не сработала, `build_response` идёт дальше сам:
`_split_multipart` (многочастный вопрос) → `_try_web_first` → `_search_best`
(TF-IDF → RAG → семантический реранк) → при мусоре/пустом результате
`try_web` / `_graph_infer_unknown` / `_fallback_chain` (веб → граф → провайдер → подсказка).
После генерации: модерация исходящего, обращение по имени (`user_profile.greet_name`),
подстройка стиля (`adapt_style`) и эмпатическая заставка (`empathy.apply_empathy`).

## Модули algos/ (интеллектуальные алгоритмы)

Нейтральные `NN_*.py` — 16 файлов (04, 17, 18, 19 нет; `02_nlp`, а не `12_nlp`).

| Файл | Назначение | Ключевые функции |
|---|---|---|
| `01_stats.py` | Статистика | mean, median, variance, stddev, percentile, pearson, zscore, winsorize |
| `02_nlp.py` | NLP: токены, стемминг, TF-IDF, сентимент | tokenize, russian_stem, tfidf, MiniLemmatizer, sentiment |
| `03_search.py` | Поиск | linear_search, binary_search, bm25, cosine_similarity, edit_distance, hamming, interpolation_search, fuzzy_match, invert_index |
| `05_sorts.py` | Сортировки | bubble_sort … radix_sort, timsort |
| `06_strings.py` | Строки | reverse_string, is_palindrome, levenshtein, substring_kmp, anagram, caesar, atbash |
| `07_graphs.py` | Графы | bfs, dfs, dijkstra, kruskal_mst, topological_sort, bipartite_check, graph_diameter_bfs |
| `08_math.py` | Математика | gcd, lcm, is_prime, fib, pow_mod, phi |
| `09_dp.py` | Динамика | knapsack, lcs, coin_change, LIS |
| `10_combinatorics.py` | Комбинаторика | factorial, binomial, catalan, derangements, combinations_list, generate_combinations, **evaluate_best_logical_tree** |
| `11_physics.py` | Физика | гравитация, орбиты, три тела, квант, de_broglie_wavelength |
| `12_probability.py` | Вероятность | bayes, normal_pdf, normal_cdf, poisson_pmf, markov_predict, monte_carlo_pi, entropy |
| `13_boolean.py` | Булева логика | bool_and/or/xor, half_adder, full_adder, de_morgan_and/or |
| `14_quantum.py` | Квантовое | Qubit, hadamard, bell, 3-значная логика |
| `15_hilbert.py` | Планковские/гильберт | planck_time … planck_charge, inner_product, gram_schmidt, hermitian_conjugate, de_broglie_energy_wavelength |
| `16_university.py` | Школьная/университет | solve_quadratic, nuclear_mass_defect, triangle_area_heron, euler_characteristic, mixture_percent |
| `humor.py` | Юмор (канонический) | shutka, sarkazm, o_udache_i_uspehe, nichego_ne_delat |
| `reasoning.py` | Рассуждения (канонический) | think_about_thinking, citata_bosovy, get_scheme, list_schemes, render_scheme_steps |
| `knowledge_graph.py` | Знаниевый граф | Node, KnowledgeGraph, add_edge, path, relation, edge_weight, reward_sign, try_knowledge_graph, try_full_explanation, try_enrich, try_what_links, try_similar, try_feedback |
| `graph_infer.py` | Вывод через граф + опыт | infer_from_graph, try_graph_infer, try_infer_unknown, try_get_memory_experience, generate_dynamic_inference, remember_pattern |
| `dialogue_memory.py` | Память диалога | DialogueMemory, try_dialogue_memory |
| `novelty.py` | Детектор новизны | Novelty, try_novelty |
| `ttl_extract.py` | Извлечение триплетов | extract, ingest_into |
| `zero_dimensional.py` | Нульмерный граф + рост размерности | field_signature, dimension_of, dimension_of_understanding, _node_meta_dependencies, growth_report, try_zero_dim, try_growth |
| `knowledge_ai_history.py` | История ИИ | применить, _lookup, run_self_check |
| `bosova_engine.py` | Схемы Босовой | применить, схема_мышления, тройственность, run_self_check |
| `think.py` | Мыслительный движок | classify, think, answer_question, list_available |
| `evolve.py` | Нейроэволюция (популяция графов) | Genome, MirroEvolver, mutate, crossover, evolve_step, try_evolve |
| `quantum_graph.py` | Квантовая суперпозиция концептов | QState, init_quantum_states, apply_quantum_entanglement, collapse_wave_function, quantum_superposition_report, try_quantum |
| `resonance.py` | Волновой резонанс роу-связей | calculate_vector_distance, try_bridge_resonant_edges |
| `refractory.py` | Синаптическое утомление и рефрактерность | RefractoryState, init_refractory_counters, update_refractory_states, apply_fatigue_to_weights |
| `quantum_coherence.py` | Квантовая когерентность и декогеренция | try_apply_decoherence_decay, check_phase_synchrony |
| `immune_sentinel.py` | Иммунный страж графа | run_graph_immune_scan, scan_report |
| `voice_temperament.py` | Адаптивный характер ответов | determine_voice_temperament, try_apply_temperament_filters, apply_temperament_to_text |
| `memory_crystallization.py` | Свёртывающая кристаллизация памяти | calculate_centroid_vector, try_crystallize_experience |
| `mirror_cognition.py` | Зеркальное моделирование сознания | init_mirror_profile, update_mirror_profile, apply_mirror_modulation_to_graph |
| `wave_resonance.py` | Квантовый макро-резонанс фаз | calculate_complex_phase, try_align_quantum_phases |
| `module_knowledge.py` | База знаний по функциям | FunctionKnowledge, try_function_knowledge, try_definition |
| `neuromodulators.py` | Дофамин/серотонин/норадреналин/ацетилхолин | Neuromodulators, style_prefix, answer_with_style, try_neuromod |
| `neural_electric.py` | Электрический контур графа + PINN | fire, activate_chain, hebbian_update_path, try_neural_electric, try_route_pipeline |
| `mindstream.py` | Внутренняя речь, метапознание | MindStream (mind), reasoning_steps, meta_thought, try_metacognition |
| `empathy.py` | Тон собеседника | observe, current_tone, apply_empathy |
| `user_profile.py` | Профиль пользователя | load_profile, learn_from_message, try_user_profile, greet_name, adapt_style |
| `moderation.py` | Фильтр входа/выхода | moderate_input, moderate_output |
| `english_kb.py` + `english_kb_part1..6.py` | Английский: словарь и темы | try_english (части — данные) |

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

## Скрипты нейроэволюции и обслуживания (scripts/)

| Файл | Функция | Назначение |
|---|---|---|
| `scripts/evolution.py` | `create_initial_population` | Стартовая популяция хромосом (нейрохимия ach/ser/dop + W_decoder) |
| `scripts/evolution.py` | `mutate_chromosome` | Мутация химии и весов декодера |
| `scripts/evolution.py` | `run_evolution_epoch` | Оценка через PINN Loss, селекция топ-50%, замена худших |
| `scripts/evolution.py` | `_evaluate_fitness` | PINN-loss на выборке рёбер (быстро для CLI) |
| `scripts/evolve_weights.py` | `run` / `evolve_iteration` | Эволюция собственно весов рёбер графа по fitness |
| `scripts/clean_corpus.py` | `clean_jsonl` / `clean_directory` | Токенизация, дедуп, фильтр мусора в маленьких JSONL-корпусах |
| `scripts/rag.py` | `MirroRAG.search` | Двухуровневый дисковый RAG: глобальный индекс → сегменты → локальный TF-IDF |
| `scripts/rag.py` | `MirroRAG.run_quantum_guided_rag` / `_guided_segments` | Направленный поиск: контекст из комбинаторной пары расширяет запрос перед `search` |
| `scripts/cipher.py` | `encode` / `decode` / `expand_key` / `parse_numbers` | Десятичный поточный шифр (ключ из документа); CLI encode/decode/test |
| `scripts/cipher.py` | `try_generate_secure_key` / `try_load_secure_key` / `transform_bytes_to_cipher` | API шифра для авто-бэкапов (ключ `keys/secret.key`, байт-обёртка) |
| `scripts/restore.py` | `try_find_latest_backup` / `try_restore_graph_from_backup` | Восстановление графа из свежего `backup_<ts>.mirro.enc` → расшифровка → `models/knowledge_graph.pkl` (полный dict {nodes,edges,experience}) |
| `scripts/synaptic_plasticity.py` | `clean_weak_meta_edges` / `apply_ltp_consolidation` | LTD-прунинг слабых роу-ссылок + дофаминовое LTP-закрепление активных рёбер |
| `scripts/algorithms.py` | `MirroAlgorithms.*` | Индекс TF-IDF, BM25, TextRank, CBOW, Naive Bayes, перцептрон/MLP, кэш, FAQ, автообучение |
| `scripts/reasoning_engine.py` | `choose_best` / `confidence_from_score` | Выбор лучшего кандидата и калибровка уверенности |
| `scripts/providers.py` | `fallback` / `status` / `save_keys` | Фоллбэк на DeepSeek/OpenAI, статус ключей |
| `scripts/thinking.py` | `thinking.web_search` / `decide` | Веб-поиск Wikidata/Wikipedia и алгоритм включения |
| `scripts/voice.py` | `try_jarvis` / `speak` | Характер ответа, «Джарвис» |
| `scripts/vault.py` | `Vault` | Локальное хранилище секретов (PBKDF2-SHA256 + HMAC, не AES) |
| `scripts/mirro_cli.py` | `main` | CLI: `ask`/`chat`, `search`, `graph`, `health` |

## Фронтенд (web/)

| Файл | Что это |
|---|---|
| `web/index.html` | Основной чат: виды `#v-chat`, `#v-stats` (аналитика), `#v-clusters` (кластеры + каталог датасетов) |
| `web/meysto-neiroset.html` | «Мейсто Нейросеть»: конструктор нейросети из блоков, задания, поле данных, мета-граф роу-связей |
| `web/mirro-evolve.html` | Визуализация нейроэволюции графа |
| `web/mirro-meysto-dashboard.html` | Дашборд метрик, обновляется `scripts/refresh_dashboard.py` |
| `web/*.php`, `web/mirro-php/` | Отдельная PHP-версия демо, к ядру не подключена |

Рендер мета-графа (`web/meysto-neiroset.html`):

| Функция | Назначение |
|---|---|
| `drawMirroMetaGraph(ctx, w, h, graphData)` | Рисует знаниевый граф + роу-ссылки изогнутыми линиями между центрами синапсов; mod<0 — красный («гасит кашу»), mod>0 — синий («усиливает») |
| `redrawMetaGraph()` | Отрисовка demo-мета-графа на `canvas#cvMeta` (вызывается в анимационном кадре) |

## Выявленные повторы (проверено 14.11.2026)

Полная таблица с решением по каждой группе — в `DUPLICATES.md`
(сгенерирована `python tools/check_duplicates.py --min-lines 6`).

| Группа | Что | Статус |
|---|---|---|
| `18_humor.py` / `humor.py` | Полные дубли юмора; `humor.py` богаче (есть `o_udache_i_uspehe`) | `18_humor.py` **удалён**, канон — `humor.py` |
| `20_reasoning.py` / `reasoning.py` | Идентичные (7985 байт, diff пуст) | `20_reasoning.py` **удалён**, канон — `reasoning.py` |
| `применить`/`run_self_check` в `bosova_engine`, `knowledge_ai_history`, `reasoning_engine` | Одинаковые имена, **разные модули** | Оставить локальными |
| `rec` внутри 07_graphs / 10_combinatorics | Локальные помощники с одним именем | Не дубли (инструмент их пропускает по имени) |
| `de_broglie_wavelength` (11) / `de_broglie_energy_wavelength` (15) | **Разные** функции (одна даёт длину волны, вторая — энергетическую форму) | Не дубли — прежняя пометка снята |
| `connected_components` в 07_graphs и `KnowledgeGraph.connected_components` | Одна на dict-графах, другая — метод класса графа | Оставить локальными |
| `try_*` в `core/mirro_core.py` | Тонкие обёртки с ленивым импортом вокруг функций `algos/` | Оставить: это шов импорта, не копия логики |

## Рекомендации

1. Новые функции добавлять в канонический модуль, а не копией.
2. Регулярно гонять `python tools/check_duplicates.py --min-lines 6`; `main`, `setUp`
   и dunder-методы инструмент уже отбрасывает как шум.
3. Общие помощники (`_json`, `_load_json`, `_get_global_graph`, `convert_item`,
   `_convert_messages`) выносить в `scripts/common.py` — см. `DUPLICATES.md`.