# -*- coding: utf-8 -*-
"""
Mirro Reasoning Engine — кластерная приоритизация ответов.
=================================================================
Чистый модуль (без тяжёлого импорта MirroCore/algorithms), чтобы
кластерную логику выбора ответа можно было юнит-тестировать быстро.

Перенесено из core/mirro_core.py (функции _tokenize, score_candidate,
choose_best) без изменения семантики, чтобы не зависеть от построения
индекса в память при импорте.
"""

import re as _re


STOPWORDS = {
    "и", "в", "на", "с", "по", "за", "от", "до", "из", "у", "для", "о",
    "не", "ни", "все", "это", "как", "так", "что", "кто", "где", "когда",
    "к", "об", "под", "над", "чем", "какие", "какой", "какая", "расскажи",
    "напиши", "про", "при", "или", "из", "ещё", "же", "бы", "а", "но",
    "a", "an", "the", "to", "of", "for", "and", "or", "in", "on", "by",
}


def _tokenize(text):
    return _re.findall(r"[а-яёa-z0-9]+", text.lower())


# Лёгкий стемминг: срезаем частые окончания русских слов, чтобы «роботов/роботы»
# и «функцию/функция» совпадали без полного морфологического анализа.
_ENDINGS = (
    ("ами", ""), ("ями", ""), ("ого", ""), ("ому", ""), ("ими", ""),
    ("ых", ""), ("их", ""), ("ий", ""), ("ый", ""), ("ая", ""), ("яя", ""),
    ("ое", ""), ("ее", ""), ("ие", ""), ("ые", ""), ("а", ""), ("я", ""),
    ("о", ""), ("е", ""), ("ы", ""), ("и", ""), ("у", ""), ("ю", ""),
    ("ой", ""), ("ей", ""), ("ом", ""), ("ем", ""), ("ах", ""), ("ях", ""),
    ("ам", ""), ("ям", ""), ("ов", ""), ("ев", ""), ("ей", ""), ("ом", ""),
    ("сь", ""), ("ть", ""), ("ет", ""), ("ит", ""), ("ут", ""), ("ют", ""),
)


def _stem(word):
    w = word
    if len(w) <= 4:
        return w
    for suf, rep in _ENDINGS:
        if w.endswith(suf) and len(w) - len(suf) >= 3:
            return w[: len(w) - len(suf)]
    return w


def _tokenize_stem(text):
    return [_stem(w) for w in _tokenize(text)]


def _content_words(text):
    """Стеммированные слова без стоп-слов — носители смысла."""
    return {_stem(w) for w in _tokenize(text) if w not in STOPWORDS}


def score_candidate(query, inst, out, cluster, tfidf_score, preferred=None):
    s = tfidf_score * 2.5
    reasons = []
    if preferred:
        if cluster == preferred:
            s += 5.0
        elif cluster == "generated":
            s -= 4.0
        else:
            s -= 2.0

    # СЕМАНТИЧЕСКАЯ РЕЛЕВАНТНОСТЬ: совпадение со стеммированным СМЫСЛОМ.
    q_content = _content_words(query)
    # Основной сигнал — совпадение со ВОПРОСОМ, к которому относится этот ответ
    # (inst), т.к. ответ может содержать текст о другом. Запас — содержимое out.
    a_base = q_content
    ref_set = _content_words(inst or "") or a_base
    out_set = _content_words(out or "")
    # объединяем: слова и инструкции, и ответа
    ref = ref_set | out_set

    overlap = len(q_content & ref) if q_content else 0
    if q_content:
        jac = overlap / max(len(q_content | ref), 1)
        s += overlap * 1.5
        reasons.append(f"тема:{overlap}")
        if overlap == 0:
            # Ни одного смыслового слова вопроса в (вопрос+ответ) — это мимо темы.
            # Обнуляем вклад TF-IDF (он и выдал мусор) и сильно штрафуем,
            # чтобы «расскажи про роботов»→певица никогда не выигрывало.
            s += -2.5 * tfidf_score
            s -= 8.0
            reasons.append("мимо-темы")
        elif jac < 0.15:
            s -= 1.5
            reasons.append("слабая-тема")

    if len(out) < 20:
        s -= 0.5
    q_set = set(_tokenize_stem(query))
    a_set = set(_tokenize_stem(out))
    if q_set and a_set and len(q_set & a_set) / max(len(q_set | a_set), 1) > 0.7:
        s -= 1.0
    return s, reasons


def choose_best(query, candidates, preferred=None):
    if not candidates:
        return None, 0.0, "нет кандидатов"
    cands = [c for c in candidates if c[0][2] != "generated"] or candidates

    if preferred:
        same = [(inst, out, cl, sc) for (inst, out, cl), sc in cands if cl == preferred]
        if same:
            best = max(same, key=lambda x: score_candidate(query, x[0], x[1], x[2], x[3], preferred)[0])
            sc, _ = score_candidate(query, best[0], best[1], best[2], best[3], preferred)
            if sc >= 4.0:
                return best[1], sc, f"кластер {best[2]}"
            return None, 0.0, f"слабый результат в кластере {preferred}"
        return None, 0.0, f"нет в кластере {preferred}"
    b_out, b_sc, b_r = None, -999, ""
    for (inst, out, cl), tfidf_score in cands[:5]:
        sc, rs = score_candidate(query, inst, out, cl, tfidf_score, preferred)
        if sc > b_sc:
            b_sc, b_out, b_r = sc, out, "; ".join(rs) if rs else "базовый"
    if b_sc < 4.0:
        return None, 0.0, f"слабый результат ({b_sc:.1f})"
    return b_out, b_sc, b_r


def run_self_check():
    """Компактная самопроверка кластерной логики. Возвращает (ok, details).

    Требует только этот модуль — без базы и без загрузки корпуса.
    """
    checks = []

    # 1. НДС-вопрос: предпочтительный ru-кластер выигрывает у generated.
    q = "Что такое НДС?"
    candidates = [
        (("что такое ндс", "НДС — налог на добавленную стоимость.", "ru"), 5.0),
        (("сгенерированный шум", "авум срама случайный текст хз.", "generated"), 6.0),
    ]
    best, sc, reason = choose_best(q, candidates, preferred="ru")
    checks.append(("ru преобладает над generated", best is not None and "НДС" in best))

    # 2. generated деприоритизируется, если есть не-generated альтернатива.
    candidates2 = [
        (("сгенерированный шум", "авум срама случайный текст хз.", "generated"), 7.0),
        (("что такое ндс", "НДС — косвенный налог.", "general"), 3.0),
    ]
    best2, _, _ = choose_best(q, candidates2, preferred=None)
    checks.append(("generated уступает general", best2 is not None and "налог" in best2))

    # 3. Пустой предпочтительный кластер -> нет ответа (поведение сохранено).
    candidates3 = [(("что такое ндс", "НДС — налог.", "general"), 4.0)]
    best3, _, reason3 = choose_best(q, candidates3, preferred="code")
    checks.append(("нет в предпочтительном кластере", best3 is None))

    # 4. Точное совпадение кластера даёт ответ.
    candidates4 = [
        (("напиши функцию на python", "def f(x): return x", "code"), 5.0),
        (("другой", "другой ответ совсем", "general"), 6.0),
    ]
    best4, _, reason4 = choose_best("напиши функцию на python", candidates4, preferred="code")
    checks.append(("код-кластер выбран", best4 is not None and "def" in best4))

    details = "\n".join(f"  [{'OK' if ok else 'FAIL'}] {name}" for name, ok in checks)
    ok = all(ok for _, ok in checks)
    return ok, details


if __name__ == "__main__":
    ok, d = run_self_check()
    print("REASONING SELF-CHECK:")
    print(d)
    print("[summary]", "OK" if ok else "FAIL")