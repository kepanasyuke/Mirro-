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
    def _forward_links(self, name):
        """Исходящие связи узла (p, other, w). Один return: list."""
        out = []
        for (s, p, d), w in self.edges.items():
            if s == name:
                out.append((p, d, w))
        return out

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

    def _step(self, frontier, b, visited):
        """Один шаг BFS: из текущего фронта к b. Один return: (found, next_frontier)."""
        nxt = []
        for cur, trail in frontier:
            for p, other, w in self.neighbors(cur):
                if other == b:
                    found = trail + [(cur, p, b, w)]
                    return (found, [])
                if other not in visited:
                    visited.add(other)
                    nxt.append((other, trail + [(cur, p, other, w)]))
        return (None, nxt)

    def path(self, a, b, max_depth=3):
        """Цепочка связей от a к b (если есть) — «рассуждение через граф»."""
        a, b = self._norm(a), self._norm(b)
        frontier = [(a, [(a, None, None, 1.0)])]
        visited = {a}
        result = None
        for _ in range(max_depth):
            if result is not None or not frontier:
                break
            result, frontier = self._step(frontier, b, visited)
        return result

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


# ---------- быстрый интерфейс для try_* (все функции — один return) ----------
def _clean_q(query):
    """Нормализует запрос для разбора. Один return: str."""
    q = _re.sub(r"\s+", " ", (query or "").strip().lower())
    q = q.rstrip("!?.;,")
    q = q.replace("что связывает ", "").replace("что общего у ", "").replace("как связан", "связан")
    q = q.replace("связано ли ", "").replace("есть ли связь между", "связь между")
    return q


def _want_relation(query, q):
    """Есть ли в запросе явный запрос на связь. Один return: bool."""
    return bool(kg.edges and (" связывает " in (" " + query.lower()) or " что общего у " in " " + query.lower()))


def _pair_from(q):
    """Вытаскивает пару понятий из запроса. Один return: (a, b) или (None, None)."""
    m = _re.search(r"\b([^\s]+?)\s+(?:и|и с|с)\s+([^\s]+?)[\s?]*$", q)
    if m:
        return (m.group(1), m.group(2))
    return (None, None)


def _answer_relation(a, b):
    """Прямая связь между a и b. Один return: str или None."""
    if not a or not b:
        return None
    rels = kg.relation(a, b)
    if rels:
        return ", ".join(f"«{a}» {p} «{b}»" for p, _w in rels) + "."
    return None


def _chain_text(path):
    """Красивая цепочка узлов из пути. Один return: str."""
    nodes = [line[0] for line in path if line[0]]
    last = path[-1][2]
    if last:
        nodes.append(last)
    return " → ".join(dict.fromkeys(nodes))


def _answer_path(a, b):
    """Вывод через цепочку связей. Один return: str или None."""
    path = kg.path(a, b)
    if path:
        return f"Прямой связи нет, но выводится: {_chain_text(path)}."
    return None


def _answer_explain(q):
    """Объяснение понятия из запроса. Один return: str или None."""
    for name in kg.nodes:
        if "объясн" in q and name in q and len(name) > 3:
            ex = kg.explain(name)
            if ex:
                return ex
    return None


def try_knowledge_graph(query):
    """Возвращает ответ строкой, если запрос про связи понятий, иначе None."""
    q = _clean_q(query)
    ans = None
    if _want_relation(query, q):
        a, b = _pair_from(q)
        ans = _answer_relation(a, b) or _answer_path(a, b)
    else:
        ans = _answer_explain(q)
    return ans


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