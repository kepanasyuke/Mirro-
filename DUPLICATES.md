# Дубли в коде Mirro — таблица с решениями

Источник: `python tools/check_duplicates.py --min-lines 6` (14.11.2026, база `abd9981`).
Инструмент ищет одинаковые имена `def` в разных файлах и отбрасывает шум
(`main`, `setUp`, `__init__`, `rec`). Каждая строка ниже проверена по коду.

Решения: **вынести** — общий модуль; **оставить** — локальные/разные функции;
**удалить копию** — реальный дубль, оставить канон. Код не менялся — только рекомендации.

## A. Настоящие дубли — кандидаты на вынос

| Имя | Файлы | Что внутри | Решение |
|---|---|---|---|
| `convert_item` | `scripts/decompress_ingest.py`, `scripts/download_and_ingest.py`, `scripts/ingest_data.py` | Конвертация записи датасета в `{instruction,input,output}`: три копии одной логики (Alpaca/ShareGPT), расходятся деталями обрезки строк | **вынести** в `scripts/common.py::convert_item` |
| `_convert_messages` | `scripts/download_and_ingest.py`, `scripts/ingest_data.py` | Сборка пары из `messages[]` для чатовых датасетов | **вынести** туда же |
| `_get_global_graph` | `scripts/evolution.py`, `scripts/evolve_weights.py` | Ленивая загрузка `models/knowledge_graph.pkl` c фоллбэком на `algos.knowledge_graph.kg` | **вынести** в `scripts/common.py` |
| `_load_json` / `_json` | `core/mirro_core.py`, `scripts/health_check.py`; `core/mirro_core.py`, `scripts/collector.py`, `scripts/vault.py` | Чтение JSON с глушением ошибок; варианты отличаются тем, что возвращают при ошибке (`None` / `{}`) | **вынести** одну версию; сейчас расхождение по семантике |
| `compose_answer` | `scripts/algorithms.py` (`MirroAlgorithms.compose_answer`), `scripts/generative_engine.py` (`MirroAI.compose_answer`) | Два независимых сборщика ответа из выдачи; `generative_engine` — упрощённый двойник `algorithms` | **вынести**: `generative_engine` перевести на `algorithms.compose_answer` |
| `_sigmoid` | `algos/evolve.py`, `scripts/algorithms.py` | Одна и та же формула, два модуля | **вынести** в `algos/08_math.py` (там своей `sigmoid` пока нет) |
| `_boost_key` | `scripts/algorithms.py`, `scripts/generative_engine.py` | Нормализация ключа буста при обучении | **вынести** вместе с `compose_answer` |

## B. Совпадают по имени, но разные по смыслу — оставить локальными

| Имя | Файлы | Почему не дубль |
|---|---|---|
| `connected_components` | `algos/07_graphs.py`, `algos/knowledge_graph.py` | Функция над dict-графом и метод класса `KnowledgeGraph` — разные структуры данных |
| `cosine_similarity` | `algos/03_search.py`, `scripts/algorithms.py` | Первая — по векторам `{слово: вес}`, вторая — по двум текстам через токенизацию |
| `try_*` (17 имён) | `core/mirro_core.py` ↔ `algos/*` | Тонкие обёртки с ленивым импортом внутри `_try_direct_handlers`. Это шов импорта, а не копия логики; вынос сделает ядро хрупким |
| `status`, `search`, `think`, `observe`, `save`, `load`, `create`, `get`, `report` | разные модули | Короткие имена разных классов/предметных областей (`MirroThinking.status` ≠ `MirroAlgorithms.status`) |
| `применить`, `run_self_check` | `algos/bosova_engine.py`, `algos/knowledge_ai_history.py`, `scripts/reasoning_engine.py` | Одинаковый паттерн «обработчик + self-check» у независимых баз знаний |
| `_clamp` | `algos/12_probability.py`, `algos/neuromodulators.py` | Двухстрочные утилиты, разные диапазоны по умолчанию |
| `_clean`, `_words`, `_path`, `_extract_topic`, `_fetch`, `_tokenize` | пары модулей | Локальные помощники с узкой семантикой; обобщение ухудшит читаемость |

## C. Локальные помощники одного имени — не дубли

| Имя | Файлы | Решение |
|---|---|---|
| `_extract` | 7 тестов | **оставить** — фикстуры каждого теста свои |
| `_graph`, `_graph_with_anomaly` | тесты | **оставить** |
| `_init_cbow`, `_iter_cbow_windows`, `_train_cbow_step`, `_normalize_cbow`, `build_cbow_embeddings`, `cbow_similarity` | `scripts/algorithms.py` + `tests/test_cbow.py` | **оставить**: тесты дублируют внутренние шаги, чтобы проверять их изолированно |
| `perceptron_*`, `_hidden_forward`, `_mlp_activation`, `_calibrate_priors`, `train_from_history`, `autonomous_learn`, `_save_perceptron`, `_now_iso` | `scripts/algorithms.py` + соответствующие тесты | **оставить**: тест прямо импортирует и мокает методы |
| `_server_up`, `ask`, `_request` | `scripts/run_qa.py` ↔ тесты | **оставить**: у тестов должен быть независимый клиент |
| `check_deps`, `check_data` | `start.py`, `start_mirro.py` | **удалить копию** в `start.py`, если он вообще остаётся в репозитории (см. `REPORT.md`, п. «осталось») |

## D. Мнение по прежним «дублям» из CODE_MAP

| Группа | Факт по коду | Решение |
|---|---|---|
| `18_humor.py` / `humor.py` | файла `18_humor.py` в дереве нет | пометка «удалён» верна, канон — `humor.py` |
| `20_reasoning.py` / `reasoning.py` | файла `20_reasoning.py` в дереве нет | пометка «удалён» верна, канон — `reasoning.py` |
| `de_broglie_wavelength` в 11 и 15 | в `11_physics.py` — `de_broglie_wavelength(m, v)`, в `15_hilbert.py` — `de_broglie_energy_wavelength(m, v)` | **не дубли**, разные формулы; пометку «вынести» снять |

## Как поддерживать

```bash
python tools/check_duplicates.py --min-lines 6   # только функции длиннее 5 строк
python tools/check_duplicates.py                 # всё, включая однострочники
```

Код выхода 1 = найден хотя бы один кандидат (так задумано, для CI-гейта полезнее
`--min-lines`, иначе гейт красный всегда).
