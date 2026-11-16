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
    """Русская подпись понятия: первый ключ моста. Один return: dict."""
    from algos.ru_bridge import RU_KEYS

    return {topic: keys[0] for topic, keys in RU_KEYS.items() if keys}


def _ru_text(topic):
    """Русский текст понятия: описание или запись module_knowledge. Один return: str."""
    from algos.ru_bridge import ru_definition

    return ru_definition(topic) or ""


def _label_pattern(label):
    """Шаблон упоминания подписи с учётом окончания, но без склейки слов.
    Один return: pattern."""
    stem = label.lower()
    if len(stem) >= 5:
        stem = stem[:-1]
    return re.compile(r"(?<![а-яё])%s[а-яё]{0,3}(?![а-яё])" % re.escape(stem))


def _ru_neighbours(topic, labels):
    """Соседи по русскому тексту: упомянутые русские подписи. Один return: list."""
    text = (_ru_text(topic) or "").lower()
    found = []
    for other, label in labels.items():
        if other != topic and len(label) >= 4 and _label_pattern(label).search(text):
            found.append(other)
    return found[:8]


def build_edges():
    """Два слоя рёбер: противопоставления и упоминания. Один return: tuple.

    Противопоставление — оборот «it differs from» в английском определении.
    Упоминание — русская подпись другого понятия внутри русского описания.
    Слои разные по смыслу, поэтому и хранятся отдельно.
    """
    contrast = {}
    mention = {}
    labels = _ru_labels()
    for topic in _EN_KB:
        hard = _neighbours_of(topic)
        soft = [name for name in _ru_neighbours(topic, labels) if name not in hard]
        if hard:
            contrast[topic] = hard
        if soft:
            mention[topic] = soft
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
