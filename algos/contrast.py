# -*- coding: utf-8 -*-
"""Различия между понятиями: чем одно отличается от другого.

В английских определениях 1523 раза встречается «it differs from X» — это готовые
противопоставления. В русских записях их почти нет (1 из 179), поэтому цитировать
различие можно только из английского текста, честно помечая источник.

Модуль ищет в описании первого понятия упоминание второго и отдаёт сам кусок
фразы — то, что можно показать вместо выдуманного объяснения.
"""
MARKERS = ("differs from", "is the opposite of", "in contrast to", "unlike",
           "as opposed to")
STOP = (" and ", ",", ";", ".", " which ", " but ", " that ",
        " in ", " on ", " at ", " by ", " to ", " from ", " of ", " for ", " with ",
        " when ", " where ", " while ", " because ")
LIMIT = 160


def _clean(text):
    """Строка без лишних пробелов в нижнем регистре."""
    return " ".join((text or "").split()).lower()


def _target(text, start):
    """Имя, с которым сравнивают: слова после маркера до служебного знака."""
    rest = (text or "")[start:]
    cut = len(rest)
    for marker in STOP:
        position = rest.find(marker)
        if 0 <= position < cut:
            cut = position
    words = rest[:cut].strip().split()[:4]
    while words and words[0].lower() in ("a", "an", "the", "this", "that", "these"):
        words = words[1:]
    return " ".join(words).strip(" .,;:")


def _clause(text, start, limit=LIMIT):
    """Кусок фразы от маркера до конца предложения."""
    rest = (text or "")[start:]
    stop = rest.find(". ")
    piece = rest[:stop] if stop > 0 else rest
    piece = " ".join(piece.split()).strip(" .,;:")
    if len(piece) > limit:
        cut = piece.rfind(" ", 0, limit)
        piece = piece[:cut if cut > 0 else limit].rstrip(" ,;:") + "…"
    return piece


def clauses(text):
    """Все противопоставления в тексте: [(с_кем, кусок)]."""
    low = _clean(text)
    result = []
    for marker in MARKERS:
        position = low.find(marker)
        while position >= 0:
            target = _target(low, position + len(marker))
            piece = _clause(low, position)
            if target and piece:
                result.append((target, piece))
            position = low.find(marker, position + len(marker))
    return result


def mentions(text, name):
    """Есть ли в тексте упоминание имени (по началу слова)."""
    low = _clean(text)
    key = _clean(name)
    result = False
    if key:
        position = low.find(key)
        result = position >= 0
    return result


def between(first, second):
    """Кусок про отличие первого понятия от второго (или пусто)."""
    text = (first or {}).get("en") if isinstance(first, dict) else ""
    name = (second or {}).get("name") if isinstance(second, dict) else str(second or "")
    result = ""
    for target, piece in clauses(text):
        if mentions(target, name) and not result:
            result = piece
    return result


def difference(first, second):
    """Различие в обе стороны: (кусок, чьё_описание) или ("", "")."""
    forward = between(first, second)
    if forward:
        return forward, str((first or {}).get("name") or "")
    backward = between(second, first)
    return (backward, str((second or {}).get("name") or "")) if backward else ("", "")
