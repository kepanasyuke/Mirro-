# -*- coding: utf-8 -*-
"""Причинные связи из описаний: почему, а не только что.

В русских записях (`module_knowledge`) причин почти нет — там «что это» и пример.
А в английских определениях (`_EN_KB`) их 213: «because», «leads to», «results in».
Модуль вытаскивает такие куски как отдельный факт и отдаёт их для вопроса «почему».

Кусок берётся от маркера до конца предложения и обрезается по длине: цитировать
весь абзац бессмысленно, а соврать про причину нельзя — лучше показать фрагмент
и сказать, откуда он.
"""
RU_MARKERS = ("потому что", "из-за", "поэтому", "приводит к", "вследствие",
              "в результате", "так как", "благодаря")
EN_MARKERS = ("because", "so that", "therefore", "leads to", "results in",
              "causes", "since", "as a result")
LIMIT = 180


CONNECTORS = ("того, что", "тем, что", "из-за того, что", "the fact that", "что ", "это ")


def _strip_connectors(piece):
    """Убирает связки в начале причины: «того, что молекулы…» → «молекулы…»."""
    text = (piece or "").strip(" ,;:-")
    changed = True
    while changed:
        changed = False
        for connector in CONNECTORS:
            low = text.lower()
            if low.startswith(connector) and len(text) > len(connector) + 5:
                text = text[len(connector):].strip(" ,;:-")
                changed = True
    return text[:1].upper() + text[1:] if text else text


def _cut(text, start, limit=LIMIT):
    """Кусок от позиции до конца предложения, не длиннее предела."""
    rest = (text or "")[start:]
    stop = rest.find(". ")
    piece = rest[:stop] if stop > 0 else rest
    piece = _strip_connectors(piece.strip(" .,;:"))
    if len(piece) > limit:
        stop = piece.rfind(" ", 0, limit)
        piece = piece[:stop if stop > 0 else limit].rstrip(" ,;:") + "…"
    return piece


def fragments(text, markers):
    """Куски текста сразу после каждого маркера."""
    low = (text or "").lower()
    result = []
    for marker in markers:
        position = low.find(marker)
        if position >= 0:
            piece = _cut(text, position + len(marker))
            if len(piece) >= 5:
                result.append(piece)
    return result


def for_text(ru_text="", en_text=""):
    """Причинные куски из русских и английских описаний: [(язык, кусок)]."""
    result = [("ru", piece) for piece in fragments(ru_text, RU_MARKERS)]
    result.extend(("en", piece) for piece in fragments(en_text, EN_MARKERS))
    return result


def for_concept(concept, limit=2):
    """Причинные куски по понятию реестра, не больше limit штук."""
    result = []
    if isinstance(concept, dict):
        result = for_text(concept.get("ru") or "", concept.get("en") or "")[:limit]
    return result


def has_causes(concept):
    """Есть ли у понятия хоть одна причинная связь."""
    return bool(for_concept(concept, limit=1))


def index(limit=1):
    """Причины по всем понятиям: имя -> [(язык, кусок)]."""
    from algos import concepts
    result = {}
    for name, concept in concepts.build().items():
        pieces = for_concept(concept, limit=limit)
        if pieces:
            result[name] = pieces
    return result
