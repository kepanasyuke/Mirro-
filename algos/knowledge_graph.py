# -*- coding: utf-8 -*-
"""Mirro Algorithms — 21 · Знаниевый граф (Knowledge Graph)

Инновация: понимать РАСШИРЕННО через связи понятий, а не текст.
Хранит онтологию: понятие -> Node(материал/факты), relation "X --p--> Y".
Может отвечать: «что связывает X и Y?», «что вытекает из X?», «объясни X».

Лёгкий, без внешних библиотек: чистый dict/граф + вывод через связи.
Заполняется вручную и/или извлечением из текста (см. 24_ttl_extract.py).
"""
import re as _re


class Node:
    __slots__ = ("name", "tag", "facts", "weight")
    def __init__(self, name, tag="понятие", facts=None, weight=1.0):
        self.name = name
        self.tag = tag
        self.facts = facts or []
        self.weight = weight

    def __repr__(self):
        return f"<Node:{self.name}:{self.tag}>"


class KnowledgeGraph:
    def __init__(self):
        self.nodes = {}      # name -> Node
        self.edges = {}      # (src, p, dst) -> weight  (p = предикат/связь)

    # ---------- построение ----------
    def add_node(self, name, tag="понятие", facts=None, weight=1.0):
        name = self._norm(name)
        if not name:
            return
        if name not in self.nodes:
            self.nodes[name] = Node(name, tag, facts, weight)
        elif facts:
            self.nodes[name].facts = list(dict.fromkeys(self.nodes[name].facts + facts))

    def add_edge(self, src, pred, dst, weight=1.0):
        s, d = self._norm(src), self._norm(dst)
        if not s or not d or s == d:
            return
        self.add_node(s)
        self.add_node(d)
        key = (s, self._norm(pred), d)
        self.edges[key] = max(self.edges.get(key, 0.0), weight)

    @staticmethod
    def _norm(name):
        return _re.sub(r"\s+", " ", name or "").strip().lower().rstrip(".!?;")

    # ---------- вопросы ----------
    def neighbors(self, name):
        """Все прямые связи узла: list[(pred, other, weight)]."""
        name = self._norm(name)
        out = []
        for (s, p, d), w in self.edges.items():
            if s == name:
                out.append((p, d, w))
            elif d == name:
                out.append((p, s, w))
        return out

    def path(self, a, b, max_depth=3):
        """Цепочка связей от a к b (если есть) — «рассуждение через граф»."""
        a, b = self._norm(a), self._norm(b)
        if a not in self.nodes or b not in self.nodes:
            return None
        if a == b:
            return [(a, "=", b, 1.0)]
        frontier = [(a, [(a, None, None, 1.0)])]
        visited = {a}
        for _ in range(max_depth):
            nxt = []
            for cur, trail in frontier:
                for p, other, w in self.neighbors(cur):
                    if other == b:
                        return trail + [(cur, p, b, w)]
                    if other not in visited:
                        visited.add(other)
                        nxt.append((other, trail + [(cur, p, other, w)]))
            frontier = nxt
        return None

    def relation(self, a, b):
        """Прямые отношения между a и b."""
        a, b = self._norm(a), self._norm(b)
        rels = []
        for (s, p, d), w in self.edges.items():
            if (s == a and d == b) or (s == b and d == a):
                rels.append((p, w))
        return rels

    def explain(self, name, depth=1):
        """Связное объяснение понятия: сами факты + соседи."""
        name = self._norm(name)
        n = self.nodes.get(name)
        if not n:
            return None
        lines = [f"«{name}» — {n.tag}"]
        if n.facts:
            lines.append("Факты: " + "; ".join(n.facts[:5]))
        for p, other, w in self.neighbors(name)[:6]:
            lines.append(f"связано {p} с «{other}»")
        return "\n".join(lines)

    def from_triples(self, triples):
        """Наполнить из списка (субъект, предикат, объект)."""
        for s, p, o in triples:
            self.add_edge(s, p, o)
        return len(triples)

    # ---------- состояние ----------
    def summary(self):
        return f"граф: {len(self.nodes)} узлов, {len(self.edges)} связей"


# Общий синглтон графа для всего процесса
kg = KnowledgeGraph()


# ---------- быстрый интерфейс для try_* ----------
def try_knowledge_graph(query):
    """Возвращает ответ строкой, если запрос про связи понятий, иначе None."""
    q = ok = _re.sub(r"\s+", " ", (query or "").strip().lower())
    q = q.rstrip("!?.;,")
    q = q.replace("что связывает ", "").replace("что общего у ", "").replace("как связан", "связан")
    q = q.replace("связано ли ", "").replace("есть ли связь между", "связь между")
    # прямое: «X и Y» / «X — Y»
    if kg.edges and (" связывает " in (" " + query.lower()) or " что общего у " in " " + query.lower()):
        m = _re.search(r"\b([^\s]+?)\s+(?:и|и с|с)\s+([^\s]+?)[\s?]*$", q)
        if m:
            a, b = m.group(1), m.group(2)
            rels = kg.relation(a, b)
            if rels:
                return ", ".join(f"«{a}» {p} «{b}»" for p, _w in rels) + "."
            path = kg.path(a, b)
            if path:
                nodes = [line[0] for line in path if line[0]]
                last = path[-1][2]
                if last:
                    nodes.append(last)
                chain = " → ".join(dict.fromkeys(nodes))
                return f"Прямой связи нет, но выводится: {chain}."
    if "объясн" in q:
        for name in kg.nodes:
            if name in q and len(name) > 3:
                ex = kg.explain(name)
                if ex:
                    return ex
    return None


if __name__ == "__main__":
    kg.from_triples([
        ("Нейрон", "принадлежит", "мозг"),
        ("Нейрон", "передаёт", "сигнал"),
        ("Сигнал", "формирует", "мысль"),
        ("Мысль", "порождает", "понимание"),
    ])
    print(kg.summary())
    print("связывает нейрон и мысль?", kg.relation("нейрон", "мысль"))
    print("путь нейрон->понимание:", kg.path("нейрон", "понимание"))
    print(kg.explain("нейрон"))