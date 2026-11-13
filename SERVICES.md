# Сервисы, фоновые процессы и порты Mirro

Снято с кода 14.11.2026. Нужно, чтобы в шести параллельных ветках никто не занял
чужой порт и не запустил второй планировщик.

## Порты

| Порт | Кто слушает | Файл | Примечание |
|---|---|---|---|
| **3443** | Основной сервер Mirro (HTTP API + веб) | `core/mirro_core.py` | `MIRRO_HOST` / `MIRRO_PORT` переопределяют |
| **3444** | Vault API (секреты) | `scripts/vault.py` | Отдельный процесс, `python scripts/vault.py` |
| **3445** | Сборщик внешних данных (API над каталогом) | `scripts/collector.py` | `HOST, PORT = "127.0.0.1", 3445` |

Правило для параллельной работы: **не поднимать 3443** без необходимости — боевая
копия владельца использует именно его.

## Фоновые процессы

| Что | Где запускается | Период | Что пишет |
|---|---|---|---|
| `autonomous_learning_loop` | поток в `core/mirro_core.py` (`main`) | 3600 с (60 мин) | `models/model_state.json`, `models/knowledge_graph.pkl` |
| `scripts/self_learn.py` | отдельный процесс | `interval_hours` часов, `while True` | `data/self_learned/` |
| `scripts/qa_watch.py` | отдельный процесс | `--every` секунд | `data/qa_watch.log`, отчёт |
| `scripts/deploy_vps.sh` | cron на VPS | каждый час | `web/mirro-meysto-dashboard.html`, `data/phi_history.json` |
| `scripts/schedule_dashboard.ps1` | Планировщик Windows | каждый час | то же, локально |

## Что считается состояниями (и не коммитится)

- `models/knowledge_graph.pkl` — граф знаний + опыт
- `models/model_state.json` — перцептрон/MLP и веса
- `core/stats.json` — счётчики вызовов и `total_examples`
- `data/self_learned/`, `data/qa_*.jsonl`, `data/dialogue_memory.json`, `data/*_log.jsonl`

Всё это пересобирается или восстанавливается; в git их держать не нужно
(см. `.gitignore`).

## Как проверить, что сервер жив

```bash
curl -s http://127.0.0.1:3443/health      # без MIRRO_TOKEN в env — без авторизации
python scripts/mirro_cli.py health
```

`/health` отдаёт `total_examples`, кластеры и провайдеров; чужие ветки могут
безопасно читать его, не перезапуская сервер.
