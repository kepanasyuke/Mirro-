# -*- coding: utf-8 -*-
"""Эмбеддинги понятий на чистом Python: PPMI по совместной встречаемости.

Зачем: поиск в Mirro сравнивает слова буквально (TF-IDF/BM25), поэтому
«кошка» и «собака» для него так же далеки, как «кошка» и «алгоритм».
PPMI-векторы дают близость по контексту: слова, встречающиеся в похожих
окружениях, получают близкие векторы.

Реализация намеренно простая и без зависимостей:
1. считаем совместную встречаемость слов в окне;
2. переводим счётчики в PPMI (positive pointwise mutual information);
3. сравниваем векторы косинусом.

Модель разреженная (слово → {контекст: вес}), поэтому её можно сохранять
в JSON и держать в памяти без numpy.
"""
import json
import math
import re as _re

_TOKEN = _re.compile(r"[а-яёa-z]{3,}")
DEFAULT_WINDOW = 2
DEFAULT_MAX_VOCAB = 3000
DEFAULT_MIN_COUNT = 2


def tokenize(text):
    """Слова текста в нижнем регистре (буквы, длина 3+). Один return: list."""
    return _TOKEN.findall((text or "").lower())


def _count_pairs(tokens, window):
    """Счётчики пар «слово ↔ сосед» в окне. Один return: dict."""
    pairs = {}
    size = len(tokens)
    for i, word in enumerate(tokens):
        low = max(0, i - window)
        high = min(size, i + window + 1)
        for j in range(low, high):
            if j != i:
                other = tokens[j]
                pairs[(word, other)] = pairs.get((word, other), 0) + 1
    return pairs


def build_vocabulary(documents, max_vocab=DEFAULT_MAX_VOCAB, min_count=DEFAULT_MIN_COUNT):
    """Словарь самых частых слов корпуса. Один return: list."""
    freq = {}
    for tokens in documents:
        for word in tokens:
            freq[word] = freq.get(word, 0) + 1
    kept = [(count, word) for word, count in freq.items() if count >= min_count]
    kept.sort(reverse=True)
    return [word for _count, word in kept[:max_vocab]]


def _ppmi(pair_counts, word_totals, context_totals, total):
    """PPMI одного слова по его счётчикам. Один return: dict."""
    vector = {}
    for (word, context), count in pair_counts.items():
        pmi = math.log((count * total) / (word_totals[word] * context_totals[context]))
        if pmi > 0:
            vector[context] = pmi
    return vector


def train(documents, window=DEFAULT_WINDOW, max_vocab=DEFAULT_MAX_VOCAB,
          min_count=DEFAULT_MIN_COUNT):
    """Обучает PPMI-модель на списке документов (списков токенов).
    Один return: dict {window, vectors: {word: {context: weight}}}."""
    vocab = set(build_vocabulary(documents, max_vocab, min_count))
    pairs = {}
    word_totals = {}
    context_totals = {}
    total = 0
    for tokens in documents:
        filtered = [word for word in tokens if word in vocab]
        for (word, context), count in _count_pairs(filtered, window).items():
            if word in vocab and context in vocab:
                pairs[(word, context)] = pairs.get((word, context), 0) + count
                word_totals[word] = word_totals.get(word, 0) + count
                context_totals[context] = context_totals.get(context, 0) + count
                total += count
    vectors = {}
    if total > 0:
        by_word = {}
        for (word, context), count in pairs.items():
            by_word.setdefault(word, {})[(word, context)] = count
        for word, rows in by_word.items():
            vectors[word] = _ppmi(rows, word_totals, context_totals, total)
    return {"window": window, "vectors": vectors}


def train_from_texts(texts, **kwargs):
    """Обучает модель по списку строк. Один return: dict."""
    return train([tokenize(text) for text in texts], **kwargs)


def cosine(left, right):
    """Косинус двух разреженных векторов. Один return: float 0..1."""
    if not left or not right:
        return 0.0
    keys = set(left) & set(right)
    dot = sum(left[key] * right[key] for key in keys)
    norm_left = math.sqrt(sum(value * value for value in left.values()))
    norm_right = math.sqrt(sum(value * value for value in right.values()))
    return dot / (norm_left * norm_right) if norm_left and norm_right else 0.0


def similarity(model, first, second):
    """Близость двух слов по обученной модели. Один return: float 0..1."""
    vectors = model.get("vectors", {}) if isinstance(model, dict) else {}
    return cosine(vectors.get((first or "").lower(), {}),
                  vectors.get((second or "").lower(), {}))


def text_vector(model, text):
    """Средний PPMI-вектор слов текста. Один return: dict."""
    vectors = model.get("vectors", {}) if isinstance(model, dict) else {}
    total = {}
    used = 0
    for word in tokenize(text):
        vector = vectors.get(word)
        if vector:
            used += 1
            for key, value in vector.items():
                total[key] = total.get(key, 0.0) + value
    if used:
        total = {key: value / used for key, value in total.items()}
    return total


def text_similarity(model, first, second):
    """Смысловая близость двух текстов (средние векторы). Один return: float 0..1."""
    return cosine(text_vector(model, first), text_vector(model, second))


def save(model, path):
    """Сохраняет модель в JSON. Один return: bool."""
    ok = False
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps(model, ensure_ascii=False), encoding="utf-8")
        ok = True
    except OSError:
        ok = False
    return ok


def load(path):
    """Загружает модель из JSON; при ошибке — пустая модель. Один return: dict."""
    model = {"vectors": {}}
    try:
        model = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        model = {"vectors": {}}
    return model
