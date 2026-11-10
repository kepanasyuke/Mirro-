# -*- coding: utf-8 -*-
"""Mirro Algorithms — 31 · Иммунный страж (Immune Sentinel)

По принципу биологической иммунной системы непрерывно сканирует граф на
аномалии:
  - рёбра (edges[(src,pred,dst)] -> weight), чей вес после Хебб-обучения или
    мутаций разогнался сверх лимита → иммунное подавление (антитело ×0.1);
  - авто-резонансные роу-ссылки meta_routes вида (key -> KEY) (петля на себя)
    → удаление, чтобы не допускать бесконечного разгона.

Возвращает (graph, quarantined). Чистый Python, атомарно, по LINTER.md.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def run_graph_immune_scan(graph, max_allowed_weight=5.0, suppression=0.1):
    """Сканирует граф и подавляет аномальные веса / петлевые роу-ссылки.
    Пустой граф, некорректные параметры, не-dict edges → (graph, []).
    Рёбра с не-трёхэлементным ключом пропускаются; веса клампятся в ±50;
    симметрия подавления не роняет основной цикл при сбое.
    Возвращает (graph, quarantined_edges). Один return: tuple."""
    quarantined = []
    try:
        max_allowed_weight = float(max_allowed_weight)
    except Exception:
        max_allowed_weight = 5.0
    if graph is None or not hasattr(graph, "edges") or max_allowed_weight <= 0:
        return graph, quarantined
    if not isinstance(graph.edges, dict):
        return graph, quarantined
    if not graph.edges:
        # нет рёбер — нечего сканировать (всё равно чистим мета-петли ниже)
        pass
    # suppression 0..1 — «сила антитела»; вне диапазона берём по умолчанию
    try:
        suppression = float(suppression)
    except Exception:
        suppression = 0.1
    if not (0 < suppression <= 1):
        suppression = 0.1
    # 1. иммунное подавление аномально разогнанных рёбер
    for key, w in list(graph.edges.items()):
        try:
            if not isinstance(key, (tuple, list)) or len(key) < 3:
                continue
            w = float(w)
        except Exception:
            continue
        if w != w or w in (float("inf"), float("-inf")):
            continue
        if abs(w) > max_allowed_weight:
            nw = max(-50.0, min(50.0, w * suppression))
            graph.edges[key] = nw
            if hasattr(graph, "_set_adj_weight"):
                try:
                    graph._set_adj_weight(key[0], key[1], key[2], nw)
                    graph._set_adj_weight(key[2], key[1], key[0], nw)
                except Exception:
                    pass
            quarantined.append(key)
    # 2. удаление авто-резонансных петель мета-графа (from_edge == to_edge)
    meta = getattr(graph, "meta_routes", None)
    if meta:
        for key in list(meta.keys()):
            try:
                if isinstance(key, (tuple, list)) and len(key) >= 2 and key[0] == key[1]:
                    del meta[key]
            except Exception:
                continue
    return graph, quarantined


def scan_report(graph):
    """Краткий отчёт о состоянии графа после сканирования (для логирования).
    Не-граф → «нет графа». Один return: str."""
    if graph is None or not hasattr(graph, "edges"):
        return "нет графа"
    edges = getattr(graph, "edges", {})
    if not isinstance(edges, dict):
        edges = {}
    n_high = 0
    n_neg = 0
    for w in edges.values():
        try:
            fw = float(w)
        except Exception:
            continue
        if fw != fw or fw in (float("inf"), float("-inf")):
            continue
        if abs(fw) > 5.0:
            n_high += 1
        if fw < 0:
            n_neg += 1
    meta = getattr(graph, "meta_routes", None) or {}
    loops = sum(
        1 for k in meta
        if isinstance(k, (tuple, list)) and len(k) >= 2 and k[0] == k[1]
    )
    return (f"рёбер {len(edges)}, аномальных >5: {n_high}, "
            f"отрицательных: {n_neg}, мета-петель: {loops}")


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    from neural_electric import add_meta_route
    g = KnowledgeGraph()
    g.add_edge("a", "p", "b", 99.0)
    add_meta_route(g, ("a", "p", "b"), ("a", "p", "b"), mod=1.0)  # петля на себя
    gg, q = run_graph_immune_scan(g, max_allowed_weight=5.0)
    print("подавлено рёбер:", len(q), "вес после:", round(gg.edges[("a", "p", "b")], 2),
          "meta:", dict(gg.meta_routes), "| отчёт:", scan_report(gg))