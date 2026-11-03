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


def _chain_to_str(kg, chain):
    """Цепочка узлов -> строка вида «a —p→ b». Один return: str."""
    parts = []
    for i in range(len(chain) - 1):
        rels = kg.relation(chain[i], chain[i + 1])
        pred = rels[0][0] if rels else "связан"
        parts.append(f"{chain[i]} —{pred}→ {chain[i+1]}")
    return " ; ".join(parts)


def _join_chains(kg, chains):
    """Собирает человекочитаемый ответ из первых цепочек. Один return: str."""
    lines = []
    for ch in chains[:4]:
        part = _chain_to_str(kg, ch)
        if part:
            lines.append(part)
    return "Из своих связей вывожу: " + " | ".join(lines) + "."


_INFER_WORDS = ("как", "почему", "объясни", "что такое", "выведи", "связано")


def _looks_like_reasoning(q):
    """Похож ли запрос на вопрос-вывод. Один return: bool."""
    return any(w in q for w in _INFER_WORDS)


def try_graph_infer(query):
    """Точка входа для try_*: отвечает, если граф непуст и вопрос про связи.
    Один return: str или None."""
    from knowledge_graph import kg
    answer = None
    q = (query or "").lower()
    if kg.edges and len(kg.nodes) >= 3 and _looks_like_reasoning(q):
        chains = infer_from_graph(kg, q, max_depth=2)
        if chains:
            answer = _join_chains(kg, chains)
    return answer


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