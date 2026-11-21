# -*- coding: utf-8 -*-
"""Диспетчер планов: под тип вопроса выбирается свой план на машине.

Определение, связи, сравнение, вопрос «почему» — разные планы, но одни и те же
операции над понятиями и графом. Тип определяется по маркерам вопроса, без
внешних моделей; каждый план исполняется машиной (`algos/plan_machine.py`).

Честность важнее гладкости: если причинных связей в базе нет, план «почему»
так и говорит и показывает то, что известно.
"""
import re


PAIR_MARKERS = (" и ", ",", " vs", " versus", " от ", " with ", " и чем ")

# Порядок важен: сначала узкие маркеры (stats раньше count, compare раньше links),
# иначе «сколько понятий» уедет в count, а «чем отличается» — в links.
PATTERNS = (
    ("stats", ("сколько всего", "сколько понятий", "сколько тем", "размер базы",
               "статистика", "что знаешь о базе", "how big", "database size")),
    ("count", ("сколько", "how many", "число связей", "количество связей")),
    ("compare", ("чем отличается", "отличается", "отличие", "разница", "сравни",
                 "сходств", "похож", "что общего", "difference between", "differ",
                 " vs ", " versus ")),
    ("links", ("с чем связан", "связан", "связи", "связь", "related", "relates")),
    ("why", ("почему", "why", "зачем", "для чего", "с какой целью")),
    ("how", ("как работает", "как устроен", "как устроена", "how does", "how do")),
    ("definition", ("что такое", "what is", "это что", "определение", "define", "who is")),
)


def classify(query):
    """Тип вопроса: compare, links, why, definition или unknown."""
    low = (query or "").lower()
    result = "unknown"
    for intent, markers in PATTERNS:
        if any(marker in low for marker in markers) and result == "unknown":
            result = intent
    return result


PAIR_LEAD = ("что общего", "чем отличается", "чем отличаются", "в чём разница",
             "в чем разница", "в чём отличие", "в чем отличие", "сходство",
             "разница", "различие", "отличие", "сравни", "сравнить", "похожи",
             "similarities", "difference between", "compare")


def _clean_side(text):
    """Убирает из стороны сравнения слова вопроса: «сходство любви» → «любви»."""
    side = (text or "").strip(" ?.!,-")
    changed = True
    while changed:
        changed = False
        for lead in PAIR_LEAD:
            if side.startswith(lead):
                side = side[len(lead):].strip(" ?.!,-")
                changed = True
    for lead in ("между", "у", "of", "between"):
        if side.startswith(lead + " "):
            side = side[len(lead):].strip(" ?.!,-")
    return side


def split_pair(query):
    """Две сущности из вопроса сравнения: (первая, вторая) или (None, None)."""
    low = " " + (query or "").lower() + " "
    for marker in PAIR_MARKERS:
        if marker in low:
            left, _, right = low.partition(marker)
            return _clean_side(left), _clean_side(right.strip(" ?.!"))
    return None, None


def _concept(operation, arguments):
    """Понятие по запросу: язык слова, реестр, затем выученные имена."""
    from algos import lookup
    query = arguments[0] if arguments else ""
    found = lookup.find_with_learned(query) if isinstance(query, str) else None
    return found["concept"] if found else None


def _neighbours(operation, arguments):
    """Соседи понятия из графа определений.

    Одно понятие может жить в двух узлах: английская тема («binary_search») и
    русская запись модуля («_бинарный поиск»). Рёбра бывают у второго, а
    вопрос разрешается в первый — поэтому ищем узел и по русскому названию.
    """
    from algos.concept_graph import EDGES, neighbours
    value = arguments[0] if arguments else None
    name = value.get("name") if isinstance(value, dict) else value
    if not isinstance(name, str):
        return []
    found = list(neighbours(name, depth=1))
    if not found:
        alt = name[1:] if name.startswith("_") else "_" + name
        found = list(neighbours(alt, depth=1))
    if not found and isinstance(value, dict):
        from algos import compose
        title = (compose.russian_title(value) or "").strip().lower()
        if len(title) >= 4:
            for node in EDGES:
                plain = node.lstrip("_").replace("_", " ").strip().lower()
                if plain == title:
                    found = list(neighbours(node, depth=1))
                    break
    return found[:4]


def _common(operation, arguments):
    """Общие соседи двух понятий."""
    first, second = (arguments + [None, None])[:2]
    return sorted(set(first or ()) & set(second or ()))


def _only_first(operation, arguments):
    """Соседи первого понятия, которых нет у второго."""
    first, second = (arguments + [None, None])[:2]
    return sorted(set(first or ()) - set(second or ()))


def _only_second(operation, arguments):
    """Соседи второго понятия, которых нет у первого."""
    first, second = (arguments + [None, None])[:2]
    return sorted(set(second or ()) - set(first or ()))


STOPWORDS = {"сколько", "всего", "тем", "про", "понятий", "понятия", "в", "на", "базе",
             "есть", "только", "the", "how", "many", "topics", "about", "of", "in", "base"}


def _stat_word(query):
    """Значимое слово запроса: «сколько тем про математику» → «математику»."""
    words = [w for w in re.findall(r"[а-яёa-z]{4,}", (query or "").lower())
             if w not in STOPWORDS and not w.startswith(("русск", "англ", "причин", "текст"))]
    return max(words, key=len) if words else ""


def _stats(operation, arguments):
    """Сводка по базе: понятия, языки, причины, очередь."""
    from algos import self_metrics
    data = self_metrics.coverage()
    word = _stat_word(arguments[0] if arguments else "")
    if word:
        from algos import concepts
        stem = word[:6]
        hits = [c for c in concepts.build().values()
                if stem in ((c.get("name") or "") + " " + (c.get("ru") or "") + " "
                            + (c.get("en") or "")).lower()]
        data["word"] = word
        data["word_count"] = len(hits)
        data["word_ru"] = sum(1 for c in hits if (c.get("ru") or "").strip())
    return data


def _count(operation, arguments):
    """Сколько элементов в значении (связей, слов, записей)."""
    value = arguments[0] if arguments else None
    return len(value) if isinstance(value, (list, tuple, set, dict, str)) else 0


def operations():
    """Реестр операций для планов диспетчера."""
    return {"concept": _concept, "neighbours": _neighbours, "common": _common,
            "only_first": _only_first, "only_second": _only_second, "count": _count,
            "stats": _stats}


def dispatch(operation, arguments):
    """Единая точка вызова операций для машинного плана."""
    handler = operations().get(operation)
    return handler(operation, arguments) if handler else None


def plan_for(intent, query):
    """План шагов под тип вопроса; для unknown плана нет."""
    plans = {
        "stats": [("data", "stats", [query])],
        "count": [("concept", "concept", [query]), ("links", "neighbours", ["=concept"]),
                  ("total", "count", ["=links"])],
        "definition": [("concept", "concept", [query]), ("links", "neighbours", ["=concept"])],
        "how": [("concept", "concept", [query]), ("links", "neighbours", ["=concept"])],
        "links": [("concept", "concept", [query]), ("links", "neighbours", ["=concept"])],
        "why": [("concept", "concept", [query]), ("links", "neighbours", ["=concept"])],
        "compare": [("left", "concept", [split_pair(query)[0]]),
                    ("right", "concept", [split_pair(query)[1]]),
                    ("links_left", "neighbours", ["=left"]),
                    ("links_right", "neighbours", ["=right"]),
                    ("shared", "common", ["=links_left", "=links_right"]),
                    ("only_left", "only_first", ["=links_left", "=links_right"]),
                    ("only_right", "only_second", ["=links_left", "=links_right"])],
    }
    return plans.get(intent, [])


def _short_definition(concept, limit=110):
    """Первое предложение русского описания понятия, не длиннее предела."""
    if not isinstance(concept, dict):
        return ""
    text = " ".join((concept.get("ru") or "").split())
    if not text:
        return ""
    stop = text.find(". ")
    if stop > 0:
        text = text[:stop]
    text = text.rstrip(" .;:,")
    if len(text) > limit:
        cut = text.rfind(" ", 0, limit)
        text = text[:cut if cut > 0 else limit].rstrip(" ,;:") + "…"
    return text


def _saying(concept, name):
    """«Имя — толкование» или пустая строка, если толкования нет.

    Русский текст часто уже начинается с имени («Стек — это структура…»),
    поэтому повтор убираем, иначе выходит «Стек — Стек — это структура…».
    """
    text = _short_definition(concept)
    if not (name and text):
        return ""
    low = text.lower()
    if low.startswith(name.lower()):
        text = text[len(name):].lstrip(" —-–:,").strip()
        if text.lower().startswith("это "):
            text = text[4:]
    return "%s — %s" % (name, text) if len(text) >= 8 else ""


def _list_text(items):
    """Список имён в читаемую строку; подчёркивания коротких записей убираем."""
    if not items:
        return "нет"
    return ", ".join(str(item).replace("_", " ").strip() for item in items)


def _is_russian(text):
    """Есть ли в строке кириллица. Один return: bool."""
    return any("а" <= ch.lower() <= "я" or ch.lower() == "ё" for ch in str(text or ""))


def _canon_topic(word):
    """Каноническая тема словаря по первым буквам слова («дерева» → «дерево»).
    Один return: str (пустая строка, если темы нет)."""
    from algos.module_knowledge import fk
    low = str(word or "").strip().lower()
    best, best_score = "", (0, 0)
    if len(low) >= 4:
        for info in (fk._by_name or {}).values():
            if not isinstance(info, dict):
                continue
            candidates = [str(info.get("topic") or "")] + [str(t) for t in (info.get("tags") or [])]
            for cand in candidates:
                cand = cand.strip().lower()
                if len(cand) < 4:
                    continue
                common = 0
                for x, y in zip(low, cand):
                    if x != y:
                        break
                    common += 1
                # «массива» ближе к «массив», чем к «масса»: решает общий префикс
                score = (common, int(cand == low), -len(cand))
                if common >= 4 and score > best_score:
                    best, best_score = cand, score
    return best


def _name_of(value):
    """Человекочитаемое имя: русское имя понятия, иначе имя без подчёркиваний."""
    if isinstance(value, dict):
        from algos import compose
        result = compose.russian_title(value) or value.get("name") or ""
    else:
        result = value or ""
    return str(result).replace("_", " ").strip()


def render(intent, values, query=""):
    """Текст ответа по типу вопроса и посчитанным значениям."""
    from algos.neuro_answer import russian_answer
    concept = values.get("concept") or values.get("left")
    if intent == "stats":
        query_low = (query or "").lower()
        data = values.get("data") or {}
        total = data.get("concepts") or 0
        if data.get("word"):
            result = ("Понятий про «%s»: %s из %s, с русским текстом: %s."
                      % (data["word"], data.get("word_count"), total, data.get("word_ru")))
        elif "русск" in (query_low or ""):
            result = "Понятий с русским текстом: %s из %s." % (data.get("with_ru"), total)
        elif "англ" in (query_low or ""):
            result = "Понятий только по-английски: %s из %s." % (data.get("en_only"), total)
        elif "причин" in (query_low or ""):
            result = "Понятий с причинными связями: %s." % data.get("causes")
        else:
            result = ("Понятий всего: %s, с русским текстом: %s, только по-английски: %s."
                      % (total, data.get("with_ru"), data.get("en_only")))
    elif intent == "count":
        name = _name_of(concept)
        result = ("У понятия «%s» связей в графе: %s." % (name, values.get("total"))
                  if name else "")
    elif intent == "compare":
        left = _name_of(values.get("left"))
        right = _name_of(values.get("right"))
        empty = not (values.get("links_left") or values.get("links_right")
                     or values.get("shared"))
        result = ""
        # готовая таблица сравнений важнее перечня связей: у многих пар связей
        # в графе нет вовсе, а различие осмысленное уже записано
        raw_left, raw_right = split_pair(query)
        # готовое сравнение не требует, чтобы оба слова нашлись в понятиях:
        # «ии» в реестр не попадает, а запись сравнения у нас есть
        known_text = ""
        if raw_left and raw_right:
            try:
                from algos.knowledge_graph import _compare_known_pair
                canon_left = _canon_topic(raw_left) or raw_left
                canon_right = _canon_topic(raw_right) or raw_right
                for pair in ((canon_left, canon_right), (left or raw_left, right or raw_right),
                             (raw_left, raw_right)):
                    known_text = _compare_known_pair(pair) or ""
                    if known_text:
                        break
            except Exception:
                known_text = ""
        if known_text:
            result = known_text
        if result:
            pass
        elif left and right and empty:
            result = "%s и %s есть в базе, но связей в графе у них нет." % (left, right)
        elif left and right:
            result = ("%s: связи — %s. %s: связи — %s. Общее: %s. Только у %s: %s. Только у %s: %s."
                      % (left, _list_text(values.get("links_left")), right,
                         _list_text(values.get("links_right")), _list_text(values.get("shared")),
                         left, _list_text(values.get("only_left")),
                         right, _list_text(values.get("only_right"))))
            from algos import contrast
            piece, source = contrast.difference(values.get("left"), values.get("right"))
            if piece:
                result = result + " Различие: %s (так сказано в описании «%s»)." % (piece, source)
            else:
                # Противопоставления в тексте нет — тогда хотя бы толкования:
                # «связи — trust» без определений ничего не объясняет
                pair = [_saying(values.get("left"), left), _saying(values.get("right"), right)]
                known = [item for item in pair if item]
                if known:
                    result = result + " По описаниям: %s." % "; ".join(known)
        elif left or right:
            # одно из понятий не нашлось: сравнение не построить, но известную
            # часть отдаём — иначе ответ пустой и вопрос уходит в мусор
            raw_left, raw_right = split_pair(query)
            missing = raw_right if left else raw_left
            known = left or right
            result = ("Сравнить не с чем: понятия «%s» в базе нет. Про «%s»: связи — %s."
                      % ((missing or "второе").strip(" ?.!"), known,
                         _list_text(values.get("links_left") or values.get("links_right"))))
    elif intent == "links":
        name = _name_of(concept)
        result = ("%s — связи: %s." % (name, _list_text(values.get("links")))) if name else ""
    elif intent == "why":
        name = _name_of(concept)
        result = ""
        # готовое назначение понятия важнее перечня связей
        try:
            from algos.module_knowledge import why_for
            result = why_for(query) or ""
        except Exception:
            result = ""
        if result:
            pass
        else:
            # готовая причина из словаря раньше связей графа
            try:
                from algos.module_knowledge import cause_for
                result = cause_for(query) or ""
            except Exception:
                result = ""
        if result:
            pass
        elif isinstance(concept, dict):
            from algos import causality
            pieces = causality.for_concept(concept, limit=2)
            russian = [piece for language, piece in pieces if language == "ru"]
            english = [piece for language, piece in pieces if language == "en"]
            if russian:
                result = "Причина: %s." % "; ".join(russian)
            elif english:
                result = ("По-русски объяснения пока нет. В английском описании причина названа так: %s."
                          % "; ".join(english))
            elif name:
                # В отказ пускаем только русские связи: английские темы
                # («peacock», «crow») в русском ответе выглядят мусором
                links = [str(item).replace("_", " ").strip()
                         for item in (values.get("links") or [])
                         if _is_russian(str(item))]
                if links:
                    result = ("Причинных связей в базе нет. Известно, что «%s» связано с: %s."
                              % (name, ", ".join(links[:3])))
                else:
                    # Тупик без пользы: лучше отдать толкование, чем пустоту.
                    # На вопрос «почему идёт дождь» причинной записи нет, но
                    # что такое дождь — известно
                    saying = _saying(concept, name)
                    result = ("Причинных связей в базе нет. Известно, что %s." % saying
                              if saying else
                              "Причинных связей в базе нет — объяснения, почему это так, "
                              "в моих знаниях не нашлось.")
    elif isinstance(concept, dict):
        # Тема есть только в английской части: русский вопрос не должен
        # получать абзац чужого текста — это не ответ на русском
        russian_text = (concept.get("ru") or "").strip()
        if not russian_text and (concept.get("en") or "").strip() and _is_russian(query):
            result = ("По-русски описания нет: «%s» есть только в английской части базы. "
                      "Спроси по-английски — отдам определение целиком." % _name_of(concept))
        else:
            result = russian_answer(concept, values.get("links") or [])
    else:
        result = ""
    return result


def answer(query):
    """Ответ по плану под тип вопроса; короткие продолжения — о прошлом понятии."""
    from algos import context, plan_machine
    effective = context.expand(query) if isinstance(query, str) else query
    intent = classify(effective)
    if intent == "unknown" and isinstance(query, str) and context.is_followup(query) and context.last():
        intent = "definition"
    result = None
    if intent != "unknown" and isinstance(effective, str):
        executed = plan_machine.run_plan(plan_for(intent, effective), dispatch)
        values = executed["values"]
        text = render(intent, values, effective)
        if text:
            concept = values.get("concept") or values.get("left")
            name = concept.get("name") if isinstance(concept, dict) else None
            context.remember_from_answer(effective, name)
            result = {"answer": text, "intent": intent, "steps": executed["steps"],
                      "values": values, "query": effective}
    return result


def answer_special(query):
    """Ответ только для «особых» типов: сравнение, связи, причина, подсчёт, статистика.

    Определение и «как работает» намеренно не трогаем: их отдают обработчики,
    которые стоят в конвейере раньше и умеют это лучше. Нужно, чтобы сравнение
    и подсчёт не съедались общим ответом на любое упоминание темы.
    """
    intent = classify(query)
    result = None
    if intent in ("compare", "links", "why", "count", "stats"):
        found = answer(query)
        result = found["answer"] if found else None
    return result


def answer_text(query):
    """Только текст ответа диспетчера."""
    found = answer(query)
    return found["answer"] if found else None
