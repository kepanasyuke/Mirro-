# -*- coding: utf-8 -*-
"""Mirro Algorithms — 28 · Волновой резонанс роу-связей (Wave Resonance)

Инновация: если два отдалённых участка графа «вибрируют» синхронно — их рёбра
имеют близкую активную проводимость (сходный «химический фон») — между ними
автоматически простраивается ВРЕМЕННАЯ мостовая роу-ссылка. Так сеть сама
эволюционирует топологию во время диалога, а не только по жёстким триплетам.

Работает поверх реального KnowledgeGraph:
    edges[(src, pred, dst)] -> weight;   роу-ссылки в graph.meta_routes.

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def calculate_vector_distance(vec_a, vec_b):
    """Евклидово расстояние между векторами. Разная длина → минимум по паре,
    хвост считается разницей. Один return: float."""
    if vec_a is None or vec_b is None:
        return 0.0
    dist = 0.0
    n = max(len(vec_a), len(vec_b))
    for i in range(n):
        a = vec_a[i] if i < len(vec_a) else 0.0
        b = vec_b[i] if i < len(vec_b) else 0.0
        dist += (a - b) ** 2
    return dist ** 0.5


def _edge_conductance(graph, key):
    """Активная проводимость ребра (текущий вес). Один return: float."""
    try:
        return float(graph.edges.get(key, 0.0))
    except Exception:
        return 0.0


def conductance_of(graph, key):
    """Публичная проводимость ребра; NaN/inf -> 0. Один return: float."""
    value = _edge_conductance(graph, key)
    return value if value == value and abs(value) != float("inf") else 0.0


def _safe_mod(value):
    """Модуль |mod| роу-ссылки; битое значение -> 0. Один return: float."""
    try:
        mod = abs(float(value))
    except Exception:
        mod = 0.0
    return mod if mod == mod and mod != float("inf") else 0.0


META_ROUTE_CAP = 2000
MOD_FLOOR = 0.05   # порог, ниже которого роу-ссылка считается увядшей (LTD)


def _meta_route_budget(graph, cap=META_ROUTE_CAP):
    """Сколько новых роу-ссылок ещё можно завести до жёсткого потолка.
    Пустой/некорректный граф или неположительный cap → 0. Один return: int."""
    limit = 0
    try:
        limit = int(cap)
    except Exception:
        limit = META_ROUTE_CAP
    if limit <= 0:
        return 0
    meta = getattr(graph, "meta_routes", None)
    used = len(meta) if isinstance(meta, dict) else 0
    return max(0, limit - used)


def _node_pairs(graph, edge_limit=120):
    """Кандидаты на резонанс: рёбра попарно, но только парами «соседних»
    по проводимости, без квадратичного перебора всего графа.
    Берём не более edge_limit рёбер и сравниваем только с окном близких.
    Пустой граф → []. Один return: list [(edge_a, edge_b), ...]."""
    pairs = []
    keys = list(graph.edges.keys()) if isinstance(getattr(graph, "edges", None), dict) else []
    if len(keys) < 2:
        return pairs
    try:
        limit = max(2, int(edge_limit))
    except Exception:
        limit = 120
    probe = [(k, _edge_conductance(graph, k)) for k in keys[:limit]]
    probe.sort(key=lambda kv: kv[1])
    for i in range(len(probe) - 1):
        pairs.append((probe[i][0], probe[i + 1][0]))
    return pairs


def try_bridge_resonant_edges(graph, resonance_threshold=0.15, max_routes=META_ROUTE_CAP,
                              edge_limit=120):
    """Простраивает временные мостовые роу-ссылки между рёбрами с близкой
    активной проводимостью (резонанс).

    Раньше перебирались ВСЕ пары рёбер: на 200 рёбрах это ~20 000 роу-ссылок
    за шаг, на реальном графе — миллионы и рост памяти без остановки. Теперь
    рассматриваются только соседи по отсортированной проводимости (не более
    edge_limit рёбер), а общий размер meta_routes ограничен max_routes.

    Пустой граф/некорректный порог → 0. Возвращает число созданных роу-ссылок.
    Один return: int."""
    if graph is None or not hasattr(graph, "edges") or not isinstance(graph.edges, dict):
        return 0
    try:
        threshold = float(resonance_threshold)
    except Exception:
        threshold = 0.15
    if not (threshold > 0):
        return 0
    from neural_electric import add_meta_route
    budget = _meta_route_budget(graph, max_routes)
    created = 0
    if budget <= 0:
        return 0
    meta = getattr(graph, "meta_routes", None)
    meta = meta if isinstance(meta, dict) else {}
    for ea, eb in _node_pairs(graph, edge_limit):
        if created >= budget:
            break
        diff = abs(conductance_of(graph, ea) - conductance_of(graph, eb))
        if diff >= threshold:
            continue
        # уже существующая роу-ссылка не пересчитывается: шаг должен быть
        # идемпотентным и не затирать сильные mod от Хебба/иммунного стража
        if not _has_strong_route(meta, ea, eb):
            add_meta_route(graph, ea, eb, mod=0.35)
            created += 1
    return created


def _has_strong_route(meta, edge_a, edge_b):
    """Есть ли уже осмысленная (|mod| >= MOD_FLOOR) роу-ссылка между рёбрами.
    Мёртвые остатки (увядшие через LTD) перекрываются резонансом заново.
    Один return: bool."""
    return _safe_mod(meta.get((edge_a, edge_b))) >= MOD_FLOOR


def prune_meta_routes(graph, cap=META_ROUTE_CAP):
    """Обрезает meta_routes до cap самых сильных по |mod| роу-ссылок.
    Нужен для графов, уже раздутых прошлым неограниченным ростом.
    Пустой/некорректный граф → 0. Один return: int (сколько удалено)."""
    meta = getattr(graph, "meta_routes", None)
    removed = 0
    if isinstance(meta, dict) and meta:
        try:
            limit = int(cap)
        except Exception:
            limit = META_ROUTE_CAP
        if 0 < limit < len(meta):
            keep = sorted(meta.items(), key=lambda kv: -abs(_safe_mod(kv[1])))[:limit]
            removed = len(meta) - len(keep)
            graph.meta_routes = dict(keep)
    return removed


if __name__ == "__main__":
    print("расстояние (0.1,0.2)-(0.4,0.6):",
          round(calculate_vector_distance([0.1, 0.2], [0.4, 0.6]), 4))