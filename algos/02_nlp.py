# -*- coding: utf-8 -*-
"""
Mirro Algorithms — 02 · NLP (10 алгоритмов)
Чистый Python, без numpy.
"""

import re, math
from collections import Counter, defaultdict

STOP_RU = {"и", "в", "на", "с", "по", "за", "от", "до", "из", "у", "для", "о",
           "не", "ни", "все", "это", "как", "так", "что", "кто", "где", "когда",
           "к", "об", "под", "над", "перед", "между", "чтобы", "потому", "а", "но",
           "или", "если", "же", "бы", "ли", "то", "уже", "ещё", "только"}


def tokenize(text):
    """Токенизация с фильтром стоп-слов. Один return: list[str]."""
    if not text:
        return []
    words = re.findall(r"[а-яёa-z0-9]+", str(text).lower())
    return [w for w in words if w not in STOP_RU and len(w) > 1]


def ngrams(tokens, n=2):
    """N-граммы."""
    return [tuple(tokens[i:i + n]) for i in range(len(tokens) - n + 1)]


def word_freq(tokens):
    """Частотный словарь."""
    return Counter(tokens)


_STEM_RULES = [
    ("ами", "а"), ("ями", "я"), ("ого", ""), ("его", ""), ("ому", ""),
    ("ему", ""), ("ых", ""), ("их", ""), ("ый", ""), ("ий", ""),
    ("ая", "а"), ("яя", "я"), ("ое", "о"), ("ее", "е"), ("ые", "ы"),
    ("ие", "и"), ("а", ""), ("я", ""), ("о", ""), ("е", ""), ("ы", ""),
    ("и", ""), ("у", ""), ("ю", ""), ("ет", "ть"), ("ит", "ть"),
    ("ут", "ть"), ("ют", "ть"), ("ал", "ть"), ("ил", "ть"),
    ("лив", "лив"), ("чив", "чив"), ("еньк", "еньк"), ("оньк", "оньк"),
]


def _apply_stem_rule(word):
    """Подбирает первое подходящее правило стемминга. Один return: str."""
    result = word
    for suf, rep in _STEM_RULES:
        if word.endswith(suf) and len(word) - len(suf) >= 3:
            result = word[: -len(suf)] + rep
            break
    return result


def russian_stem(word):
    """Лёгкий стеммер русского (Porter-lite). Один return: str."""
    base = word
    if len(word) >= 5:
        base = _apply_stem_rule(word)
    return base


def stem_document(text):
    """Стемминг всего текста (с кэшем)."""
    cache = {}

    def st(w):
        if w not in cache:
            cache[w] = russian_stem(w)
        return cache[w]

    return [st(w) for w in tokenize(text)]


def tfidf(docs):
    """TF-IDF по списку документов (список строк → список {слово: вес})."""
    N = len(docs)
    tokenized = [tokenize(d) for d in docs]
    df = Counter()
    for toks in tokenized:
        for w in set(toks):
            df[w] += 1
    out = []
    for toks in tokenized:
        tf = Counter(toks)
        total = len(toks) or 1
        vec = {}
        for w, c in tf.items():
            idf = math.log((N + 1) / (1 + df[w])) + 1
            vec[w] = (c / total) * idf
        out.append(vec)
    return out


class MiniLemmatizer:
    """Мини-лемматизатор: словарь-исключения + стемминг."""

    EXC = {
        "люди": "человек", "детей": "ребенок", "дети": "ребенок",
        "лучше": "хорошо", "хуже": "плохо", "есть": "быть",
        "могу": "мочь", "может": "мочь", "могут": "мочь",
        "иду": "идти", "идет": "идти", "идут": "идти",
        "была": "быть", "было": "быть", "были": "быть",
        "первый": "один", "первая": "один", "первое": "один",
        "себя": "себя", "нибудь": "нибудь", "лишь": "лишь",
    }

    def lemma(self, word):
        """Лемма слова: словарь-исключение, иначе стемминг. Один return: str."""
        exc = self.EXC.get(word)
        result = exc if exc is not None else russian_stem(word)
        return result

    def lemmatize(self, text):
        return [self.lemma(w) for w in tokenize(text)]


POS_WORDS = {"хорошо", "отлично", "прекрасно", "круто", "замечательно", "спасибо",
             "успех", "супер", "нравится", "победа", "лучший", "класс", "здорово",
             "люблю", "рад", "рада", "приятно", "помогло"}
NEG_WORDS = {"плохо", "ужасно", "проблема", "ошибка", "провал", "грустно",
             "ненавижу", "негатив", "катастрофа", "фейл", "худший", "сломал",
             "бесит", "раздражает", "неприятно", "жаль"}


def sentiment(text):
    """Простая тональность по словарю позитив/негатив.
    Один return: int (положительный — позитив, отрицательный — негатив)."""
    w = set(tokenize(text))
    score = len(w & POS_WORDS) - len(w & NEG_WORDS)
    return score


def keyword_extract(text, top_n=5):
    """Ключевые слова через TF внутри документа. Один return: list."""
    toks = tokenize(text)
    result = []
    if toks:
        n = len(toks)
        top = Counter(toks).most_common(top_n)
        result = [(w, c / n) for w, c in top]
    return result


def similarity_jaccard(a, b):
    """Сходство Жаккара двух текстов (1.0 при полном совпадении,
    0 при пустых/непересекающихся). Один return: float."""
    A, B = set(tokenize(a)), set(tokenize(b))
    score = 0.0
    if A and B:
        score = len(A & B) / len(A | B)
    elif not A and not B:
        score = 1.0  # оба пусты — считаем идентичными
    return score


if __name__ == "__main__":
    t = "Люди покупают хорошие машины. Каждый выбирает лучшую модель."
    print("tokens:", tokenize(t)[:8])
    print("stems:", [russian_stem(w) for w in ["машины", "машину", "машиной"]])
    lemm = MiniLemmatizer()
    print("lemma:", lemm.lemmatize("люди идут покупать машины деньги"))
    print("sentiment:", sentiment("отлично получилось, спасибо"))
    print("keywords:", keyword_extract(t))