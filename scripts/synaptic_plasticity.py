# -*- coding: utf-8 -*-
"""Эволюционный регулятор синапсов: пластичность мета-графа (улучшение №38).

LTP (долговременная потенциация) и LTD (долговременная депрессия) на уровне
роу-ссылок реального KnowledgeGraph:
  - clean_weak_meta_edges  — серотониновое «увядание»: прунит роу-ссылки с
    |mod| ниже порога (LTD), не давая графу забиваться мёртвыми связями;
  - apply_ltp_consolidation — дофаминовое закрепление: успешный спайк дофамина
    намертво увеличивает базовый вес активных рёбер (LTP).

Работает поверх графа с graph.meta_routes (список (from_edge,to_edge)->mod).

Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))


def clean_weak_meta_edges(graph, extinction_threshold=0.05):
    """Прунит слабые роу-ссылки мета-графа: |mod| < порога -> связь увядает.
    Возвращает число удалённых роу-ссылок. Один return: int."""
    meta = getattr(graph, "meta_routes", None)
    dead_keys = []
    if meta:
        for key, mod in meta.items():
            if abs(mod) < extinction_threshold:
                dead_keys.append(key)
        for key in dead_keys:
            del meta[key]
    return len(dead_keys)


def apply_ltp_consolidation(graph, activated_edges, dopamine_spike=0.5, lr=0.05,
                            cap=2.0):
    """Дофаминовое структурное закрепление активных рёбер (LTP).

    Успешный ответ (спайк дофамина) увеличивает базовый вес ребра и
    синхронизирует индекс соседей. Возвращает число укреплённых рёбер.
    Один return: int."""
    strengthened = 0
    edges = graph.edges
    for key in activated_edges:
        if key in edges:
            new_w = min(cap, edges[key] + lr * dopamine_spike)
            edges[key] = new_w
            if hasattr(graph, "_set_adj_weight"):
                graph._set_adj_weight(key[0], key[1], key[2], new_w)
                graph._set_adj_weight(key[2], key[1], key[0], new_w)
            strengthened += 1
    return strengthened


if __name__ == "__main__":
    print("synaptic_plasticity готов")