# -*- coding: utf-8 -*-
"""Mirro Algorithms — 34 · Зеркальное моделирование сознания (Mirror Cognition)

Theory of Mind для нейросети: Mirro строит «зеркальный подграф»-профиль
собеседника на основе лингвистического анализа его реплик и адаптирует
проводимость вывода под его когнитивное состояние (усталость, фокус интента).

Профиль — это чистый dict-стейт (аналог RefractoryState), он НЕ пишется в
Node.__slots__ и НЕ мутирует рёбра напрямую (у edges нет поля active_weight):
apply_mirror_modulation возвращает dict проводимостей, который можно свернуть
с результатами compute_modulated_edges.

Чистый Python, атомарные функции (один return), по LINTER.md.
"""


def init_mirror_profile():
    """Создаёт пустой когнитивный профиль собеседника. Один return: dict."""
    return {
        "user_fatigue": 0.0,
        "user_intent_focus": 1.0,
        "idle_updates": 0,
    }


def update_mirror_profile(current_profile, user_query_tokens, session_pulse=0.7):
    """Обновляет зеркальный слепок по реплике пользователя.
    Пустые/None токены → профиль без правок. Некорректный профиль → новый.
    Один return: dict (новый профиль)."""
    prof = dict(current_profile) if isinstance(current_profile, dict) else init_mirror_profile()
    tokens = user_query_tokens or []
    if not isinstance(tokens, (list, tuple, set)):
        tokens = []
    try:
        pulse = max(0.0, min(1.0, float(session_pulse or 0.0)))
    except Exception:
        pulse = 0.7
    try:
        base_fatigue = max(0.0, min(1.0, float(prof.get("user_fatigue", 0.0) or 0.0)))
    except Exception:
        base_fatigue = 0.0
    if len(tokens) < 3 and pulse > 0.8:
        prof["user_fatigue"] = min(1.0, base_fatigue + 0.2)
    else:
        prof["user_fatigue"] = max(0.0, base_fatigue - 0.1)
    art_keywords = {"искусство", "театр", "дизайн", "арт", "образ", "стиль", "творческ",
                "музыка", "кино", "живопись", "литература", "поэзия", "сценар",
                "фото", "архитектур", "балет", "опера", "скульптур", "графика",
                "рассказ", "стих", "роман", "песн", "мод", "эстетик", "интерьер"}
    query_set = {str(t).lower() for t in tokens}
    try:
        base_focus = max(0.0, min(1.0, float(prof.get("user_intent_focus", 1.0) or 1.0)))
    except Exception:
        base_focus = 1.0
    if query_set & art_keywords:
        prof["user_intent_focus"] = max(0.0, base_focus - 0.4)
    else:
        prof["user_intent_focus"] = min(1.0, base_focus + 0.1)
    prof["idle_updates"] = min(100000, max(0, int(prof.get("idle_updates") or 0)) + 1)
    return prof


def apply_mirror_modulation_to_graph(graph, mirror_profile):
    """Модулирует проводимости рёбер по зеркальному профилю (усталость/фокус).
    Пустой граф или пустой-не-профиль → {}; fatigue/focus нормализуются в [0,1];
    веса не опускаются ниже 0. Возвращает НОВЫЙ dict (не мутирует граф).
    Один return: dict."""
    if graph is None or not isinstance(mirror_profile, dict) or not mirror_profile \
        or not getattr(graph, "edges", None):
        return {}
    try:
        fatigue = max(0.0, min(1.0, float(mirror_profile.get("user_fatigue", 0.0) or 0.0)))
        focus = max(0.0, min(1.0, float(mirror_profile.get("user_intent_focus", 1.0) or 1.0)))
    except Exception:
        fatigue, focus = 0.0, 1.0
    if fatigue != fatigue or fatigue in (float("inf"), float("-inf")):
        fatigue = 0.0
    if focus != focus or focus in (float("inf"), float("-inf")):
        focus = 1.0
    out = {}
    for key, w in graph.edges.items():
        try:
            if not isinstance(key, (tuple, list)) or len(key) < 3:
                continue
            nw = float(w)
        except Exception:
            continue
        if nw != nw or nw in (float("inf"), float("-inf")):
            continue
        combined = " ".join(str(x) for x in key[:3]).lower()
        if ("хаос" in combined) or ("юмор" in combined or "шутк" in combined
                            or "ирония" in combined or "сарказм" in combined):
            nw *= focus                      # строгий ИТ-фокус гасит юмор/хаос/иронию
        if fatigue > 0.5:
            nw *= (1.0 - 0.4 * fatigue)      # усталый пользователь -> лаконично
        out[key] = max(0.0, nw)
    return out


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.add_edge("математика", "ядро", "код", 1.0)
    g.add_edge("шутка", "цепь", "юмор", 1.5)
    prof = update_mirror_profile(init_mirror_profile(), ["написать", "функцию"], 0.7)
    mod = apply_mirror_modulation_to_graph(g, prof)
    print("профиль:", prof)
    print("модуляция:", {k: round(v, 2) for k, v in mod.items()})