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
    stem = w
    if len(w) > 4:
        hits = [suf for suf, _rep in _ENDINGS
                if w.endswith(suf) and len(w) - len(suf) >= 3]
        if hits:
            stem = w[: len(w) - len(hits[0])]
    return stem


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


def confidence_from_score(score, has_result=True):
    """Преобразует сырой score-кандидата в уверенность 0..1.
    Порог выдачи choose_best = 4.0; уверенность растёт от 4.0 до ~12.0.
    Если результата нет — уверенность 0.0. Один return: float."""
    conf = 0.0
    if has_result and score is not None:
        raw = max(0.0, float(score) - 4.0)
        conf = min(1.0, raw / 8.0)
    return round(conf, 2)


def _dedupe_candidates(cands):
    """Возвращает кандидатов без дублей по ответу (держит первый по входу).
    Короткие/пустые ответы отбрасываются. Один return: list."""
    seen = set()
    out = []
    for (inst, out_txt, cl), sc in cands:
        if not out_txt or len(out_txt) < 6:
            continue
        key = out_txt.strip().lower()[:80]
        if key in seen:
            continue
        seen.add(key)
        out.append(((inst, out_txt, cl), sc))
    return out


def _prio_leaf_tie(cands, preferred):
    """При равном score выбирает ответ из предпочтительного кластера.
    Один return: (best_item, best_score) или None."""
    best = None
    best_sc = -999.0
    for (inst, out, cl), sc in cands:
        item_sc = sc
        if preferred and cl == preferred:
            item_sc += 0.001  # лёгкий приоритет предпочтительного кластера
        if item_sc > best_sc:
            best_sc = item_sc
            best = ((inst, out, cl), sc)
    return best, best_sc


def choose_best(query, candidates, preferred=None, top_n=8):
    b_out = None
    b_sc = 0.0
    b_r = "нет кандидатов"
    cands = []
    if candidates:
        cands = [c for c in candidates if c[0][2] != "generated"] or candidates
    cands = _dedupe_candidates(cands)  # 1) дедуп и очистка пустых

    if cands:
        if preferred:
            same = [(inst, out, cl, sc) for (inst, out, cl), sc in cands if cl == preferred]
            if same:
                best = max(same, key=lambda x: score_candidate(query, x[0], x[1], x[2], x[3], preferred)[0])
                sc, _ = score_candidate(query, best[0], best[1], best[2], best[3], preferred)
                if sc >= 4.0:
                    b_out, b_sc, b_r = best[1], sc, f"кластер {best[2]}"
                else:
                    b_r = f"слабый результат в кластере {preferred}"
            else:
                b_r = f"нет в кластере {preferred}"
        else:
            best_out = None
            best_score = -999
            best_reason = ""
            # 2) учитываем больше кандидатов (top_n вместо жёстких 5)
            ranked = []
            for (inst, out, cl), tfidf_score in cands[:top_n]:
                sc, rs = score_candidate(query, inst, out, cl, tfidf_score, preferred)
                ranked.append((sc, out, "; ".join(rs) if rs else "базовый"))
            if ranked:
                ranked.sort(key=lambda x: -x[0])
                best_score, best_out, best_reason = ranked[0]
            if best_score >= 4.0:
                b_out, b_sc, b_r = best_out, best_score, best_reason
            else:
                b_r = f"слабый результат ({best_score:.1f})"
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