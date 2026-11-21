# -*- coding: utf-8 -*-
"""Граф понятий из англоязычных определений.

Определения в algos/english_kb.py почти всегда содержат сравнение:
«… and it differs from a fissure, …», «… in contrast to X …». Это готовые
рёбра между понятиями — 1900+ штук. Здесь они превращаются в граф, по
которому можно «думать»: активировать понятие из вопроса и разойтись по
соседям на 1–2 шага.

Граф строится в памяти при импорте (быстро: только регулярные выражения
по текстам определений) и не пишет на диск.

Запуск проверки:  python algos/concept_graph.py память
"""
import re
import sys
from functools import lru_cache

from algos.english_kb import _EN_KB

_DIFFERS = re.compile(r"it differs from\s+(?:a|an|the)?\s*([a-z][a-z _-]{2,40})", re.I)
_CONTRAST = re.compile(r"in contrast to\s+(?:a|an|the)?\s*([a-z][a-z _-]{2,40})", re.I)
_UNLIKE = re.compile(r"unlike\s+(?:a|an|the)?\s*([a-z][a-z _-]{2,40})", re.I)

_STOP = {"which", "that", "it", "and", "or", "but", "the", "a", "an", "its", "his",
         "her", "their", "this", "these", "those", "one", "ones", "such", "other"}


def _aliases():
    """Индекс алиасов: слово/фраза -> тема. Один return: dict."""
    index = {}
    for topic in _EN_KB:
        index.setdefault(topic.lower(), topic)
        index.setdefault(topic.lower().replace("_", " "), topic)
    return index


_ALIASES = _aliases()


def _resolve(raw):
    """Приводит упоминание к теме базы. Один return: str/None."""
    phrase = " ".join(word for word in re.split(r"[^a-zа-яё _-]+", raw.lower()).copy() if word)
    phrase = re.sub(r"\s+", " ", phrase).strip(" -_")
    words = [word for word in phrase.split() if word not in _STOP]
    candidate = None
    while words:
        attempt = " ".join(words)
        if attempt in _ALIASES:
            candidate = _ALIASES[attempt]
            break
        words.pop()
    return candidate


def _neighbours_of(topic):
    """Соседи понятия по тексту определения. Один return: list."""
    text = _EN_KB.get(topic) or ""
    found = []
    for pattern in (_DIFFERS, _CONTRAST, _UNLIKE):
        for match in pattern.finditer(text):
            target = _resolve(match.group(1))
            if target and target != topic and target not in found:
                found.append(target)
    return found


def _ru_labels():
    """Русская подпись понятия: ключ моста или имя из описания. Один return: dict."""
    from algos.ru_bridge import RU_KEYS, _TEXT_KEYS

    labels = {topic: keys[0] for topic, keys in RU_KEYS.items() if keys}
    for name, topic in _TEXT_KEYS.items():
        labels.setdefault(topic, name)
    return labels


def _ru_text(topic):
    """Русский текст понятия: описание или запись module_knowledge. Один return: str."""
    from algos.ru_bridge import ru_definition

    return ru_definition(topic) or ""


VOWELS = "аеёиоуыэюя"
# Только падежные окончания, а не произвольные буквы: «масс» + «ива» из
# «массива» — это уже другое слово, а не форма от «массы».
CASE_ENDINGS = ("ыми", "ими", "ями", "ами", "ов", "ев", "ам", "ям", "ах", "ях",
                "ой", "ей", "ом", "ем", "ий", "ый", "ых", "их", "им", "ая", "яя",
                "ое", "ее", "ые", "ие", "ую", "юю", "ею", "й", "а", "я", "у", "ю",
                "е", "ы", "и", "о", "")


@lru_cache(maxsize=8192)
def _label_pattern(label):
    """Шаблон упоминания подписи с учётом падежного окончания.

    Основой считается подпись без конечной гласной: «забота» → «забот».
    Раньше отрезался последний символ независимо от буквы, и «забор»
    находился внутри «заботы» — отсюда ребро «любовь → забор».
    Один return: pattern."""
    base = _label_base(label)
    tail = "|".join(re.escape(end) for end in CASE_ENDINGS)
    return re.compile(r"(?<![а-яё])%s(?:%s)(?![а-яё])" % (re.escape(base), tail))


def _label_base(label):
    """Основа подписи: без конечных гласных. Один return: str.

    «данные» → «данн», «функция» → «функц»: окончания приклеиваются уже
    в шаблоне, иначе «данных» не находится от «данные».
    """
    base = (label or "").lower().rstrip(VOWELS)
    return base if len(base) >= 3 else (label or "").lower()


def _label_patterns(labels):
    """Основы и шаблоны подписей: считаются один раз, а не на каждую пару.
    Один return: list троек (понятие, основа, pattern)."""
    return [(other, _label_base(label), _label_pattern(label))
            for other, label in labels.items() if len(label) >= 4]


def _ru_neighbours(topic, patterns):
    """Соседи по русскому тексту: упомянутые русские подписи. Один return: list.

    Сначала дешёвая проверка «основа входит в текст», и только потом регулярное
    выражение с границами слова: без этого граф собирался двенадцать секунд.
    """
    text = (_ru_text(topic) or "").lower()
    found = []
    if text:
        for other, base, pattern in patterns:
            if other != topic and base in text and pattern.search(text):
                found.append(other)
    return found[:8]


def _module_entries():
    """Понятия учебных модулей: ключ и текст. Один return: dict."""
    from algos.module_knowledge import _KNOWLEDGE

    return _KNOWLEDGE


def _module_node(key, entry):
    """Узел графа для записи модуля: английская тема, если запись её дублирует.

    Многие записи модулей хранятся под тем же ключом, что и английская тема
    («binary_search» с русским названием «бинарный поиск»). Такая запись — не
    отдельное понятие: её рёбра должны лежать на узле темы, иначе вопрос
    «какие связи у бинарного поиска» отвечает «связей нет». Записи без
    английской темы остаются отдельными узлами с подчёркиванием.
    """
    topic = (entry.get("topic") or key).strip()
    if key in _EN_KB:
        return key
    return "_" + topic


def _module_edges():
    """Рёбра между понятиями модулей по упоминаниям в их же текстах.

    В модулях 385 записей, и текст одной часто называет другую («бинарный
    поиск работает по массиву»). Это тот же слой упоминаний, что и для
    английских тем.
    """
    entries = {}
    for key, entry in _module_entries().items():
        topic = (entry.get("topic") or key).strip()
        if topic:
            entries[topic.lower()] = _module_node(key, entry)
    # Упоминание ищем целым словом: «алгоритме» — это «алгоритм», а вот
    # «алгоритм» не должен давать ложное ребро к «ритм» изнутри слова
    patterns = [(target, _label_base(label), _label_pattern(label))
                for label, target in entries.items() if len(label) >= 4]
    edges = {}
    for key, entry in _module_entries().items():
        node = _module_node(key, entry)
        text = ((entry.get("what") or "") + " " + (entry.get("ex") or "")).lower()
        found = []
        for target, base, pattern in patterns:
            if target != node and base in text and pattern.search(text):
                found.append(target)
        if found:
            edges[node] = list(dict.fromkeys(found))[:8]
    return edges


def build_edges():
    """Два слоя рёбер: противопоставления и упоминания. Один return: tuple.

    Противопоставление — оборот «it differs from» в английском определении.
    Упоминание — русская подпись другого понятия внутри русского описания,
    плюс перекрёстные упоминания между понятиями учебных модулей.
    Слои разные по смыслу, поэтому и хранятся отдельно.
    """
    contrast = {}
    mention = {}
    patterns = _label_patterns(_ru_labels())
    for topic in _EN_KB:
        hard = _neighbours_of(topic)
        soft = [name for name in _ru_neighbours(topic, patterns) if name not in hard]
        if hard:
            contrast[topic] = hard
        if soft:
            mention[topic] = soft
    for node, targets in _module_edges().items():
        known = [name for name in mention.get(node, []) if name not in targets]
        mention[node] = list(dict.fromkeys(known + targets))
    return contrast, mention


EDGES_CONTRAST, EDGES_MENTION = build_edges()


def _merge_layers(first, second):
    """Склеивает два слоя рёбер без повторов. Один return: dict."""
    merged = {}
    for topic in list(first) + [name for name in second if name not in first]:
        merged[topic] = list(dict.fromkeys(list(first.get(topic, [])) + list(second.get(topic, []))))
    return merged


EDGES = _merge_layers(EDGES_CONTRAST, EDGES_MENTION)


def neighbours(topic, depth=1):
    """Соседи понятия на заданной глубине. Один return: list."""
    seen = []
    frontier = [topic]
    for _ in range(max(depth, 1)):
        next_frontier = []
        for node in frontier:
            for target in EDGES.get(node, []):
                if target not in seen and target != topic:
                    seen.append(target)
                    next_frontier.append(target)
        frontier = next_frontier
    return seen


def activate(seeds, depth=2):
    """Активация от понятий-входов: [(тема, вес)]. Один return: list."""
    scores = {}
    for topic, weight in seeds:
        if topic in _EN_KB:
            scores[topic] = scores.get(topic, 0.0) + float(weight)
    frontier = list(scores)
    for level in range(max(depth, 0)):
        decay = 1.0 / (2 ** (level + 1))
        next_frontier = []
        for node in frontier:
            for target in EDGES.get(node, []):
                if target in _EN_KB:
                    scores[target] = scores.get(target, 0.0) + decay
                    next_frontier.append(target)
        frontier = next_frontier
    ranked = sorted(scores.items(), key=lambda pair: (-pair[1], pair[0]))
    return ranked


def main(argv):
    """Проверка из командной строки. Один return: int."""
    query = (argv[0] if argv else "memory").strip().lower()
    topic = _ALIASES.get(query)
    print("тема:", topic)
    if topic:
        print("соседи:", neighbours(topic, depth=1)[:12])
        print("активация на 2 шага:", [name for name, _ in activate([(topic, 1.0)], depth=2)][:12])
    print("всего рёбер:", len(EDGES), "| понятий с рёбрами:", len(EDGES))
    return 0 if topic else 1


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
