# -*- coding: utf-8 -*-
"""Поиск понятия по запросу: сначала язык слова, потом общий реестр.

Русский вопрос может содержать латинское имя («как работает mean»). Тогда искать
надо именно это имя в английской базе, иначе грубый русский алиас («работа»)
перебьёт верное понятие. Порядок такой:

  1) латинское слово запроса, совпавшее с именем понятия — самый сильный признак;
  2) общий поиск `algos.concepts.find` (русские и английские алиасы);
  3) ничего не нашли — вызывающий может спросить выученные из опыта имена.
"""
import re

LATIN = re.compile(r"[A-Za-z][A-Za-z0-9_]{2,}")
CYRILLIC = re.compile(r"[\u0400-\u04FF]")

# Служебные слова не могут быть именем понятия: без этого «what is quark?»
# находило понятие по алиасу «what», если самого слова в базе нет.
STOP = frozenset((
    "what", "who", "which", "how", "why", "when", "where", "is", "are", "was",
    "the", "a", "an", "of", "in", "on", "about", "does", "do", "and", "or",
    "it", "this", "that", "tell", "me", "как", "что", "чем", "почему", "кто",
    "где", "когда", "это", "и", "в", "на", "о", "про", "от", "для", "мне",
    "какие", "какой", "какая", "каких", "какое", "каков",
))

# Слова-связки вопроса о графе: «какие связи у графа» — тема «граф», а не «связь».
META = frozenset(("связь", "связи", "связей", "связям", "связях", "связан",
                  "связана", "связано", "связаны", "связывать", "связывают",
                  "информация", "данные", "related"))

# Окончания, которые снимаются перед поиском понятия: «графа» → «граф»,
# «музыку» → «музык» + «а». Целые слова не усекаем — «график» остаётся собой.
ENDINGS = ("ыми", "ими", "ого", "его", "ому", "ами", "ями", "ами", "ых", "их",
           "ая", "яя", "ий", "ый", "ое", "ее", "ую", "юю", "ов", "ев", "ам",
           "ям", "ах", "ях", "ой", "ей", "ом", "ем", "а", "я", "ы", "и", "у",
           "ю", "е")

WORD = re.compile(r"[а-яёА-ЯЁa-z]{3,}")


def _word_concept(registry, word):
    """Понятие по слову с учётом падежного окончания: «графа» → «граф».

    Если слово есть и как короткая русская запись («граф», «музыка»), и как
    тема с английским описанием, берём вторую: у неё есть текст и связи в
    графе, а короткая запись — только толкование из учебного модуля.
    """
    from algos import concepts
    forms = [word] + [word[:-len(end)] for end in ENDINGS
                      if word.endswith(end) and len(word) - len(end) >= 3]
    spare = None
    for base in forms:
        candidates = []
        direct = registry.get(concepts._normal(base))
        if direct is not None:
            candidates.append(direct)
        hit = concepts.find(base)
        if hit is not None:
            candidates.append(hit["concept"])
        for concept in candidates:
            if (concept.get("en") or "").strip():
                return concept
            spare = spare or concept
        if spare is not None:
            return spare
    return None


def _stems(text):
    """Основы слов для сравнения: первые четыре буквы, как в проверке ответов."""
    return {word[:4] for word in WORD.findall((text or "").lower()) if len(word) >= 4}


def _content_words(query):
    """Значимые слова запроса: без служебных и без связок вроде «связана»."""
    return [word for word in WORD.findall((query or "").lower())
            if word not in STOP and word not in META
            and not word.startswith(("связ", "отнош"))]


def _best_by_words(registry, query):
    """Понятие, чьё имя покрывает больше основ запроса.

    Одно слово не решает: «бинарного поиска» содержит «поиск» (это и линейный
    поиск, и бинарный), но только у бинарного поиска есть вторая основа.
    """
    wanted = _stems(" ".join(_content_words(query)))
    best = None
    best_score = 0
    seen = []
    for word in _content_words(query):
        concept = _word_concept(registry, word)
        if concept is None or any(concept is item for item in seen):
            continue
        seen.append(concept)
        hay = " ".join([concept.get("name") or ""] + list(concept.get("aliases") or ()))
        score = len(wanted & _stems(hay))
        richer = (score == best_score and best is not None
                  and (concept.get("en") or "").strip() and not (best.get("en") or "").strip())
        if best is None or score > best_score or richer:
            best, best_score = concept, score
    return best


def latin_terms(query):
    """Латинские слова запроса в нижнем регистре."""
    return [item.lower() for item in LATIN.findall(query or "")]


def answer_language(query):
    """Язык запроса по перевесу букв: «ru» или «la»."""
    text = query or ""
    latin = len(LATIN.findall(text))
    cyrillic = len(CYRILLIC.findall(text))
    return "ru" if cyrillic >= latin else "la"


def find(query):
    """Понятие по запросу: {concept, alias, score, via} или None."""
    from algos import concepts
    registry = concepts.build()
    result = None
    for term in latin_terms(query):
        if term in STOP:
            continue
        concept = registry.get(concepts._normal(term))
        if concept is not None and result is None:
            result = {"concept": concept, "alias": term, "score": 1.0, "via": "latin"}
    if result is None:
        # значимые слова запроса важнее совпадения по части слова: «какие связи
        # у графа» — это граф, а не понятие «связь»; «список от массива» —
        # список, а не «список перестановок»; «бинарного поиска» — бинарный
        # поиск, потому что его имя покрывает обе основы
        concept = _best_by_words(registry, query)
        if concept is not None:
            result = {"concept": concept, "alias": (concept.get("name") or ""),
                      "score": 0.9, "via": "word"}
        found = concepts.find(query)
        alias = (found.get("alias") or "").lower() if found else ""
        # длинная фраза из реестра важнее одного слова: «поиск в ширину» —
        # это обход в ширину, а не общее понятие «Поиск»
        phrase_wins = found is not None and (found.get("score") or 0) >= 0.5
        if found is not None and alias not in STOP and not alias.startswith(("связ", "отнош")):
            if result is None or phrase_wins:
                result = {"concept": found["concept"], "alias": found["alias"],
                          "score": found["score"], "via": "registry"}
    return result


def find_with_learned(query, learned_path=None):
    """То же, но последним шагом пробуются имена, выученные из опыта."""
    from algos import label_learning
    result = find(query)
    if result is None:
        name = label_learning.guess(query, learned_path)
        if name:
            from algos import concepts
            concept = concepts.build().get(concepts._normal(name))
            if concept is None:
                concept = {"id": concepts._normal(name), "name": name,
                           "title": str(name).replace("_", " ").strip(),
                           "ru": "", "en": "", "aliases": ()}
            result = {"concept": concept, "alias": name, "score": 0.5, "via": "learned"}
    return result
