# -*- coding: utf-8 -*-
"""Хеди Ламарр: псевдослучайная перестройка частоты и расширение спектра.

Идея патента Ламарр–Антейл (1942) простая: передатчик и приёмник прыгают по
каналам по одной и той же псевдослучайной последовательности, поэтому чужой
не может ни подслушать, ни заглушить передачу. Здесь то же самое в чистом виде:
регистр сдвига с линейной обратной связью (LFSR) даёт последовательность,
она выбирает каналы, а расширение спектра перемешивает биты с кодом.

Один return на функцию, без побочных эффектов.
"""


def lfsr(seed, taps=(3, 2), length=15):
    """Псевдослучайные биты из регистра сдвига: taps — позиции обратной связи."""
    width = max(max(taps) + 1, 2)
    state = [(seed >> index) & 1 for index in range(width)]
    result = []
    for _ in range(max(int(length), 0)):
        feedback = 0
        for tap in taps:
            feedback ^= state[tap % width]
        result.append(state[-1])
        state = [feedback] + state[:-1]
    return result


def period(seed=1, taps=(3, 2), limit=64):
    """Длина цикла последовательности до возврата в исходное состояние."""
    width = max(max(taps) + 1, 2)
    start = [(seed >> index) & 1 for index in range(width)]
    state = list(start)
    result = 0
    for step in range(1, limit + 1):
        feedback = 0
        for tap in taps:
            feedback ^= state[tap % width]
        state = [feedback] + state[:-1]
        if state == start:
            result = step
            break
    return result


def hop_channels(channels, bits, width=3):
    """Каналы передачи: каждые width бит выбирают канал из списка."""
    names = list(channels or ())
    result = []
    if names:
        for start in range(0, len(bits or ()), width):
            block = (bits or ())[start:start + width]
            index = 0
            for bit in block:
                index = index * 2 + int(bit)
            result.append(names[index % len(names)])
    return result


def hop_indexes(channels, bits, width=3):
    """То же, но номерами каналов — удобно сравнивать приёмник и передатчик."""
    names = list(channels or ())
    result = []
    if names:
        for start in range(0, len(bits or ()), width):
            block = (bits or ())[start:start + width]
            index = 0
            for bit in block:
                index = index * 2 + int(bit)
            result.append(index % len(names))
    return result


def spread(bits, code):
    """Расширение спектра: каждый бит складывается по модулю 2 с кодом."""
    marks = list(code or ())
    result = []
    if marks:
        for index, bit in enumerate(bits or ()):
            result.append(int(bit) ^ int(marks[index % len(marks)]))
    return result


def despread(chips, code):
    """Обратное расширение: та же операция возвращает исходные биты."""
    return spread(chips, code)


def correlate(first, second):
    """Доля совпавших позиций: 1.0 — код совпал, около 0.5 — чужой."""
    left, right = list(first or ()), list(second or ())
    size = min(len(left), len(right))
    result = 0.0
    if size:
        same = sum(1 for index in range(size) if int(left[index]) == int(right[index]))
        result = same / size
    return result
