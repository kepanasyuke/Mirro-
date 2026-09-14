#!/usr/bin/env python3
"""Список всех возможных улучшений Mirro - аудит текущего состояния."""
import sys, json
from pathlib import Path

MIRRO = Path(r"D:\Mirro")

# ================= ФИНАЛЬНЫЙ СПИСОК УЛУЧШЕНИЙ (30+) =================
IMPROVEMENTS = [
    # --- Поиск и семантика ---
    ("01", "Стемминг русских слов", "high", "Нормализация wordforms: налога/налогу/налогом → налог", "semantics", "done"),
    ("02", "BM25 полноценный", "low", "Использовать все параметры BM25 (k1, b, dl)", "search", "partial"),
    ("03", "Фразовое индексирование", "medium", "Индексировать биграммы для ngram поиска", "search", "partial"),
    ("04", "Остановочные слова", "low", "Фильтр частоупотребимых слов (и, в, на, с)", "search", "pending"),
    ("05", "Важность кластера в поиске", "medium", "Взвешивать результаты по приоритету кластера", "search", "partial"),
    # --- Генерация ---
    ("06", "Abstractive textrank", "medium", "Не просто извлекать, а переписывать предложения", "generation", "partial"),
    ("07", "Слияние ответов по смыслу", "high", "Убирать дублирующиеся абзацы по cosine similarity", "generation", "done"),
    ("08", "Контекстный перцептрон", "medium", "Учитывать кластер в векторе признаков перцептрона", "generation", "partial"),
    # --- Оценка качества ---
    ("09", "Self-eval через BLEU", "medium", "BLEU сходство ответа с эталоном из базы", "eval", "pending"),
    ("10", "Оценка тональности ответа", "low", "Базовая тональность по словарю (позитив/негатив)", "eval", "pending"),
    ("11", "Детектор галлюцинаций", "high", "Проверять факты ответа по TF-IDF базе", "eval", "done"),
    # --- Обучение ---
    ("12", "Автономный планировщик обучения", "high", "Каждые 60 мин: самовопросы + обновление веслов", "learning", "in_progress"),
    ("13", "Реплеи-буффер feedback", "medium", "Переигрывать оценённые пользователем вопросы", "learning", "partial"),
    ("14", "Экспоненциальное затухание boost", "low", "Старые бусты меньше влияют", "learning", "pending"),
    ("15", "Перцептрон → 2 слоя", "medium", "Добавить скрытый слой (MLP)", "learning", "pending"),
    ("16", "Пакетное обучение перцептрона", "medium", "Обучать по батчам из history", "learning", "pending"),
    # --- Классификация ---
    ("17", "Naive Bayes мульти-класс", "done", "Уже есть: 6 кластеров", "classify", "done"),
    ("18", "Калибровка вероятностей NB", "low", "Откалибровать априорные вероятности", "classify", "pending"),
    # --- Эмбеддинги ---
    ("19", "Skip-gram эмбеддинги", "medium", "Собственные CBOW/Skip-gram векторов слов", "embeddings", "pending"),
    ("20", "Sentence embeddings", "high", "Усреднённый вектор предложения для близости", "embeddings", "done"),
    ("21", "Векторный поиск (faiss-лайт)", "medium", "Индексировать векторы для быстрого поиска", "embeddings", "pending"),
    # --- Интерфейс ---
    ("22", "Вкладка Алгоритмы (живая метрика)", "done", "Показывает все метрики алгоритмов", "ui", "done"),
    ("23", "Вкладка История диалогов", "medium", "Сохранять и просматривать историю чатов", "ui", "done"),
    ("24", "Тёмная/светлая темы", "low", "Переключатель темы в UI", "ui", "pending"),
    ("25", "Экспорт знаний в PDF/MD", "medium", "Скачивать дайджест базы знаний", "ui", "pending"),
    ("26", "Прогресс-бар обучения", "low", "Показывать прогресс self-learn", "ui", "pending"),
    ("27", "Статистика ТОП-вопросов", "low", "Какие вопросы чаще задают Mirro", "ui", "pending"),
    # --- Данные ---
    ("28", "Дизайн/креатив кластер", "high", "Загрузить SVG/дизайн датасеты", "data", "pending"),
    ("29", "Math кластер (200k+ задач)", "high", "Загрузить ORCA-math", "data", "pending"),
    ("30", "Knowledge кластер (википедия)", "medium", "Загрузить раздел Википедии RU", "data", "pending"),
    ("31", "Код-кластер (The Stack)", "medium", "Загрузить образец The Stack", "data", "pending"),
    ("32", "Дедупликация данных", "medium", "Убрать дубли в обработанных кластерах", "data", "pending"),
    # --- Инфраструктура ---
    ("33", "Автостарт при запуске Windows", "low", "Опциональный автозапуск Mirro", "infra", "pending"),
    ("34", "Векторизованный TF-IDF", "medium", "Ускорить поиск через структуры словарь", "infra", "done"),
    ("35", "Кэширование частых запросов", "high", "Ответы на частые вопросы из кэша", "infra", "done"),
    ("36", "Логирование в JSONL (аудит)", "done", "Все вызовы сохраняются в calls.jsonl", "infra", "done"),
    ("37", "Бэкап модели (ai_state)", "medium", "Сохранять веса перцептрона в файл", "infra", "pending"),
    ("38", "Self-health check", "low", "Мониторить и перезапускать при падении", "infra", "pending"),
]

# ===== Вывод =====
print("=" * 72)
print("  MIRRO — АУДИТ И СПИСОК УЛУЧШЕНИЙ")
print("=" * 72)
print(f"  Всего задач: {len(IMPROVEMENTS)}")
print()

from collections import Counter
by_status = Counter(i[4] for i in IMPROVEMENTS)
by_area = Counter(i[5] for i in IMPROVEMENTS)

print("  Статусы:")
for s, c in by_status.most_common():
    print(f"    {s:12} {c}")
print()
print("  Области:")
for a, c in by_area.most_common():
    print(f"    {a:12} {c}")
print()
print("  Осталось сделать:", sum(1 for i in IMPROVEMENTS if i[4] not in ("done", "in_progress")))
print("  В процессе:", sum(1 for i in IMPROVEMENTS if i[4] == "in_progress"))
print("  Сделано:", sum(1 for i in IMPROVEMENTS if i[4] == "done"))
print()

# Save to file for mind map
out = MIRRO / "data" / "improvements.json"
out.write_text(json.dumps(IMPROVEMENTS, ensure_ascii=False, indent=2), "utf-8")
print(f"  Сохранено в: {out}")