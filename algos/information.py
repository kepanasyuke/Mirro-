# -*- coding: utf-8 -*-
"""Теория информации Шеннона: энтропия, взаимная информация, PMI, канал.

Всё считается по счётчикам, без внешних библиотек: только `math.log2`.
Нужно для собственных решений Мирро: сколько неопределённости в выборе понятия
(энтропия), насколько слово связано с понятием (PMI), сколько удивления в ответе
(собственная информация) и какова пропускная способность шумного канала.

Один return на функцию, без побочных эффектов.
"""
import math


def _total(counts):
    """Сумма счётчиков; пустой или неверный вход даёт 0."""
    return sum(counts.values()) if isinstance(counts, dict) and counts else 0


def probabilities(counts):
    """Нормированные вероятности из счётчиков; пустой вход даёт пустой словарь."""
    total = _total(counts)
    result = {}
    if total > 0:
        result = {key: value / total for key, value in counts.items() if value > 0}
    return result


def entropy(counts):
    """Энтропия Шеннона в битах: H = -Σ p log2 p."""
    result = -sum(p * math.log2(p) for p in probabilities(counts).values())
    return result


def surprise(probability):
    """Собственная информация -log2(p): сколько удивления в событии."""
    result = -math.log2(probability) if 0 < probability <= 1 else 0.0
    return result


def joint_counts(pairs):
    """Совместные счётчики пар наблюдений."""
    result = {}
    for first, second in pairs or ():
        key = (first, second)
        result[key] = result.get(key, 0) + 1
    return result


def marginal(counts, index):
    """Маргинальные счётчики по позиции 0 или 1 в словаре пар."""
    result = {}
    for key, value in (counts or {}).items():
        item = key[index] if isinstance(key, tuple) and len(key) > index else key
        result[item] = result.get(item, 0) + value
    return result


def mutual_information(pairs):
    """Взаимная информация I(X;Y) в битах по парам наблюдений."""
    joint = probabilities(joint_counts(pairs))
    rows = probabilities(marginal(joint_counts(pairs), 0))
    columns = probabilities(marginal(joint_counts(pairs), 1))
    result = 0.0
    for (first, second), pxy in joint.items():
        px, py = rows.get(first, 0.0), columns.get(second, 0.0)
        if pxy > 0 and px > 0 and py > 0:
            result += pxy * math.log2(pxy / (px * py))
    return result


def pmi(count_pair, count_first, count_second, total):
    """Точечная взаимная информация пары: log2(p(x,y) / (p(x)p(y)))."""
    result = 0.0
    if count_pair > 0 and count_first > 0 and count_second > 0 and total > 0:
        result = math.log2((count_pair * total) / (count_first * count_second))
    return result


def cross_entropy(actual, predicted):
    """Кросс-энтропия H(p,q): цена предсказания q при верном p."""
    left, right = probabilities(actual), probabilities(predicted)
    result = 0.0
    for key, p in left.items():
        q = right.get(key, 0.0)
        result += p * (-math.log2(q)) if q > 0 else float("inf")
    return result


def kl_divergence(actual, predicted):
    """Дивергенция Кульбака–Лейблера D(p||q) в битах."""
    left, right = probabilities(actual), probabilities(predicted)
    result = 0.0
    for key, p in left.items():
        q = right.get(key, 0.0)
        result += p * math.log2(p / q) if q > 0 else float("inf")
    return result


def channel_capacity_bsc(error):
    """Пропускная способность двоичного симметричного канала: 1 - H(error)."""
    result = 1.0 - entropy({"ok": 1.0 - error, "bad": error}) if 0 <= error <= 1 else 0.0
    return max(result, 0.0)


def huffman_lengths(counts):
    """Длины кодов Хаффмана по частотам: сколько бит нужно на символ."""
    items = [(value, [key]) for key, value in (counts or {}).items() if value > 0]
    lengths = {key: 0 for key, _ in (counts or {}).items()}
    if len(items) == 1:
        lengths[items[0][1][0]] = 1
    for _ in range(max(len(items) - 1, 0)):
        items.sort(key=lambda pair: pair[0])
        left, right = items.pop(0), items.pop(0)
        for key in left[1] + right[1]:
            lengths[key] = lengths.get(key, 0) + 1
        items.append((left[0] + right[0], left[1] + right[1]))
    return lengths


def average_code_length(counts):
    """Средняя длина кода Хаффмана в битах на символ."""
    probs = probabilities(counts)
    lengths = huffman_lengths(counts)
    result = sum(p * lengths.get(key, 0) for key, p in probs.items())
    return result
