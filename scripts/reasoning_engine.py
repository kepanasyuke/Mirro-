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


def _tokenize(text):
    return _re.findall(r"[а-яёa-z0-9]+", text.lower())


def score_candidate(query, out, cluster, tfidf_score, preferred=None):
    s = tfidf_score * 2.5
    reasons = []
    if preferred:
        if cluster == preferred:
            s += 5.0
        elif cluster == "generated":
            s -= 4.0
        else:
            s -= 2.0
    q_set = set(_tokenize(query))
    a_set = set(_tokenize(out))
    overlap = len(q_set & a_set)
    if overlap > 0:
        s += overlap * 0.8
        reasons.append(f"слова:{overlap}")
    if len(out) < 20:
        s -= 0.5
    if q_set and a_set and len(q_set & a_set) / max(len(q_set | a_set), 1) > 0.7:
        s -= 1.0
    return s, reasons


def choose_best(query, candidates, preferred=None):
    if not candidates:
        return None, 0.0, "нет кандидатов"
    # Всегда исключаем шумный generated, если есть альтернативы
    cands = [c for c in candidates if c[0][2] != "generated"] or candidates
    if preferred:
        same = [(inst, out, cl, sc) for (inst, out, cl), sc in cands if cl == preferred]
        if same:
            best = max(same, key=lambda x: score_candidate(query, x[1], x[2], x[3], preferred)[0])
            sc, _ = score_candidate(query, best[1], best[2], best[3], preferred)
            return best[1], sc, f"кластер {best[2]}"
        # В предпочтительном кластере нет ответа — не тянем мусор из чужих кластеров
        return None, 0.0, f"нет в кластере {preferred}"
    b_out, b_sc, b_r = None, -999, ""
    for (inst, out, cl), tfidf_score in cands[:5]:
        sc, rs = score_candidate(query, out, cl, tfidf_score, preferred)
        if sc > b_sc:
            b_sc, b_out, b_r = sc, out, "; ".join(rs) if rs else "базовый"
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