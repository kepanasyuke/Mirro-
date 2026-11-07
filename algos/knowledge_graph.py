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
        rows = self._adj.get(from_node, [])
        found = False
        for i, row in enumerate(rows):
            if row[0] == pred and row[1] == to_node:
                self._adj[from_node][i] = (pred, to_node, weight)
                found = True
                break
        if not found:
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
        removed = 0
        if stopwords:
            dead = {n for n in self.nodes if n in stopwords or n.strip() in stopwords}
            for d in dead:
                del self.nodes[d]
                if d in self._adj:
                    del self._adj[d]
            self.edges = {k: w for k, w in self.edges.items() if k[0] not in dead and k[2] not in dead}
            # пересобрать индекс соседей
            self._rebuild_adj()
            removed = len(dead)
        return removed

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
        Один return: (found_path_or_None, next_frontier)."""
        nxt = []
        found = None
        if frontier:
            frontier = frontier[:max_fanout]  # не раздувать фронт без конца
        for cur, trail in frontier:
            for p, other, w in self.neighbors(cur):
                if other == b:
                    found = trail + [(cur, p, b, w)]
                    break
                if other not in visited:
                    visited.add(other)
                    nxt.append((other, trail + [(cur, p, other, w)]))
            if found is not None:
                break
        next_frontier = nxt
        if found is not None:
            next_frontier = []
        return (found, next_frontier)

    def path(self, a, b, max_depth=3, max_fanout=40):
        """Цепочка связей от a к b (если есть) — «рассуждение через граф».
        Один return: list-путь или None."""
        a, b = self._norm(a), self._norm(b)
        result = None
        if a in self.nodes and b in self.nodes:
            frontier = [(a, [(a, None, None, 1.0)])]
            visited = {a}
            for _ in range(max_depth):
                if result is not None or not frontier:
                    break
                result, frontier = self._step(frontier, b, visited, max_fanout)
        return result

    def explain(self, name, depth=1):
        """Связное объяснение понятия: сами факты + соседи."""
        name = self._norm(name)
        n = self.nodes.get(name)
        text = None
        if n:
            lines = [f"«{name}» — {n.tag}"]
            if n.facts:
                lines.append("Факты: " + "; ".join(n.facts[:5]))
            # соседи по силе связи (вес) — сначала самые «проводимые»
            ranked = sorted(self.neighbors(name), key=lambda r: -r[2])
            for p, other, w in ranked[:6]:
                lines.append(f"связано {p} с «{other}» (вес {w:.2f})")
            text = "\n".join(lines)
        return text

    def from_triples(self, triples):
        """Наполнить из списка (субъект, предикат, объект)."""
        for s, p, o in triples:
            self.add_edge(s, p, o)
        return len(triples)

    def save(self, path):
        """Сохраняет граф на диск (pickle). Один return: bool."""
        ok = False
        try:
            import pickle, os
            tmp = str(path) + ".tmp"
            with open(tmp, "wb") as f:
                pickle.dump({"nodes": self.nodes, "edges": self.edges}, f, protocol=4)
            os.replace(tmp, str(path))
            ok = True
        except Exception:
            ok = False
        return ok

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

    # ---------- обогащение ответа связями ----------
    def enrich(self, name, max_hop=2):
        """Находит родственные понятия и их факты для обогащения ответа.
        Возвращает список строк «related —связь→ other: факты». Один return: list."""
        name = self._norm(name)
        out = []
        if name in self.nodes:
            # соберём соседей до max_hop только по самым сильным связям
            seen_nodes = {name}
            candidates = {}  # Понятие -> (предикат, вес) от исходного узла
            frontier = [name]
            for _ in range(max_hop):
                nxt = []
                for cur in frontier:
                    for p, other, w in self._adj.get(cur, []):
                        if other not in seen_nodes and other not in candidates:
                            seen_nodes.add(other)
                            candidates[other] = (p, w)
                            nxt.append(other)
                frontier = nxt
            # ранжируем по весу, отдаём самое связанное
            ordered = sorted(candidates.items(), key=lambda kv: -kv[1][1])[:10]
            for other, (p, w) in ordered:
                node = self.nodes.get(other)
                if node and node.facts:
                    joined = "; ".join(node.facts[:3])
                    out.append(f"{name} {p} {other}: {joined}")
                elif other:
                    out.append(f"{name} {p} {other}")
        return out

    # ---------- умные запросы связей ----------
    def what_links(self, name, max_hop=1):
        """Все прямые и ближайшие связи понятия (уже есть neighbors, но с фактами).
        Один return: list строк."""
        name = self._norm(name)
        lines = []
        if name in self.nodes:
            node = self.nodes[name]
            if node.facts:
                lines.append(f"«{name}»: " + "; ".join(node.facts[:5]))
            for p, other, w in sorted(self.neighbors(name), key=lambda r: -r[2])[:8]:
                lines.append(f"{name} {p} {other} (вес {w:.2f})")
        return lines

    def similarity(self, a, b):
        """Насколько понятия связаны: число общих соседей / общий путь.
        Один return: float 0..1."""
        a, b = self._norm(a), self._norm(b)
        result = 0.0
        if a in self.nodes and b in self.nodes:
            na = {row[1] for row in self._adj.get(a, [])}
            nb = {row[1] for row in self._adj.get(b, [])}
            inter = na & nb
            union = na | nb
            if not union:
                # нет соседей ни у одного — проверяем прямую связь
                result = 1.0 if self.relation(a, b) else 0.0
            else:
                result = len(inter) / len(union)
        return result

    # ---------- обучение из отклика ----------
    def edge_weight(self, a, b):
        """Текущий активный вес связи (проводимость) между a и b. Один return: float.
        Идёт по индексу соседей; берём максимальную связь между узлами."""
        a, b = self._norm(a), self._norm(b)
        best = 0.0
        for p, other, w in self._adj.get(a, []):
            if other == b and w > best:
                best = w
        return best

    def reward(self, a, b, amount=0.3):
        """Положительный отклик: усилить связь между a и b (Хебб).
        Один return: int — сколько связей усилено."""
        return self.hebbian_learn(a, b, amount)

    def reward_sign(self, a, b, feedback_sign=1.0, amount=0.05):
        """Хебб-обновление связи по знаку отклика через обычный reward/punish.
        Один return: int — число изменённых связей."""
        changed = 0
        if feedback_sign >= 0:
            changed = self.hebbian_learn(a, b, amount)
        else:
            changed = self.punish(a, b, amount)
        return changed

    def punish(self, a, b, amount=0.3, floor=0.15):
        """Отрицательный отклик: ослабить связь (анти-Хебб). Один return: int."""
        a, b = self._norm(a), self._norm(b)
        punished = 0
        for (s, p, d), w in list(self.edges.items()):
            if (s == a and d == b) or (s == b and d == a):
                nw = max(floor, w - amount)
                self.edges[(s, p, d)] = nw
                self._set_adj_weight(s, p, d, nw)
                self._set_adj_weight(d, p, s, nw)
                punished += 1
        return punished

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
    """Вытаскивает пару понятий из запроса: два самых длинных узла графа,
    встречающихся в запросе. Один return: (a, b)."""
    q = _clean_q(q)
    found = [n for n in kg.nodes if n and len(n) > 2 and n in (" " + q + " ")]
    found.sort(key=len, reverse=True)
    pair = (None, None)
    if len(found) >= 2:
        pair = (found[0], found[1])
    elif len(found) == 1:
        pair = (found[0], None)
    return pair


def _answer_relation(a, b):
    """Прямая связь между a и b. Один return: str или None."""
    ans = None
    if a and b:
        rels = kg.relation(a, b)
        if rels:
            ans = ", ".join(f"«{a}» {p} «{b}»" for p, _w in rels) + "."
    return ans


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
    ans = None
    if path:
        ans = f"Прямой связи нет, но выводится: {_chain_text(path)}."
    return ans


def _answer_explain(q):
    """Объяснение понятия из запроса. Один return: str или None."""
    ans = None
    for name in kg.nodes:
        if "объясн" in q and name in q and len(name) > 3:
            ex = kg.explain(name)
            if ex:
                ans = ex
                break
    return ans


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


# ---------- интерфейс обогащения ответа (для ядра: try_enrich) ----------
def _extract_topic(query):
    """Пытается вытащить главное понятие из запроса (узел графа, кроме служебных).
    Один return: str или None."""
    q = _clean_q(query)
    stop = {"такое", "это", "связанное", "что", "как", "про", "расскажи",
            "объясни", "знаешь"}
    topic = None
    # узлы графа, встреченные в запросе, исключая служебные слова
    candidates = [n for n in kg.nodes if n and len(n) > 3 and n not in stop
                  and n in (" " + q + " ")]
    if candidates:
        topic = max(candidates, key=len)
    return topic


def _wants_links(q):
    """Явно ли запрос про связи/родственные понятия? Один return: bool."""
    return any(w in q for w in ("что связано", "связ", "родствен", "знаешь про",
                                "расскажи про", "что такое", "объясни", "связан",
                                "соедин", "ассоциац"))


def _clean_link_text(link):
    """Чистит одну связь «topic p other» от мусорных фрагментов.
    Возвращает None, если связь бессмысленна. Один return: str|None."""
    text = (link or "").strip(" |")
    if len(text) < 6:
        return None
    # мусорные объекты/хвосты: личные обращения, «насколько обида», «такое это смотри»
    lowered = text.lower()
    bad_markers = ("я хотел", "насколько", "обида", "такое это", "это такое",
                   "смотри намека", "хочешь поиграть", "могу дать тебе")
    if any(m in lowered for m in bad_markers):
        return None
    return text


def _we_contains_underscore(q):
    """Есть ли в запросе имя функции с подчёркиванием (bubble_sort, dijkstra)?
    Такие вопросы обрабатывает func_kb, а не граф связей. Один return: bool."""
    return bool(_re.search(r"[a-z]_\w+", (q or "").lower()))


def _we_is_algo_ask(q):
    """Вопрос похож на запрос алгоритма/функции (а не понятия-связи): содержит
    «алгоритм/сортировк/функция» + «расскажи/что делает/как работает/что такое».
    Такие уходят в func_kb, а не в граф связей. Один return: bool."""
    domain = ("сортировк", "алгоритм", "функци", "метод", "граф", "поиск", "стек")
    ask = ("расскажи", "что делает", "как работает", "что такое", "объясни", "что значит")
    hit = False
    for d in domain:
        if d in q:
            for a in ask:
                if a in q:
                    hit = True
                    break
            if hit:
                break
    return hit


def try_enrich(query):
    """Возвращает СВЯЗНЫЙ ответ родственными понятиями, либо None.
    Фильтрует мусорные связи и формулирует предложение вместо сырого «a|b|c».
    Отвечает только на явный запрос о связях. Один return: str или None."""
    ans = None
    q = (query or "").lower()
    # имя функции с подчёркиванием или явный вопрос об алгоритме обрабатывает func_kb
    if _we_contains_underscore(q) or _we_is_algo_ask(q):
        return ans
    if _wants_links(q):
        topic = _extract_topic(query)
        if topic:
            links = kg.enrich(topic, max_hop=2)
            good = [_clean_link_text(l) for l in links]
            good = [g for g in good if g]
            if good:
                # формулируем связно, не клеем «|»
                body = "; ".join(dict.fromkeys(good[:5]))
                ans = f"{topic[0].upper() + topic[1:]} — вот что я нахожу в связях: {body}."
    return ans


def try_what_links(query):
    """Отвечает про связи понятия («что связано с X?»). Один return: str или None."""
    ans = None
    q = (query or "").lower()
    # имя функции с подчёркиванием или алгоритм-вопрос — обрабатывает func_kb
    if _re.search(r"[a-z]_\w+", q) or _we_is_algo_ask(q):
        return ans
    q_raw = q
    if _wants_links(q_raw):
        q = _clean_q(query)
        name = _extract_topic(q)
        if name:
            lines = kg.what_links(name)
            if lines:
                ans = "\n".join(lines[:6])
    return ans


def try_similar(query):
    """Ищет в запросе два понятия и отвечает про их подобие. Один return: str или None."""
    ans = None
    q_raw = (query or "").lower()
    if any(w in q_raw for w in ("общего", "похож", "подоб", "сходств", "чем отлича", "в чём разниц")):
        a, b = _pair_from(_clean_q(query))
        if a and b:
            sim = kg.similarity(a, b)
            direct = kg.relation(a, b)
            if direct:
                ans = f"«{a}» и «{b}» напрямую связаны: " + ", ".join(f"{p}" for p, _ in direct[:3]) + f" (подобие {sim:.2f})."
            elif sim > 0:
                ans = f"«{a}» и «{b}» имеют общие понятия, подобие ≈ {sim:.2f}."
    return ans


# ---------- интерфейс обучения из отклика (для ядра: try_feedback) ----------
def try_feedback(a, b, positive=True):
    """Усиливает/ослабляет связь между a и b по отклику пользователя.
    Возвращает строку-отчёт. Один return: str."""
    n = 0
    act = "усилил"
    if positive:
        n = kg.reward(a, b)
        act = "усилил"
    else:
        n = kg.punish(a, b)
        act = "ослабил"
    msg = f"Граф: связи «{a}»↔«{b}» нет, учить нечего."
    if n:
        msg = f"Граф: {act} связь «{a}»↔«{b}» ({n} связей)."
    return msg


def _pair_from_text(q):
    """Вытаскивает пару понятий из свободного текста «a связан с b». Один return: (a,b)."""
    m = _re.search(r"\b([^\s]+?)\s+(?:связан\s+с|связан|и|с)\s+([^\s]+?)[\s?.,]*$", q.lower())
    pair = (None, None)
    if m:
        pair = (m.group(1), m.group(2))
    return pair


def try_feedback_text(query, positive=True):
    """parse отклик из текста («нейрон связан с мыслью» + лайк). Один return: str."""
    a, b = _pair_from_text(query)
    msg = "Граф: не нашёл пару понятий для обучения."
    if a and b:
        msg = try_feedback(a, b, positive)
    return msg


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
    print("--- обогащение ---")
    print(try_enrich("расскажи про нейрон"))
    print("--- связи ---")
    print(try_what_links("что связано с память?"))
    print("--- подобие ---")
    print(try_similar("что общего у нейрона и сигнала?"))