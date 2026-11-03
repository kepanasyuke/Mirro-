# -*- coding: utf-8 -*-
"""Mirro Algorithms — 28 · Нейро-электричество графа (Neural Electric)

Инновация: модель «электрического импульса», бегущего по знаниевому графу,
как сигнал по нейронам. Объединяет все наработки Мирро:

  нервная клетка = узел знания (граф),
  синапс        = связь между понятиями,
  импульс       = «электричество», которое активирует узлы,
  медиаторы     = регулируют ВОЗБУДИМОСТЬ (порог активации),
  нуль-точка    = источник сигнала «нигде» (изолированная/нулевая точка),
  ТТЛ           = питает рёбра (вес связи из извлечённых фактов),
  Босова        = правила распространения ЕСЛИ <возбуждён> ТО <передать> ИНАЧЕ <затух>.

Из входного слова запускаем «импульс»: он распространяется по связям от узла
к узлу, пока хватает «напряжения», а нейромедиаторы снижают или повышают порог.
Результат — цепочка активированных понятий (ассоциативная активация).
"""
import sys, os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knowledge_graph import KnowledgeGraph


# по-босовски: ток идёт по «проводу-связи», если «напряжение» выше порога
def _threshold_for(e, base=0.5, dip=0.15, ser=0.15, nor=0.2):
    """Порог активации узла от медиаторов. Один return: float (0..1).

    дофамин и серотонин повышают порог (спокойно), норадреналин понижает
    (легче возбудиться, тревога/бодрость).
    """
    return max(0.05, min(0.95, base - nor + (dip + ser) * 0.2))


def fire(graph, start, neuromod=None, voltage=1.0, max_hops=4, decay=0.5):
    """Запускает импульс от узла start по графу.

    Возвращает список (узел, hop, остаточное_напряжение). Один return: list.
    """
    if not graph.nodes:
        return []
    start = start.strip().lower()
    if start not in graph.nodes:
        return []
    med = neuromod or {}
    threshold = _threshold_for(0, dip=med.get("dop", 0), ser=med.get("ser", 0), nor=med.get("nor", 0))
    activated = []
    frontier = [(start, 0, voltage)]
    seen = {start}
    for _ in range(max_hops * 3):
        if not frontier:
            break
        node, hop, v = frontier.pop(0)
        if v < threshold:
            continue
        activated.append((node, hop, round(v, 3)))
        for pred, other, w in graph.neighbors(node):
            # вес связи (из ТТЛ) усиливает остаточное напряжение по-босовски:
            # ЕСЛИ есть связь ТО передать, вес = проводимость
            if other in seen:
                continue
            seen.add(other)
            nv = v * decay * (0.5 + w) if w else v * decay * 0.6
            if nv >= threshold:
                frontier.append((other, hop + 1, nv))
    return activated


def activate_chain(graph, start, neuromod=None):
    """Осмысленная цепочка активированных понятий. Один return: str.

    Нуль-точка: если start изолирован (нет связей) — это «точка нигде»,
    сигнал не может пойти; честно говорим об этом.
    """
    if start.strip().lower() not in graph.nodes:
        return f"Понятие «{start}» ещё не в графе — импульс не от чего оттолкнуться."
    if not graph.neighbors(start.strip().lower()):
        return f"«{start}» — изолированная нуль-точка: нет связей, электричество не побежало."
    chain = fire(graph, start, neuromod=neuromod)
    if not chain:
        return f"Импульс от «{start}» затух — порог медиаторов слишком высок."
    parts = [f"{n}@{hop}:{v}" for n, hop, v in chain]
    return " → ".join(parts)


def try_neural_electric(query, kg=None):
    """Точка входа для try_*: «пусти электричество от X», «активируй понятие X».
    Один return: str или None."""
    q = (query or "").strip().lower()
    ans = None
    m = None
    import re as _re
    for pat in (r"пусти (?:импульс|электричество|ток) (?:от|из) (.+)",
                r"активируй (.+)",
                r"какую (?:связь|цепочку).{0,10}(.+)",
                r"возбуди (.+)"):
        mm = _re.search(pat, q)
        if mm:
            m = mm.group(1).strip()
            break
    if m:
        from neuromodulators import nm
        g = kg
        if g is None or len(g.nodes) < 3:
            try:
                from knowledge_graph import kg as _globkg
                g = _globkg if len(_globkg.nodes) > 2 else KnowledgeGraph()
            except Exception:
                g = KnowledgeGraph()
        # в реальном графе узел может быть без окончания — ищем по вхождению
        anchor = _find_node(g, m)
        if anchor is not None:
            m = anchor
        ans = activate_chain(g, m, neuromod=nm.level)
    elif "нейроэлектричеств" in q or "электричеств" in q or ("импульс" in q):
        sample = "Внимание влияет на память. Память укрепляет понимание. Если вход сильный, то сигнал идёт."
        g = kg or KnowledgeGraph()
        if kg is None:
            try:
                from knowledge_graph import kg as _globkg
                g = _globkg
            except Exception:
                pass
        if len(g.nodes) < 3:
            g.from_triples([(t[0], t[1], t[2]) for t in _sample_triples()])
        ans = ("Электричество по графу: синапс=связь, нейрон=узел. "
               "Пример импульса от «внимание»: " + activate_chain(g, "внимание"))
    return ans


def _find_node(graph, needle):
    """Находит узел графа по вхождению (учитывая окончания). Один return: str|None."""
    n = (needle or "").strip().lower()
    if n in graph.nodes:
        return n
    for node in graph.nodes:
        if node and (node in n or n in node or node.startswith(n[:5])):
            return node
    return None


def _sample_triples():
    """Небольшой граф-заглушка, если реального графа нет. Один return: list."""
    return [
        ("Внимание", "влияет на", "память"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
        ("Сон", "укрепляет", "память"),
    ]


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.from_triples(_sample_triples() + [])  # без ТТЛ пока
    print("граф:", g.summary())
    print("порог (база):", round(_threshold_for(0, nor=0.2), 2))
    print("импульс от 'внимание':", fire(g, "внимание"))
    print("цепочка:", activate_chain(g, "внимание"))
    print("нуль-точка:", activate_chain(g, "квантовый"))