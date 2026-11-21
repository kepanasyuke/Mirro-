# -*- coding: utf-8 -*-
"""Связность разговора: «а почему?» относится к предыдущему понятию.

Без этого каждый вопрос начинается с нуля, и «а подробнее?» получает ответ
«понятие не найдено». Здесь хранится последнее понятие, а короткие продолжения
(«а почему», «подробнее», «ещё») разворачиваются в полный вопрос о нём же.

Состояние живёт в процессе и сбрасывается `reset()` — тесты и чужие вызовы
не должны зависеть друг от друга.
"""
STATE = {"concept": None, "query": None}

FOLLOWUPS = ("подробнее", "а почему", "почему тогда", "а как", "а чем", "а что",
             "ещё", "еще", "и что", "дальше", "tell me more", "what about", "more")


def reset():
    """Забыть предыдущее понятие."""
    STATE["concept"] = None
    STATE["query"] = None
    return True


def remember(concept, query=""):
    """Запомнить понятие, о котором шла речь."""
    remembered = False
    if concept:
        STATE["concept"] = str(concept)
        STATE["query"] = str(query or "")
        remembered = True
    return remembered


def last():
    """Последнее понятие или None."""
    return STATE["concept"]


def is_followup(query):
    """Похож ли вопрос на продолжение прошлой темы.

    Маркер должен стоять отдельным словом: иначе «объясни что такое связь»
    ловится на «и что» и вопрос разворачивается в «… связь алгоритм».
    Собственный вопрос с «что такое / кто такой» продолжением не считается.
    """
    import re as _re
    low = " " + (query or "").strip().lower() + " "
    own_subject = any(marker in low for marker in ("что такое", "кто такой",
                                                   "кто такая", "что значит",
                                                   "что означает"))
    result = False
    if len(low) <= 42 and not own_subject:
        for marker in FOLLOWUPS:
            pattern = r"(?<![а-яёa-z])" + _re.escape(marker) + r"(?![а-яёa-z])"
            if _re.search(pattern, low) and not result:
                result = True
    return result


def expand(query):
    """Полный вопрос о последнем понятии вместо короткого продолжения."""
    result = query
    concept = last()
    if concept and is_followup(query):
        name = concept.replace("_", " ")
        result = ("%s %s" % (query.strip(), name)).strip()
    return result


def remember_from_answer(query, concept):
    """Запоминает понятие, если вопрос не был пустым продолжением."""
    remembered = False
    if concept and not is_followup(query):
        remembered = remember(concept, query)
    return remembered
