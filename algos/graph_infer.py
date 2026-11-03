# -*- coding: utf-8 -*-
"""Mirro Algorithms — 25 · Граф-ассоциативный вывод (Graph Associative Reasoning)

Инновация: рассуждение ЧЕРЕЗ СВЯЗИ, а не через память.
Если прямого ответа нет, алгоритм идёт по рёбрам знаниевого графа:
  X --связь--> Y --связь--> Z  =>  про X можно вывести про Z.
Это ближе к человеческому «если A связано с B, а B с C, то A даёт C».

Работает поверх knowledge_graph (21) и наполняется через ttl_extract (24).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knowledge_graph import KnowledgeGraph


def infer_from_graph(kg: KnowledgeGraph, query, topic="", max_depth=2):
    """Пытается вывести цепочки от 'topic' или слов запроса по рёбрам графа.

    Возвращает список строк-выводов, либо [].
    """
    q = (query or "").lower()
    # стартовые узлы: тема (если указана) + узлы графа, что встречаются в вопросе
    starts = []
    if topic:
        starts.append(topic)
    for name in kg.nodes:
        if name and len(name) > 3 and name in q:
            starts.append(name)
    # дедуп
    seen = set()
    uniq = []
    for s in starts:
        if s not in seen:
            seen.add(s)
            uniq.append(s)

    results = []
    for s in uniq[:5]:
        # поиск вглубь от s — все цепочки до max_depth
        _recurse(kg, s, [], max_depth, results, seen_prefix=set())
    # обрезать до внятных
    return results[:8]


def _recurse(kg, node, trail, max_depth, results, seen_prefix):
    """Обход в глубину с фиксацией путей."""
    if len(trail) >= max_depth:
        trail_with = trail + [node]
        if len(trail_with) >= 2:
            results.append(trail_with)
        return
    for pred, other, _w in kg.neighbors(node):
        key = (node, pred, other)
        if key in seen_prefix:
            continue
        seen_prefix.add(key)
        _recurse(kg, other, trail + [node], max_depth, results, seen_prefix)
        seen_prefix.discard(key)


def format_path(path):
    """path = ['a','b','c'] -> "a —св.→ b —св.→ c" """
    if not path:
        return ""
    s = path[0]
    for i in range(1, len(path)):
        rels = []
        # подберём предикат между предыдущим и текущим узлом из edges
        s += " → " + path[i]
    return s


def try_graph_infer(query):
    """Точка входа для try_* : если граф непуст и вопрос похож на связи — отвечает."""
    from knowledge_graph import kg
    if not kg.edges or len(kg.nodes) < 3:
        return None
    q = (query or "").lower()
    # срабатываем только если вопрос похож на «объясни/как/почему/что» И в графе есть слово от запроса
    if not any(w in q for w in ("как", "почему", "объясни", "что такое", "выведи", "связано")):
        return None
    chains = infer_from_graph(kg, q, max_depth=2)
    if not chains:
        return None
    # соберём человеческий ответ
    lines = []
    for ch in chains[:4]:
        # формат через соседей
        parts = []
        for i in range(len(ch) - 1):
            rel = kg.relation(ch[i], ch[i + 1])
            parts.append(f"{ch[i]} —{rel[0][0] if rel else 'связан'}→ {ch[i+1]}")
        if parts:
            lines.append(" ; ".join(parts))
    if lines:
        return "Из своих связей вывожу: " + " | ".join(lines) + "."
    return None


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.from_triples([
        ("Внимание", "влияет на", "память"),
        ("Память", "зависит от", "внимания"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
    ])
    print("вывод от 'внимание':")
    for ch in infer_from_graph(g, "внимание", max_depth=2):
        print("  ", format_path(ch))
    print()
    print("попытка try_graph_infer:", try_graph_infer("как внимание связано с пониманием?"))