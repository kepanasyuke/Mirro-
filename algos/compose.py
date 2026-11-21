# -*- coding: utf-8 -*-
"""Русская формулировка из структуры, когда текста по-русски нет.

Для понятия без русского описания бессмысленно молчать и вредно выдумывать
перевод. Зато структура уже говорит по-русски: у понятия есть русские имена
(алиасы из карты соответствий), есть связи и раздел. Из них собирается честная
рамка: как называется по-русски, с чем связано, а английское описание идёт
следом как источник.
"""
CYRILLIC = "абвгдеёжзийклмнопрстуфхцчшщъыьэюя"


def _is_russian(text):
    """Есть ли в строке кириллица."""
    return any(character in CYRILLIC for character in (text or "").lower())


ADJECTIVE_ENDINGS = ("ая", "ое", "ый", "ий", "ые", "ей", "ого", "ому", "ыми", "его")


def _bare_adjective(text):
    """Похоже ли имя на обрубок прилагательного без существительного.

    Карта соответствий иногда приносит одно слово («иностранная» вместо
    «иностранная помощь»). Подставлять такое в ответ нельзя: получится
    «иностранная — понятие в базе». Лучше честное английское имя.
    """
    low = (text or "").strip().lower()
    return bool(low) and " " not in low and len(low) <= 16 and low.endswith(ADJECTIVE_ENDINGS)


def _head_from_text(concept):
    """Имя из самого русского текста: часть до тире, точки или двоеточия."""
    text = str((concept or {}).get("ru") or "").strip()
    result = ""
    if text:
        for mark in (" —", " -", "—", ".", ":", ","):
            cut = text.find(mark)
            if 0 < cut <= 30:
                text = text[:cut]
        text = text.strip(" .,:;")
        if _is_russian(text) and 2 <= len(text) <= 30:
            result = text
    return result


def russian_title(concept):
    """Русское имя: из текста, затем существительное, затем самое полное.

    Порядок важен: карта соответствий иногда даёт только прилагательное
    («музыкальный»), а сам текст начинается с верного имени («Музыка — …»).
    """
    if not isinstance(concept, dict):
        return ""
    head = _head_from_text(concept)
    names = [str(alias).strip() for alias in concept.get("aliases") or ()
             if _is_russian(alias) and 3 <= len(str(alias)) <= 30]
    clean = [name for name in names if not name.startswith("_")]
    names = clean or names
    full = [name for name in names
            if not any(other != name and other.lower().startswith(name.lower())
                       for other in names)]
    names = full or names
    nouns = [name for name in names if not _bare_adjective(name)]
    pool = nouns or names
    result = head if head else (max(pool, key=len) if pool else "")
    if not result:
        result = str(concept.get("title") or concept.get("name") or "").replace("_", " ").strip()
    return result


def related_text(links, limit=3):
    """Связи в читаемую строку: только русские имена, без мусора по краям.
    Английские темы («plan», «trust») в русской рамке не показываем — иначе
    ответ наполовину на другом языке."""
    names = [str(item).strip() for item in list(links or ())[:limit] if item]
    russian = [name for name in names
               if _is_russian(name) and not name.endswith(" -")]
    return ", ".join(russian) if russian else ""


ENGLISH_LIMIT = 160


def _short_english(text, limit=ENGLISH_LIMIT):
    """Короткий английский фрагмент: одной фразой, по границе слова.

    Русский вопрос про тему, у которой есть только английское описание, должен
    получать выжимку, а не триста символов чужого текста: в русской рамке это
    выглядит как дамп и обрывается по смыслу.
    """
    clean = " ".join((text or "").split())
    if len(clean) <= limit:
        return clean
    cut = clean.rfind(" ", 0, limit)
    return clean[:cut if cut > 0 else limit].rstrip(" ,;:.") + "…"


def compose(concept, links=None, english=None):
    """Русская рамка вокруг понятия: имя, связи, затем английский источник."""
    title = russian_title(concept)
    name = str((concept or {}).get("name") or "").replace("_", " ") if isinstance(concept, dict) else ""
    parts = []
    if title:
        parts.append("%s — понятие в базе Мирро." % title)
    elif name:
        parts.append("%s — понятие в базе Мирро." % name)
    related = related_text(links)
    if related:
        parts.append("Связано с: %s." % related)
    if english:
        parts.append("Описание есть только по-английски: %s" % _short_english(english))
    text = " ".join(parts)
    return text[:1].upper() + text[1:] if text else text


def compose_with_frame(concept, links=None, frame=""):
    """Рамка плюс уже готовое английское описание в скобках источника."""
    result = compose(concept, links, frame)
    return result.strip()
