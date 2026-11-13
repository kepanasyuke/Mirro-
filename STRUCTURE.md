# Структура проекта Mirro

Верхнеуровневая навигация по репозиторию. Для всех функций см. `CODE_MAP.md`.

## Папки

| Папка | Что это | Ключевые файлы |
|---|---|---|
| `algos/` | Библиотека алгоритмов + «нейробиология» | `think.py`, все `NN_*.py` (01–16), нейро-модули |
| `core/` | Ядро: HTTP-сервер, маршрутизация ответов | `mirro_core.py`, `mirro_pinn_bridge.py` |
| `scripts/` | Инфраструктура: поиск, RAG, генерация корпуса, обучение | `algorithms.py`, `rag.py`, `providers.py` |
| `tests/` | Юнит- и интеграционные тесты (pytest/unittest) | `test_*.py` |
| `tools/` | Инструменты разработчика | `check_duplicates.py`, `check_single_return.py` |
| `web/` | Фронтенд | `index.html`, `meysto-neiroset.html`, `mirro-evolve.html`, `mirro-meysto-dashboard.html` |
| `data/` | Корпуса и данные (не коммитится большая часть) | `processed/`, `corpus_big/`, `catalog_phase1.json` |
| `models/` | Кэши индекса и графа (не коммитится) | `index_cache.pkl`, `knowledge_graph.pkl`, `model_state.json`, `rag_index/` |
| `keys/`, `backups/`, `restore/` | Ключи и шифрованные бэкапы (не коммитятся, `keys/` и `restore/` создаются при первом бэкапе) | — |

## Главные документы

| Файл | Зачем |
|---|---|
| `README.md` | Обзор, быстрый старт, архитектура, API |
| `CODE_MAP.md` | Реестр функций по модулям + порядок роутинга `try_*` |
| `DUPLICATES.md` | Таблица найденных дублей с решением по каждой группе |
| `STRUCTURE.md` | Эта навигация по папкам и документам |
| `LINTER.md` | Правила линтера и стиль кода (структурное программирование) |
| `MIRRO_DEPLOY.md` | Деплой на VPS |
| `IDENTITY.md` | Паспорт проекта |

## Точки входа

| Скрипт | Назначение | Путь |
|---|---|---|
| `mirro_launcher.pyw` | GUI-загрузчик (кнопка + меню, логи в `logs/`) | жёстко `D:\Mirro` |
| `start_mirro.py` | Консольный лаунчер с проверками, `--lite` | относительно своего файла |
| `core/mirro_core.py` | Сам сервер (порт 3443) | `MIRRO_HOME` = родитель папки `core/` |
| `Start-Mirro.ps1` | Запуск из PowerShell, логи в `logs/` | жёстко `D:\Mirro` |
| `mirro.py`, `start.py` | Старые запускаторы, жёстко `D:\Mirro` | — |

## Как писать код?

- Принципы: **структурное программирование** (один выход из функции, без `continue`),
  маленькие функции 2–3 строки, декораторы — только там где реально нужно (см. `LINTER.md`).
- Порядок маршрутизации `try_*` в ядре и реестр функций — см. `CODE_MAP.md`.

## Проверки

```bash
python tools/check_duplicates.py --min-lines 6   # кандидаты в дубли (без шума main/setUp)
python tools/check_single_return.py              # «один return, без continue» по LINTER.md
python -m pytest tests -q -p no:cacheprovider    # тесты (unittest discover на 3.14 зависает)
python scripts/build_mirro.py --check            # сборка: файлы, компиляция, smoke
```
