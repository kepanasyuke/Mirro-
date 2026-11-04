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
        self._adj = {}       # name -> [(pred, other, weight)]  (индекс соседей)

    # ---------- построение ----------
    def add_node(self, name, tag="понятие", facts=None, weight=1.0):
        name = self._norm(name)
        if not name:
            return
        if name not in self.nodes:
            self.nodes[name] = Node(name, tag, facts, weight)
            self._adj[name] = []
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
        # синхронизируем вес в индексе соседей (двусторонне)
        self._set_adj_weight(s, pred, d, self.edges[key])
        self._set_adj_weight(d, pred, s, self.edges[key])

    def _set_adj_weight(self, from_node, pred, to_node, weight):
        """Обновляет вес связи в _adj для направления from_node->to_node. Один return: None."""
        for i, row in enumerate(self._adj.get(from_node, [])):
            if row[0] == pred and row[1] == to_node:
                self._adj[from_node][i] = (pred, to_node, weight)
                return
        # нет в индексе — добавляем
        self._adj.setdefault(from_node, []).append((pred, to_node, weight))
        return None

    def hebbian_learn(self, node_a, node_b, amount=0.2):
        """Синаптическая пластичность: если два узла активировались вместе —
        связь между ними усиливается (Хебб). Один return: int — число укреплённых."""
        a, b = self._norm(node_a), self._norm(node_b)
        strengthened = 0
        for (s, p, d), w in list(self.edges.items()):
            if (s == a and d == b) or (s == b and d == a):
                nw = min(2.0, w + amount)
                self.edges[(s, p, d)] = nw
                self._set_adj_weight(s, p, d, nw)
                self._set_adj_weight(d, p, s, nw)
                strengthened += 1
        return strengthened

    def synapse_decay(self, amount=0.01, floor=0.2):
        """Все связи медленно слабеют (редко используемые «атрофируются»),
        как забывание. Один return: int — число изменённых связей."""
        changed = 0
        for key, w in list(self.edges.items()):
            nw = max(floor, w - amount)
            if nw != w:
                self.edges[key] = nw
                changed += 1
        return changed

    @staticmethod
    def _norm(name):
        return _re.sub(r"\s+", " ", name or "").strip().lower().rstrip(".!?;")

    def prune_stopwords(self, stopwords):
        """Удаляет узлы-связки (мусорные слова типа «однако», «затем») из графа
        и связанные с ними рёбра. Один return: int — число удалённых узлов."""
        if not stopwords:
            return 0
        dead = {n for n in self.nodes if n in stopwords or n.strip() in stopwords}
        for d in dead:
            del self.nodes[d]
            if d in self._adj:
                del self._adj[d]
        self.edges = {k: w for k, w in self.edges.items() if k[0] not in dead and k[2] not in dead}
        # пересобрать индекс соседей
        self._rebuild_adj()
        return len(dead)

    # ---------- вопросы ----------
    def _forward_links(self, name):
        """Исходящие связи узла (p, other, w). Один return: list."""
        name = self._norm(name)
        return [row for row in self._adj.get(name, [])]

    def neighbors(self, name):
        """Все прямые связи узла по индексу. Один return: list."""
        name = self._norm(name)
        return [row for row in self._adj.get(name, [])]

    def relation(self, a, b):
        """Прямые отношения между a и b (по индексу, без дублей). Один return: list."""
        a, b = self._norm(a), self._norm(b)
        seen = set()
        rels = []
        for p, other, w in self._adj.get(a, []):
            if other == b and (p, w) not in seen:
                seen.add((p, w))
                rels.append((p, w))
        for p, other, w in self._adj.get(b, []):
            if other == a and (p, w) not in seen:
                seen.add((p, w))
                rels.append((p, w))
        return rels

    def _step(self, frontier, b, visited, max_fanout=40):
        """Один шаг BFS: из текущего фронта к b, ограничен размахом.
        Один return: (found, next_frontier)."""
        nxt = []
        if frontier:
            frontier = frontier[:max_fanout]  # не раздувать фронт без конца
        for cur, trail in frontier:
            for p, other, w in self.neighbors(cur):
                if other == b:
                    found = trail + [(cur, p, b, w)]
                    return (found, [])
                if other not in visited:
                    visited.add(other)
                    nxt.append((other, trail + [(cur, p, other, w)]))
        return (None, nxt)

    def path(self, a, b, max_depth=3, max_fanout=40):
        """Цепочка связей от a к b (если есть) — «рассуждение через граф».
        Один return: list-путь или None."""
        a, b = self._norm(a), self._norm(b)
        if a not in self.nodes or b not in self.nodes:
            return None
        frontier = [(a, [(a, None, None, 1.0)])]
        visited = {a}
        result = None
        for _ in range(max_depth):
            if result is not None or not frontier:
                break
            result, frontier = self._step(frontier, b, visited, max_fanout)
        return result

    def explain(self, name, depth=1):
        """Связное объяснение понятия: сами факты + соседи."""
        name = self._norm(name)
        n = self.nodes.get(name)
        if not n:
            return None
        lines = [f"«{name}» — {n.tag}"]
        if n.facts:
            lines.append("Факты: " + "; ".join(n.facts[:5]))
        # соседи по силе связи (вес) — сначала самые «проводимые»
        ranked = sorted(self.neighbors(name), key=lambda r: -r[2])
        for p, other, w in ranked[:6]:
            lines.append(f"связано {p} с «{other}» (вес {w:.2f})")
        return "\n".join(lines)

    def from_triples(self, triples):
        """Наполнить из списка (субъект, предикат, объект)."""
        for s, p, o in triples:
            self.add_edge(s, p, o)
        return len(triples)

    def save(self, path):
        """Сохраняет граф на диск (pickle). Один return: bool."""
        try:
            import pickle, os
            tmp = str(path) + ".tmp"
            with open(tmp, "wb") as f:
                pickle.dump({"nodes": self.nodes, "edges": self.edges}, f, protocol=4)
            os.replace(tmp, str(path))
            return True
        except Exception:
            return False

    def load(self, path):
        """Загружает граф с диска; если файла нет — пусто. Один return: int (рёбер)."""
        self.nodes = {}
        self.edges = {}
        self._adj = {}
        try:
            import pickle
            with open(str(path), "rb") as f:
                data = pickle.load(f)
            self.nodes = data.get("nodes", {})
            self.edges = data.get("edges", {})
            # восстанавливаем индекс соседей
            self._rebuild_adj()
        except Exception:
            pass
        return len(self.edges)

    def _rebuild_adj(self):
        """Пересобирает индекс соседей из рёбер. Один return: None."""
        self._adj = {n: [] for n in self.nodes}
        for (s, p, d), w in self.edges.items():
            self._adj[s].append((p, d, w))
            self._adj[d].append((p, s, w))
        return None

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