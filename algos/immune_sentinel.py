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
    Возвращает (graph, quarantined_edges). Один return: tuple."""
    quarantined = []
    # 1. иммунное подавление аномально разогнанных рёбер
    for key, w in list(graph.edges.items()):
        if abs(w) > max_allowed_weight:
            graph.edges[key] = w * suppression
            if hasattr(graph, "_set_adj_weight"):
                graph._set_adj_weight(key[0], key[1], key[2], w * suppression)
                graph._set_adj_weight(key[2], key[1], key[0], w * suppression)
            quarantined.append(key)
    # 2. удаление авто-резонансных петель мета-графа (from_edge == to_edge)
    meta = getattr(graph, "meta_routes", None)
    if meta:
        for key in list(meta.keys()):
            if key[0] == key[1]:
                del meta[key]
    return graph, quarantined


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    from neural_electric import add_meta_route
    g = KnowledgeGraph()
    g.add_edge("a", "p", "b", 99.0)
    add_meta_route(g, ("a", "p", "b"), ("a", "p", "b"), mod=1.0)  # петля на себя
    gg, q = run_graph_immune_scan(g, max_allowed_weight=5.0)
    print("подавлено рёбер:", len(q), "вес после:", round(gg.edges[("a", "p", "b")], 2),
          "meta:", dict(gg.meta_routes))