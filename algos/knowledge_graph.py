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
        self._cache = {}     # кэш дорогих вычислений (connectivity/closest_concepts)

    # ---------- построение ----------
    def add_node(self, name, tag="понятие", facts=None, weight=1.0):
        name = self._norm(name)
        if not name:
            return
        try:
            weight = float(weight)
        except Exception:
            weight = 1.0
        if weight != weight:
            weight = 1.0
        if weight > 1e6 or weight < -1e6:
            weight = max(-1e6, min(1e6, weight)) if weight == weight else 1.0
        if name not in self.nodes:
            self.nodes[name] = Node(name, tag, facts, weight)
            self._adj[name] = []
        elif facts:
            self.nodes[name].facts = list(dict.fromkeys(self.nodes[name].facts + facts))
        return self.nodes.get(name) if name in self.nodes else None

    def get_node(self, name):
        """Безопасный доступ к узлу по имени (могут быть None/неверное имя).
        Один return: Node|None."""
        if not isinstance(name, str):
            return None
        return self.nodes.get(self._norm(name))

    # ---------- пополнение графа из провалов (замыкание цикла рефлексии) ----------
    def admit_candidate(self, first, second="", weight=0.3, tag="пополнение"):
        """Принимает в граф понятие, на которое сослалась рефлексия («тема вне
        графа»). Отсутствующий узел создаётся с меткой tag (а не безликой
        «понятие»), затем понятия связываются ребром «связано_с». Пустые/
        не-строковые понятия и петли пропускаются. Один return: dict —
        что реально изменилось: {nodes_added, edge_added, a, b}."""
        a = self._norm(first) if isinstance(first, str) else ""
        b = self._norm(second) if isinstance(second, str) else ""
        added = 0
        if a and a not in self.nodes:
            self.add_node(a, tag=tag)
            added += 1
        if b and b not in self.nodes:
            self.add_node(b, tag=tag)
            added += 1
        edge_added = 0
        if a and b and a != b and not self.has_edge(a, "связано_с", b):
            self.add_edge(a, "связано_с", b, weight=weight)
            edge_added = 1
        return {"nodes_added": added, "edge_added": edge_added, "a": a, "b": b}

    def still_outside(self, first, second=""):
        """Понятия, которых в графе НЕТ (перепроверка перед записью «кандидат»).
        Пустые/не-строковые отбрасываются. Один return: list[str]."""
        names = [n for n in (first, second) if isinstance(n, str) and self._norm(n)]
        return [self._norm(n) for n in names if self._norm(n) not in self.nodes]

    def has_edge(self, src, pred, dst):
        """Есть ли прямая связь между src и dst по предикату pred.
        Некорректные аргументы → False. Один return: bool."""
        if not src or not pred or not dst:
            return False
        s, p, d = self._norm(src), self._norm(pred), self._norm(dst)
        return (s, p, d) in self.edges

    def degree_of(self, name):
        """Степень узла (число рёбер). Неизвестный/некорректный узел → 0.
        Один return: int."""
        name = self._norm(name)
        if not name:
            return 0
        return len(self._adj.get(name, []))

    def all_tags(self):
        """Множество всех тегов узлов. Один return: set."""
        return {n.tag for n in self.nodes.values()
                if hasattr(n, "tag") and isinstance(n.tag, str) and n.tag}

    def linked_nodes(self, name):
        """Имена всех узлов, напрямую связанных с данным (по индексу).
        Неизвестный/некорректный узел → []. Один return: list."""
        name = self._norm(name)
        if not name:
            return []
        return [row[1] for row in self._adj.get(name, [])
                if isinstance(row, (tuple, list)) and len(row) >= 2
                and isinstance(row[1], str)]

    def edge_sources(self, pred):
        """Все узлы-источники для заданного предиката. Не-строковый/пустой
        предикат → []. Один return: list."""
        p = self._norm(pred) if isinstance(pred, str) else ""
        if not p:
            return []
        return sorted({k[0] for k in self.edges
                       if isinstance(k, (tuple, list)) and len(k) >= 2
                       and k[1] == p and isinstance(k[0], str)})

    def prune_self_loops(self):
        """Удаляет петли (рёбра, где источник и цель совпадают) и возвращает их число.
        Часто появляются из-за ошибок парсинга. Один return: int."""
        self_loops = [k for k in self.edges
                      if isinstance(k, (tuple, list)) and len(k) >= 2
                      and k[0] == k[2]]
        for k in self_loops:
            del self.edges[k]
        if self_loops:
            self._rebuild_adj()
        return len(self_loops)

    def count_edges_between(self, a, b):
        """Число прямых связей между двумя узлами (в любом направлении).
        Некорректные аргументы → 0. Один return: int."""
        if not a or not b:
            return 0
        a, b = self._norm(a), self._norm(b)
        count = 0
        for k in self.edges:
            if not (isinstance(k, (tuple, list)) and len(k) >= 2):
                continue
            if (k[0] == a and k[2] == b) or (k[0] == b and k[2] == a):
                count += 1
        return count

    def remove_node(self, name):
        """Удаляет узел и все связанные с ним рёбра. Возвращает число удалённых
        рёбер, или 0 если узел не найден. Не-строковое имя → 0. Один return: int."""
        if not isinstance(name, str):
            return 0
        name = self._norm(name)
        if name not in self.nodes:
            return 0
        removed = 0
        for k in list(self.edges):
            if not (isinstance(k, (tuple, list)) and len(k) >= 2):
                continue
            if k[0] == name or k[2] == name:
                del self.edges[k]
                removed += 1
        del self.nodes[name]
        if name in self._adj:
            del self._adj[name]
        if removed:
            self._rebuild_adj()
        return removed

    def count_nodes(self):
        """Число узлов в графе. Один return: int."""
        return len(self.nodes)

    def count_edges(self):
        """Число рёбер в графе. Один return: int."""
        return len(self.edges)

    def get_edge_weight(self, src, pred, dst):
        """Вес конкретного ребра (src, pred, dst) или 0.0, если его нет.
        Некорректные аргументы → 0.0. Один return: float."""
        if not src or not pred or not dst:
            return 0.0
        s, p, d = self._norm(src), self._norm(pred), self._norm(dst)
        return self.edges.get((s, p, d), 0.0)

    def edge_pairs(self):
        """Все уникальные пары (источник, цель) с объединённым максимальным весом.
        Пропускает петли. Один return: list of (src, dst, weight)."""
        pairs = {}
        for k, w in self.edges.items():
            if not (isinstance(k, (tuple, list)) and len(k) >= 3):
                continue
            s, p, d = k[0], k[1], k[2]
            if not (isinstance(s, str) and isinstance(d, str)) or s == d:
                continue
            pair_key = (s, d) if (s, d) in pairs else (d, s)
            pairs[pair_key] = max(pairs.get(pair_key, 0.0), w)
        return [(s, d, w) for (s, d), w in sorted(pairs.items())]

    def subgraph(self, node_names):
        """Подграф, содержащий только указанные узлы (и рёбра между ними).
        Не-строковые элементы списка игнорируются. Один return: list of edges."""
        if not isinstance(node_names, (list, tuple, set)):
            return []
        keep = {self._norm(n) for n in node_names if isinstance(n, str)}
        return [(k, w) for k, w in self.edges.items()
                if isinstance(k, (tuple, list)) and len(k) >= 2
                and k[0] in keep and k[2] in keep]

    def merge_nodes(self, target, alias):
        """Сливает узел alias в узел target: переносит все рёбра alias на target.
        Возвращает число перенесённых связей. Неизвестные узлы → 0. Один return: int."""
        target, alias = self._norm(target), self._norm(alias)
        if target == alias or not target or not alias:
            return 0
        if alias not in self.nodes:
            return 0
        moved = 0
        for k in list(self.edges):
            if not (isinstance(k, (tuple, list)) and len(k) >= 3):
                continue
            s, p, d = k
            if s == alias:
                nk = (target, p, d)
                self.edges[nk] = max(self.edges.get(nk, 0.0), self.edges[k])
                del self.edges[k]
                moved += 1
            elif d == alias:
                nk = (s, p, target)
                self.edges[nk] = max(self.edges.get(nk, 0.0), self.edges[k])
                del self.edges[k]
                moved += 1
        del self.nodes[alias]
        if alias in self._adj:
            del self._adj[alias]
        if moved:
            self._rebuild_adj()
        return moved

    def path_exists(self, a, b, max_depth=3, max_visited=4000):
        """Есть ли путь между двумя узлами (по рёбрам, без учёта направления)?
        Использует BFS с ограничением глубины и числа посещённых вершин.
        Некорректные аргументы → False. Один return: bool."""
        if not isinstance(a, str) or not isinstance(b, str) or a == b:
            return False
        a, b = self._norm(a), self._norm(b)
        if a not in self.nodes or b not in self.nodes:
            return False
        visited = {a}
        frontier = [a]
        for _ in range(max_depth):
            if len(visited) >= max_visited:
                break
            nxt = []
            for cur in frontier:
                for row in self._adj.get(cur, []):
                    if not (isinstance(row, (tuple, list)) and len(row) >= 2):
                        continue
                    other = row[1]
                    if other == b:
                        return True
                    if other not in visited:
                        visited.add(other)
                        nxt.append(other)
            frontier = nxt
            if not frontier:
                break
        return False

    def get_all_neighbors(self, name):
        """Все различные соседи узла как список (сосед, предикат, вес).
        То же, что neighbors(), но возвращает копию кортежей, безопасную для
        использования вне класса. Неизвестный узел → []. Один return: list."""
        name = self._norm(name)
        if not name:
            return []
        rows = self._adj.get(name, [])
        return [row for row in rows
                if isinstance(row, (tuple, list)) and len(row) >= 2
                and isinstance(row[0], str) and isinstance(row[1], str)]

    def node_weights(self):
        """Словарь весов всех узлов (name -> weight). Один return: dict."""
        return {n: getattr(node, "weight", 1.0) for n, node in self.nodes.items()}

    def popular_relations(self, top_n=10):
        """Самые частые предикаты и их число вхождений, убывающе отсортированные.
        Нечисловой top_n → 10. Один return: list of (predicate, count)."""
        try:
            top_n = max(1, int(top_n))
        except Exception:
            top_n = 10
        counts = {}
        for k in self.edges:
            if not (isinstance(k, (tuple, list)) and len(k) >= 2):
                continue
            if isinstance(k[1], str):
                counts[k[1]] = counts.get(k[1], 0) + 1
        ranked = sorted(counts.items(), key=lambda x: -x[1])[:top_n]
        return [(p, c) for p, c in ranked]

    def mutual_neighbors(self, a, b):
        """Общие соседи двух узлов. Неизвестные узлы → []. Один return: list."""
        if not isinstance(a, str) or not isinstance(b, str) or a == b:
            return []
        a, b = self._norm(a), self._norm(b)
        na = {row[0] for row in self._adj.get(a, [])
              if isinstance(row, (tuple, list)) and len(row) >= 2 and isinstance(row[0], str)}
        nb = {row[0] for row in self._adj.get(b, [])
              if isinstance(row, (tuple, list)) and len(row) >= 2 and isinstance(row[0], str)}
        return sorted(na & nb)

    def get_node_facts(self, name):
        """Список фактов, связанных с узлом. Неизвестный узел → [].
        Один return: list."""
        node = self.get_node(name)
        if node is None:
            return []
        return list(node.facts or [])

    def tag_counts(self):
        """Количество узлов по тэгам. Один return: dict (tag -> count)."""
        counts = {}
        for node in self.nodes.values():
            tag = getattr(node, "tag", None)
            if isinstance(tag, str) and tag:
                counts[tag] = counts.get(tag, 0) + 1
        return counts

    def connected_components(self):
        """Список компонент связности графа (каждая — список узлов).
        Один return: list of lists."""
        nbrs = {}
        for k in self.edges:
            if not (isinstance(k, (tuple, list)) and len(k) >= 2):
                continue
            s, d = k[0], k[2]
            if isinstance(s, str) and isinstance(d, str):
                nbrs.setdefault(s, set()).add(d)
                nbrs.setdefault(d, set()).add(s)
        seen = set()
        comps = []
        for node in self.nodes:
            if node in seen:
                continue
            stack = [node]
            seen.add(node)
            comp = []
            while stack:
                cur = stack.pop()
                comp.append(cur)
                for nxt in nbrs.get(cur, ()):
                    if nxt not in seen:
                        seen.add(nxt)
                        stack.append(nxt)
            comps.append(comp)
        return comps

    def top_edges(self, top_n=10):
        """Самые «сильные» рёбра по весу (сначала самые большие). Нечисловой
        top_n → 10. Один return: list of (src, pred, dst, weight)."""
        try:
            top_n = max(1, int(top_n))
        except Exception:
            top_n = 10
        def key(e):
            try:
                return -float(e[1]) if len(e) > 1 and e[1] is not None else 0.0
            except (TypeError, ValueError):
                return 0.0
        edges = [(k[0], k[1], k[2], w) for k, w in self.edges.items()
                 if isinstance(k, (tuple, list)) and len(k) >= 3
                 and isinstance(k[0], str) and isinstance(k[2], str)]
        edges.sort(key=lambda e: -e[3] if isinstance(e[3], (int, float)) and not (e[3] != e[3]) else 0.0)
        return edges[:top_n]

    def add_edge(self, src, pred, dst, weight=1.0):
        s, d = self._norm(src), self._norm(dst)
        p = self._norm(pred)
        if not s or not d or s == d or not p or len(p) > 120:
            return
        try:
            weight = float(weight)
        except Exception:
            weight = 1.0
        if weight != weight or weight in (float("inf"), float("-inf")):
            weight = 1.0
        if weight > 1e6 or weight < -1e6:
            weight = max(-1e6, min(1e6, weight)) if weight == weight else 1.0
        self.add_node(s)
        self.add_node(d)
        key = (s, p, d)
        old = self.edges.get(key)
        # нет ребра — берём переданный вес как есть (иначе отрицательная связь
        # молча становилась бы нулевой через max с 0.0), есть — «сильнее по модулю»
        self.edges[key] = weight if old is None else max(old, weight, key=abs)
        # синхронизируем вес в индексе соседей (двусторонне)
        self._set_adj_weight(s, p, d, self.edges[key])
        self._set_adj_weight(d, p, s, self.edges[key])

    def _set_adj_weight(self, from_node, pred, to_node, weight):
        """Обновляет вес связи в _adj для направления from_node->to_node.
        Пустые узлы игнорируются. Один return: None."""
        if not from_node or not to_node:
            return None
        try:
            weight = float(weight)
        except (TypeError, ValueError):
            return None
        if weight != weight or weight in (float("inf"), float("-inf")):
            return None
        rows = self._adj.setdefault(from_node, [])
        # предикат в индексе нормализован (add_edge передаёт норму), поэтому
        # сравниваем с нормой: иначе зеркальный вес не находился при «P»/«p»
        pred_key = self._norm(pred) if isinstance(pred, str) else pred
        kept = [row for row in rows
                if not (isinstance(row, (tuple, list)) and len(row) >= 2
                        and row[0] == pred_key and row[1] == to_node)]
        # индекс показывает силу самой связи: максимум по модулю из веса самой
        # связи и из ОБРАТНОГО ребра (a->b 1.0 при b->a 0.6 даёт 1.0 обоим).
        # Устаревшее значение этой же строки не учитываем — иначе ослабление
        # (punish) не доходило бы до edge_weight()
        candidates = [weight]
        mirrored = self.edges.get((to_node, pred_key, from_node))
        own = self.edges.get((from_node, pred_key, to_node))
        if self._is_num(mirrored):
            candidates.append(float(mirrored))
        if self._is_num(own):
            candidates.append(float(own))
        kept.append((pred_key, to_node, max(candidates, key=abs)))
        self._adj[from_node] = kept
        return None

    def hebbian_learn(self, node_a, node_b, amount=0.2, depth=0):
        """Синаптическая пластичность: если два узла активировались вместе —
        связь между ними усиливается (Хебб). Если depth>0, попутно усиливаются
        соседи первого хопа (рост размерности/связности активированного блока).
        amount<=0 или пустые узлы игнорируются. Один return: int — число
        укреплённых рёбер."""
        try:
            amount = float(amount)
        except Exception:
            amount = 0.0
        if amount != amount or amount <= 0 or not node_a or not node_b:
            return 0
        a, b = self._norm(node_a), self._norm(node_b)
        strengthened = 0
        try:
            depth = int(depth)
        except Exception:
            depth = 0
        targets = [b]
        # если явного ребра a↔b ещё нет, но оба узла уже есть в графе — создаём
        # его (Хебб «fire together, wire together»). Иначе цель награды (b)
        # пропускалась бы, а при depth>0 укреплялись бы только соседи a.
        if a in self.nodes and b in self.nodes and a != b and not self.edge_weight(a, b):
            self.add_edge(a, "связано_с", b, weight=amount)
            strengthened += 1
        if depth > 0:
            for p, other, _w in self._adj.get(a, [])[:depth]:
                if other != b and other not in targets:
                    targets.append((other, _w))
        # цель усиливается полной amount; соседи-кандидаты depth — пропорционально
        # силе их связи с a, чтобы шумный слабый сосед не получал ту же награду,
        # что и сама цель
        for tgt_spec in targets:
            if isinstance(tgt_spec, tuple):
                tgt, tgt_w = tgt_spec
                try:
                    tgt_w = float(tgt_w)
                except (TypeError, ValueError):
                    tgt_w = 1.0
                if tgt_w != tgt_w or tgt_w < 0:
                    tgt_w = 1.0
            else:
                tgt, tgt_w = tgt_spec, 1.0
            use_amount = amount if tgt == b else amount * min(1.0, tgt_w)
            if use_amount <= 0:
                continue
            for key, w in list(self.edges.items()):
                if not (isinstance(key, (tuple, list)) and len(key) == 3):
                    continue
                s, p, d = key
                if (s == a and d == tgt) or (s == tgt and d == a):
                    nw = min(2.0, w + use_amount)
                    if nw == w:
                        # вес уже на потолке/границе — реального изменения нет,
                        # не сообщаем «усилил» (иначе no-op выглядел бы как факт)
                        continue
                    self.edges[key] = nw
                    self._set_adj_weight(s, p, d, nw)
                    self._set_adj_weight(d, p, s, nw)
                    strengthened += 1
        return strengthened

    def synapse_decay(self, amount=0.01, floor=0.2):
        """Все связи медленно слабеют (редко используемые «атрофируются»),
        как забывание. amount<0/floor<0 игнорируются, веса коерсируются в float.
        Один return: int — число изменённых связей."""
        try:
            amount = float(amount)
            floor = float(floor)
        except Exception:
            amount, floor = 0.01, 0.2
        if amount != amount or floor != floor:
            amount, floor = 0.01, 0.2
        if amount < 0 or floor < 0:
            return 0
        changed = 0
        for key, w in list(self.edges.items()):
            if not (isinstance(key, (tuple, list)) and len(key) == 3):
                continue
            try:
                w = float(w)
            except Exception:
                continue
            nw = max(floor, w - amount)
            if nw != nw or nw in (float("inf"), float("-inf")):
                continue
            if nw != w:
                self.edges[key] = nw
                s, p, d = key
                self._set_adj_weight(s, p, d, nw)
                self._set_adj_weight(d, p, s, nw)
                changed += 1
        return changed

    _EDGE_JUNK = " \t.,!?;:—–-«»\"'()[]"

    @staticmethod
    def _norm(name):
        name = name if isinstance(name, str) else str(name or "")
        cleaned = _re.sub(r"\s+", " ", name).strip().lower()
        return cleaned.strip(KnowledgeGraph._EDGE_JUNK)[:200]

    @staticmethod
    def _is_num(x):
        """Конечное число (не NaN/inf/строка). Один return: bool."""
        return isinstance(x, (int, float)) and x == x and x not in (float("inf"), float("-inf"))

    def prune_noise(self, noise_preds=None, max_phrase_words=4):
        """Убирает мусор: рёбра с шумовыми предикатами («это», «есть», «если»)
        и узлы-фразы длиннее max_phrase_words слов (корпусный шум, не понятия).
        Один return: int — число удалённых элементов (узлы+рёбра+предикаты)."""
        removed = 0
        try:
            max_phrase_words = int(max_phrase_words)
        except Exception:
            max_phrase_words = 4
        if max_phrase_words < 1:
            max_phrase_words = 4
        if noise_preds is None:
            noise_preds = {"это", "есть", "если", "является", "и", "или", ",", ".", "-"}
        elif isinstance(noise_preds, str):
            noise_preds = {noise_preds}
        elif not isinstance(noise_preds, (set, list, tuple)):
            noise_preds = set()
        # 1) рёбра с шумовыми предикатами
        dead_edges = [
            k for k in self.edges
            if isinstance(k, (tuple, list)) and len(k) >= 2
            and isinstance(k[1], str) and self._norm(k[1]) in noise_preds
        ]
        for k in dead_edges:
            del self.edges[k]
        removed += len(dead_edges)
        # 2) узлы-фразы (корпусные): слишком длинные, не чистые понятия
        dead_nodes = set()
        for n in self.nodes:
            if " " in n and len(n.split()) > max_phrase_words:
                dead_nodes.add(n)
        for d in dead_nodes:
            del self.nodes[d]
            if d in self._adj:
                del self._adj[d]
        removed += len(dead_nodes)
        if dead_nodes:
            self.edges = {
                k: w for k, w in self.edges.items()
                if not (isinstance(k, (tuple, list)) and len(k) >= 3
                        and (k[0] in dead_nodes or k[2] in dead_nodes))
            }
            self._rebuild_adj()
        return removed

    def prune_stopwords(self, stopwords):
        """Удаляет узлы-связки (мусорные слова типа «однако», «затем») из графа
        и связанные с ними рёбра. Один return: int — число удалённых узлов."""
        removed = 0
        if not isinstance(stopwords, (list, tuple, set, frozenset, dict)):
            return 0
        stopwords = set(stopwords)
        if stopwords:
            dead = {
                n for n in self.nodes
                if isinstance(n, str) and (n in stopwords or n.strip() in stopwords)
            }
            for d in dead:
                del self.nodes[d]
                if d in self._adj:
                    del self._adj[d]
            self.edges = {
                k: w for k, w in self.edges.items()
                if not (isinstance(k, (tuple, list)) and len(k) >= 3
                        and (k[0] in dead or k[2] in dead))
            }
            # пересобрать индекс соседей
            self._rebuild_adj()
            removed = len(dead)
        return removed

    # ---------- вопросы ----------
    def _forward_links(self, name):
        """Исходящие связи узла (p, other, w). Один return: list."""
        name = self._norm(name)
        rows = self._adj.get(name, [])
        if not isinstance(rows, (list, tuple)):
            rows = []
        return [row for row in rows if isinstance(row, (tuple, list)) and len(row) >= 2]

    def neighbors(self, name):
        """Все прямые связи узла по индексу. Один return: list."""
        name = self._norm(name)
        rows = self._adj.get(name, [])
        if not isinstance(rows, (list, tuple)):
            rows = []
        return [row for row in rows if isinstance(row, (tuple, list)) and len(row) >= 2]

    def relation(self, a, b):
        """Прямые отношения между a и b (по индексу, без дублей). Один return: list."""
        a, b = self._norm(a), self._norm(b)
        seen = set()
        rels = []
        for row in self._adj.get(a, []):
            if not (isinstance(row, (list, tuple)) and len(row) >= 3):
                continue
            p, other, w = row
            if other == b and (p, w) not in seen:
                seen.add((p, w))
                rels.append((p, w))
        for row in self._adj.get(b, []):
            if not (isinstance(row, (list, tuple)) and len(row) >= 3):
                continue
            p, other, w = row
            if other == a and (p, w) not in seen:
                seen.add((p, w))
                rels.append((p, w))
        return rels

    def _step(self, frontier, b, visited, max_fanout=40, max_visited=4000):
        """Один шаг BFS: из текущего фронта к b, ограничен размахом и числом
        посещённых вершин (max_visited), чтобы не уйти в долгий обход на
        огромных графах. Один return: (found_path_or_None, next_frontier)."""
        try:
            max_fanout = max(1, int(max_fanout))
            max_visited = max(1, int(max_visited))
        except Exception:
            max_fanout, max_visited = 40, 4000
        nxt = []
        found = None
        if frontier:
            frontier = frontier[:max_fanout]  # не раздувать фронт без конца
        for entry in frontier:
            if not (isinstance(entry, (tuple, list)) and len(entry) >= 2):
                continue
            cur, trail = entry[0], entry[1]
            for nbr in self.neighbors(cur):
                if not (isinstance(nbr, (tuple, list)) and len(nbr) >= 3):
                    continue
                p, other, w = nbr
                if other == b:
                    found = trail + [(cur, p, b, w)]
                    break
                if other not in visited and len(visited) < max_visited:
                    visited.add(other)
                    nxt.append((other, trail + [(cur, p, other, w)]))
            if found is not None or len(visited) >= max_visited:
                break
        next_frontier = nxt
        if found is not None:
            next_frontier = []
        return (found, next_frontier)

    def path(self, a, b, max_depth=3, max_fanout=40, max_visited=4000):
        """Цепочка связей от a к b (если есть) — «рассуждение через граф».
        Ограничено числом посещённых вершин (защита от долгих обходов).
        Один return: list-путь или None."""
        a, b = self._norm(a), self._norm(b)
        result = None
        try:
            max_depth = max(1, min(20, int(max_depth)))
            max_fanout = max(1, int(max_fanout))
            max_visited = max(1, int(max_visited))
        except Exception:
            max_depth = 3
        if a in self.nodes and b in self.nodes:
            frontier = [(a, [(a, None, None, 1.0)])]
            visited = {a}
            for _ in range(max_depth):
                if result is not None or not frontier:
                    break
                result, frontier = self._step(frontier, b, visited, max_fanout, max_visited)
        return result

    def explain(self, name, depth=1):
        """Связное объяснение понятия: сами факты + соседи."""
        name = self._norm(name)
        n = self.nodes.get(name)
        text = None
        try:
            depth = max(1, min(6, int(depth)))
        except Exception:
            depth = 1
        if n:
            lines = [f"«{name}» — {n.tag}"]
            if n.facts:
                lines.append("Факты: " + "; ".join(n.facts[:5]))
            # соседи по силе связи (вес) — сначала самые «проводимые»
            safe_nbrs = []
            for r in self.neighbors(name):
                if not (isinstance(r, (tuple, list)) and len(r) >= 3):
                    continue
                try:
                    fw = float(r[2])
                except (TypeError, ValueError):
                    continue
                if fw != fw:
                    continue
                safe_nbrs.append(r)
            try:
                ranked = sorted(safe_nbrs, key=lambda r: float(r[2]))
                ranked.reverse()
            except Exception:
                ranked = safe_nbrs
            for p, other, w in ranked[:6]:
                if not _is_noisy_predicate(p) and _is_meaningful_other(other, name):
                    lines.append(f"{p} → «{other}» (вес {float(w):.2f})")
            has_details = bool(n.facts) or len(lines) > 1
            text = "\n".join(lines) if has_details else None
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
            # Не затираем большой граф пустым: тесты и скрипты из reports/ сохраняют
            # свежесозданный граф из пары узлов и обнуляли models/knowledge_graph.pkl
            too_small = (len(self.nodes) < 100 and os.path.exists(str(path))
                         and os.path.getsize(str(path)) > 1_000_000)
            if not too_small:
                tmp = str(path) + ".tmp"
                with open(tmp, "wb") as f:
                    pickle.dump({"nodes": self.nodes, "edges": self.edges}, f, protocol=4)
                os.replace(tmp, str(path))
                ok = True
        except Exception:
            ok = False
        return ok

    def load(self, path):
        """Загружает граф с диска; если файла нет или он битый — пустой граф.
        Битый pickle и структурно неверный бэкап (nodes не dict, edges=None,
        ключи не тройки строк) не оставляют граф в полуразобранном состоянии:
        данные валидируются ДО записи в self. Один return: int (рёбер)."""
        data = self._read_pickle(path)
        nodes = _load_valid_nodes(data)
        edges = _load_valid_edges(data)
        # очищаем и пишем только после успешной валидации
        self.nodes = {}
        self.edges = {}
        self._adj = {}
        self.nodes = nodes
        self.edges = edges
        self._rebuild_adj()
        return len(self.edges)

    @staticmethod
    def _read_pickle(path):
        """Читает pickle-дамп; любая ошибка (нет файла, битый байткод,
        неподдерживаемый класс) → None. Один return: dict|None."""
        data = None
        try:
            import pickle
            with open(str(path), "rb") as f:
                loaded = pickle.load(f)
            data = loaded if isinstance(loaded, dict) else None
        except Exception:
            data = None
        return data

    def _rebuild_adj(self):
        """Пересобирает индекс соседей из рёбер. Один return: None."""
        self._adj = {n: [] for n in self.nodes if isinstance(n, str)}
        for key, w in self.edges.items():
            if not (isinstance(key, (tuple, list)) and len(key) == 3):
                continue
            s, p, d = key
            if not (isinstance(s, str) and isinstance(d, str) and isinstance(p, str)):
                continue
            self._adj.setdefault(s, []).append((p, d, w))
            self._adj.setdefault(d, []).append((p, s, w))
        # граф изменился — сбрасываем кэш дорогих вычислений
        self._cache = {}
        return None

    # ---------- обогащение ответа связями ----------
    def enrich(self, name, max_hop=2):
        """Находит родственные понятия и их факты для обогащения ответа.
        Возвращает список строк «related —связь→ other: факты». Один return: list."""
        name = self._norm(name)
        out = []
        try:
            max_hop = max(1, min(5, int(max_hop)))
        except Exception:
            max_hop = 2
        if name in self.nodes:
            # соберём соседей до max_hop только по самым сильным связям
            seen_nodes = {name}
            candidates = {}  # Понятие -> (предикат, вес) от исходного узла
            frontier = [name]
            for _ in range(max_hop):
                nxt = []
                for cur in frontier:
                    rows = self._adj.get(cur, [])
                    if not isinstance(rows, (list, tuple)):
                        rows = []
                    for p, other, w in rows:
                        is_link = (isinstance(other, str) and isinstance(w, (int, float))
                                   and not _is_noisy_predicate(p))
                        if is_link and other not in seen_nodes and other not in candidates:
                            seen_nodes.add(other)
                            candidates[other] = (p, w)
                            nxt.append(other)
                frontier = nxt
            # ранжируем по весу, отдаём самое связанное (без корпусных фраз-шума)
            junk_neighbors = {"откуда", "нашел", "нашла", "найти", "хочешь", "давай",
                              "спросить", "скажи", "посмотрю", "сделаю", "можно", "тебя"}
            filtered = {}
            for o, (p, w) in candidates.items():
                if not isinstance(o, str) or not o.strip() or " " in o.strip():
                    continue
                try:
                    w = float(w)
                except Exception:
                    continue
                oclean = o.split()[0]
                if len(o) <= 24 and oclean not in junk_neighbors:
                    filtered[o] = (p, w)
            ordered = sorted(filtered.items(), key=lambda kv: -kv[1][1])[:10]
            for other, (p, w) in ordered:
                node = self.nodes.get(other)
                if node and node.facts:
                    joined = "; ".join(node.facts[:3])
                    out.append(f"{name} {p} {other}: {joined}")
                elif other:
                    out.append(f"{name} {p} {other}")
        return out

    def dedupe_nodes(self, top_groups=100):
        """Сжатие: сливает узлы-дубли (словоформы одного понятия: «граф/графа/
        графе») в один канонический узел, перенаправляя на него рёбра.
        Один return: int — число удалённых узлов-дублей."""
        import re as _re_d
        removed = 0

        def stem(w):
            w = w.lower().strip()
            for suf in ("ться", "ность", "ного", "ной", "ное", "нии", "тый",
                        "ый", "ая", "ой", "ее", "ие", "их", "ам", "ами", "ой",
                        "е", "а", "и", "ы", "у", "ю", "о"):
                if len(w) > len(suf) + 3 and w.endswith(suf):
                    return w[:-len(suf)]
            return w

        from collections import defaultdict
        groups = defaultdict(list)
        for n in self.nodes:
            if " " not in n and len(n) > 3:
                groups[stem(n)].append(n)

        merged = 0
        for key, variants in groups.items():
            if merged >= top_groups:
                break
            if len(variants) < 2:
                continue
            canon = min(variants, key=len)
            dups = [v for v in variants if v != canon]
            for d in dups:
                # перенаправляем рёбра с узла-дубля на канонический
                for key, w in list(self.edges.items()):
                    if not (isinstance(key, (tuple, list)) and len(key) == 3):
                        continue
                    s, p, t = key
                    if s == d:
                        self.edges[(canon, p, t)] = w if (canon, p, t) not in self.edges else max(w, self.edges[(canon, p, t)])
                        del self.edges[key]
                    elif t == d:
                        self.edges[(s, p, canon)] = w if (s, p, canon) not in self.edges else max(w, self.edges[(s, p, canon)])
                        del self.edges[key]
                if d in self.nodes:
                    del self.nodes[d]
                if d in self._adj:
                    del self._adj[d]
                removed += 1
                merged += 1
        if removed:
            self._rebuild_adj()
        return removed

    def consolidate(self, min_weight=0.15, max_phrase_words=4):
        """Автоочистка и консолидация: удаляет слабые рёбра ниже порога и
        узлы-фразы длиннее порога. Рост плотности за счёт смысла, а не шума.
        Один return: int — число удалённых элементов (рёбра+узлы)."""
        removed = 0
        try:
            min_weight = float(min_weight)
        except Exception:
            min_weight = 0.15
        if min_weight != min_weight or min_weight < 0:
            min_weight = 0.15
        try:
            max_phrase_words = int(max_phrase_words)
        except Exception:
            max_phrase_words = 4
        if max_phrase_words < 1:
            max_phrase_words = 4
        # рёбра ниже порога (шум от частых пар) — убираем
        weak = [k for k, w in self.edges.items() if w < min_weight]
        for k in weak:
            del self.edges[k]
        removed += len(weak)
        # узлы-фразы длиннее порога (корпусный мусор)
        dead = set()
        for n in self.nodes:
            if " " in n and len(n.split()) > max_phrase_words:
                dead.add(n)
        for d in dead:
            del self.nodes[d]
            if d in self._adj:
                del self._adj[d]
        if dead:
            self.edges = {
                k: w for k, w in self.edges.items()
                if not (isinstance(k, (tuple, list)) and len(k) >= 3
                        and (k[0] in dead or k[2] in dead))
            }
            self._rebuild_adj()
        removed += len(dead)
        return removed

    # ---------- умные запросы связей ----------
    def bridge_components(self, max_edges=2000, weight=0.25, sample_conn=None):
        """Семантический мост: связывает изолированные узлы (без рёбер) со
        связными через общее значащее слово. Сращивает компоненты графа в одну
        сеть. Один return: int — число добавленных рёбер."""
        import re as _re_b
        connected = set()
        for key in self.edges:
            if isinstance(key, (tuple, list)) and len(key) >= 3:
                connected.add(key[0])
                connected.add(key[2])
        isolated = [n for n in self.nodes if n not in connected]
        if sample_conn and len(connected) > sample_conn:
            import random as _rnd
            connected = set(_rnd.sample(list(connected), sample_conn))
        stop = {"это", "что", "как", "для", "на", "в", "по", "с", "из", "и", "или"}
        added = 0
        # для быстрого поиска: слово -> связные узлы, содержащие его (по одному на слово)
        word_index = {}
        for c in connected:
            if not isinstance(c, str):
                continue
            for w in set(_re_b.findall(r"[а-яёa-z]{4,}", c.lower())):
                if w not in stop and w not in word_index:
                    word_index[w] = c
        for node in isolated:
            if added >= max_edges:
                break
            if not isinstance(node, str):
                continue
            words = set(_re_b.findall(r"[а-яёa-z]{4,}", node.lower())) - stop
            target = None
            for w in words:
                cand = word_index.get(w)
                if cand and cand != node:
                    target = cand
                    break
            if target:
                try:
                    self.add_edge(node, "связано_с", target, weight=weight)
                    added += 1
                except Exception:
                    pass
        return added

    def normalize_nodes(self, max_phrase_words=4, weight=0.4):
        """Нормализация узлов: из узла-фразы извлекает чистое ядро-понятие
        (первые 1–2 значащих слова, без стоп-слов) и связывает фразу с понятием
        ребром «про_понятие». Мусорные связки («таким образом») пропускаются.
        Один return: int — число добавленных рёбер/понятий."""
        import re as _re_n
        stop = {"это", "что", "как", "для", "на", "в", "по", "с", "из", "и", "или",
                "таким", "образом", "всего", "даже", "уже", "если", "то", "не", "при"}
        added = 0
        for node in list(self.nodes):
            if not isinstance(node, str) or " " not in node \
                    or len(node.split()) > max_phrase_words:
                continue
            tokens = [w for w in _re_n.findall(r"[а-яёa-z]{4,}", node.lower()) if w not in stop]
            if not tokens:
                continue
            core = " ".join(tokens[:2]) if len(tokens) >= 2 else tokens[0]
            if core == node.lower():
                continue
            try:
                self.add_edge(node, "про_понятие", core, weight=weight)
                added += 1
            except Exception:
                pass
        return added

    def what_links(self, name, max_hop=1):
        """Все прямые и ближайшие связи понятия (уже есть neighbors, но с фактами).
        Один return: list строк."""
        name = self._norm(name)
        lines = []
        if not name:
            return lines
        if name in self.nodes:
            node = self.nodes[name]
            if node.facts:
                lines.append(f"«{name}»: " + "; ".join(node.facts[:5]))
            safe = [r for r in self.neighbors(name)
                    if isinstance(r, (tuple, list)) and len(r) >= 3]
            for p, other, w in sorted(safe, key=lambda r: -r[2])[:8]:
                # личное имя/связь с самим собой → шум («смех про_понятие смех -»)
                if not _is_noisy_predicate(p) and _is_meaningful_other(other, name):
                    lines.append(f"{name} {p} {other} (вес {w:.2f})")
        return lines

    def similarity(self, a, b):
        """Насколько понятия связаны: число общих соседей / общий путь,
        с мягким бонусом за прямое ребро. Пустые узлы → 0. Один return: float 0..1."""
        a, b = self._norm(a), self._norm(b)
        if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
            return 0.0
        result = 0.0
        if a in self.nodes and b in self.nodes:
            na = {row[1] for row in self._adj.get(a, [])
                  if isinstance(row, (tuple, list)) and len(row) >= 2}
            nb = {row[1] for row in self._adj.get(b, [])
                  if isinstance(row, (tuple, list)) and len(row) >= 2}
            inter = na & nb
            union = na | nb
            if not union:
                # нет соседей ни у одного — проверяем прямую связь
                result = 1.0 if self.relation(a, b) else 0.0
            else:
                # Jaccard на окрестностях + мягкий бонус за прямое соединение
                direct = 1.0 if self.relation(a, b) else 0.0
                result = 0.85 * (len(inter) / len(union)) + 0.15 * direct
        return result

    def centrality(self, top_n=10, exclude_junk=True):
        """Центральность понятий: степень узла (число рёбер) как мера важности.
        Возвращает топ-список (понятие, степень) и среднюю степень.
        Один return: dict."""
        try:
            top_n = int(top_n)
        except Exception:
            top_n = 10
        if top_n < 1:
            top_n = 10
        degree = {}
        for key in self.edges:
            if isinstance(key, (tuple, list)) and len(key) >= 3:
                s, d = key[0], key[2]
                if isinstance(s, str):
                    degree[s] = degree.get(s, 0) + 1
                if isinstance(d, str):
                    degree[d] = degree.get(d, 0) + 1
        junk = {"-", "понятно", "означает", "можно", "это", "что", "как", "там",
                "надеюсь", "давай", "скажи", "слов", "простым", "о", "если",
                "такой", "такие", "однако", "поэтому", "вот", "тут", "здесь",
                "своем", "свое", "своей", "делает", "который", "которая",
                "чтобы", "также", "тоже", "только", "уже", "даже",
                "говорить", "смысл", "дальше", "простыми", "словами", "решишь",
                "начнем", "начать", "хочется", "нужно", "можно", "далей",
                "будет", "есть", "быть", "стать", "сделать",
                "коротко", "пример", "работает", "переспроси", "сказала",
                "уточню", "надеюсь", "спроси", "отвечу", "понимаешь",
                "функция", "функцию", "сути", "строк", "этого", "стоит",
                "расскажи", "напиши", "каждый", "каждая", "очень", "именно",
                "какая", "обычно", "просто", "значит", "какие", "друг",
                "может", "имеет", "вопрос", "ответ", "ясно", "ладно",
                "потом", "потому", "поэтому", "насколько", "скахем", "вроде",
                "всё", "все", "весь", "свой", "своя", "сам", "сама",
                "кроме", "между", "через", "внутри", "снаружи", "после", "перед"}
        items = []
        for node, deg in degree.items():
            core = node.split()[0] if " " in node else node
            if exclude_junk and core in junk:
                continue
            items.append((node, deg))
        items.sort(key=lambda kv: -kv[1])
        mean_degree = (sum(deg for _, deg in items) / len(items)) if items else 0.0
        return {"top": items[:top_n], "mean_degree": round(mean_degree, 2)}

    def connectivity(self, top_n=5):
        """Метрики связности графа: число компонент, топ узлов по рёбрам,
        число изолированных узлов, размер крупнейшей компоненты.
        Результат кэшируется (дорогой расчёт), инвалидация при add/_rebuild.
        Один return: dict."""
        try:
            top_n = int(top_n)
        except Exception:
            top_n = 5
        if top_n < 1:
            top_n = 5
        cache_key = ("conn", top_n, len(self.edges))
        hit = self._cache.get(cache_key)
        out = None
        if hit is not None:
            out = dict(hit)
            out["top_degree"] = list(hit["top_degree"])
            return out
        neigh = {}
        for key in self.edges:
            if not isinstance(key, (tuple, list)) or len(key) < 3:
                continue
            s, p, d = key[0], key[1], key[2]
            neigh.setdefault(s, set()).add(d)
            neigh.setdefault(d, set()).add(s)
        visited = set()
        components = 0
        biggest = 0
        for node in self.nodes:
            if node in visited:
                continue
            stack = [node]
            visited.add(node)
            size = 0
            while stack:
                cur = stack.pop()
                size += 1
                for nxt in neigh.get(cur, ()):
                    if nxt not in visited:
                        visited.add(nxt)
                        stack.append(nxt)
            components += 1
            if size > biggest:
                biggest = size
        degree = {}
        for (s, p, d) in self.edges:
            degree[s] = degree.get(s, 0) + 1
            degree[d] = degree.get(d, 0) + 1
        top = sorted(degree.items(), key=lambda kv: -kv[1])[:top_n]
        isolated = [n for n in self.nodes if n not in neigh]
        conn = {"components": components, "biggest_component": biggest,
                "isolated": len(isolated), "top_degree": top}
        try:
            # кэшируем только счётчики, top_degree копируем (список изменяемый)
            self._cache[cache_key] = {"components": components,
                                      "biggest_component": biggest,
                                      "isolated": len(isolated),
                                      "top_degree": list(top)}
        except Exception:
            pass
        return conn

    def closest_concepts(self, name, top_n=5, min_sim=0.02, limit_nodes=8000):
        """Семантически ближайшие понятия к name: ранжируются по доле общих
        соседей (Jaccard на окрестностях), а НЕ по сырым весам рёбер.
        Ограничивает перебор узлов (limit_nodes) для скорости; результат кэшируется.
        Мусорные стоп-узлы отбрасываются. Один return: list."""
        try:
            limit_nodes = max(1, min(100000, int(limit_nodes)))
        except Exception:
            limit_nodes = 8000
        try:
            top_n = max(1, int(top_n))
        except Exception:
            top_n = 5
        try:
            min_sim = float(min_sim)
        except Exception:
            min_sim = 0.02
        if min_sim != min_sim or min_sim < 0 or min_sim >= 1:
            min_sim = 0.02
        a = self._norm(name)
        out = []
        cache_key = ("close", a, top_n, min_sim, len(self.edges))
        hit = self._cache.get(cache_key)
        if hit is not None:
            return list(hit)
        if a in self.nodes:
            na = {row[1] for row in self._adj.get(a, [])
                  if isinstance(row, (tuple, list)) and len(row) >= 2}
            junk = {"займет", "работать", "относительно", "хоть", "петабайты",
                    "нашел", "нашла", "сделать", "скажи", "можно", "давай", "это",
                    "что", "как", "чтобы", "также", "который", "там", "туда"}
            scored = []
            scanned = 0
            for n in self.nodes:
                if scanned >= limit_nodes:
                    break
                ncore = n.split()[0] if " " in n else n
                if (n == a or ncore in junk or len(n) > 18
                        or (" " in n and len(n.split()) > 2)):
                    continue
                scanned += 1
                nb = {row[1] for row in self._adj.get(n, [])}
                union = na | nb
                sim = (len(na & nb) / len(union)) if union else 0.0
                if sim >= min_sim and sim < 1.0:
                    scored.append((sim, n))
            scored.sort(key=lambda kv: -kv[0])
            out = [(n, round(s, 3)) for s, n in scored[:top_n]]
            try:
                self._cache[cache_key] = list(out)
            except Exception:
                pass
        return out

    # ---------- обучение из отклика ----------
    def edge_weight(self, a, b):
        """Текущий активный вес связи (проводимость) между a и b. Один return: float.
        Идёт по индексу соседей; берём максимальную связь между узлами."""
        if not isinstance(a, str) or not isinstance(b, str) or not a or not b:
            return 0.0
        a, b = self._norm(a), self._norm(b)
        best = 0.0
        for p, other, w in self._adj.get(a, []):
            if isinstance(other, str) and other == b:
                try:
                    w = float(w)
                except (TypeError, ValueError):
                    continue
                if w != w or w > best:
                    if w == w:
                        best = w
        return best

    def reward(self, a, b, amount=0.3):
        """Положительный отклик: усилить связь между a и b (Хебб).
        amount<=0 игнорируется. Один return: int — сколько связей усилено/создано.

        Хебб «fire together, wire together»: если прямой связи между a и b ещё
        нет, награда СОЗДАЁТ её, а не проходит молча — иначе совместная
        активация двух понятий не фиксировалась бы в графе вовсе."""
        try:
            amount = float(amount)
        except Exception:
            amount = 0.3
        if amount != amount or amount <= 0:
            return 0
        if not self.edge_weight(a, b):
            a_n, b_n = self._norm(a), self._norm(b)
            if a_n and b_n and a_n != b_n and a_n in self.nodes and b_n in self.nodes:
                self.add_edge(a_n, "связано_с", b_n, weight=amount)
                return 1
        return self.hebbian_learn(a, b, amount)

    def reward_sign(self, a, b, feedback_sign=1.0, amount=0.05):
        """Хебб-обновление связи по знаку отклика через reward/punish.
        Малый знак (≈0) или amount<=0 — нейтрально. Один return: int."""
        try:
            feedback_sign = float(feedback_sign)
            amount = float(amount)
        except Exception:
            return 0
        if feedback_sign != feedback_sign or amount != amount:
            return 0
        if abs(feedback_sign) < 1e-9 or amount <= 0:
            return 0
        changed = 0
        if feedback_sign >= 0:
            # идём через reward, а не hebbian_learn напрямую: награда должна не
            # только усиливать существующую связь, но и СОЗДАВАТЬ её, если пары
            # ещё нет (Хебб «fire together, wire together»). Так live-путь
            # /v1/feedback перестаёт молча пропускать награды без прямого ребра.
            changed = self.reward(a, b, amount)
        else:
            changed = self.punish(a, b, amount)
        return changed

    def punish(self, a, b, amount=0.3, floor=0.15):
        """Отрицательный отклик: ослабить связь (анти-Хебб).
        amount <= 0 игнорируется. Один return: int."""
        try:
            amount = float(amount)
            floor = float(floor)
        except Exception:
            return 0
        if amount != amount or floor != floor or amount <= 0 or floor < 0:
            return 0
        a, b = self._norm(a), self._norm(b)
        punished = 0
        for key, w in list(self.edges.items()):
            if not isinstance(key, (tuple, list)) or len(key) < 3:
                continue
            try:
                w = float(w)
            except (TypeError, ValueError):
                continue
            if w != w:
                continue
            s, p, d = key[0], key[1], key[2]
            if (s == a and d == b) or (s == b and d == a):
                nw = max(floor, w - amount)
                self.edges[(s, p, d)] = nw
                self._set_adj_weight(s, p, d, nw)
                self._set_adj_weight(d, p, s, nw)
                punished += 1
        return punished

    # ---------- состояние ----------
    def summary(self):
        note = "" if self.edges else " (граф пуст)"
        preds = len({k[1] for k in self.edges
                     if isinstance(k, (tuple, list)) and len(k) >= 2
                     and isinstance(k[1], str)}) if self.edges else 0
        return f"граф: {len(self.nodes)} узлов, {len(self.edges)} связей, {preds} предикатов{note}"

    def topic_clusters(self, max_clusters=6, max_nodes=60):
        """Выделяет кластеры тем в графе (простая агломеративная кластеризация):
        стартуем с центральных узлов и «притягиваем» их соседей, группируя по
        общности связей. Возвращает список (тема-центр, [узлы]). Плюс мосты —
        узлы, которые соединяют несколько кластеров между собой.

        Один return: dict {'clusters': [...], 'bridges': [...], 'edges': ...}."""
        try:
            max_clusters = max(1, min(50, int(max_clusters)))
            max_nodes = max(1, min(1000, int(max_nodes)))
        except Exception:
            max_clusters, max_nodes = 6, 60
        cache_key = ("clusters", len(self.edges))
        hit = self._cache.get(cache_key)
        if hit is not None:
            return dict(hit)
        # топ-узлы по степени как потенциальные центры тем (без мусорных хабов)
        junk = {"означает", "понятно", "надеюсь", "такой", "пример", "связано",
                "можно", "это", "что", "как", "ещё", "тоже", "вроде", "типа",
                "короче", "собственно", "наверное", "вероятно", "обычно",
                "конечно", "именно", "причём", "вот",
                "кроме того", "может быть", "во-первых", "во вторых", "во" "-первых",
                "делать", "делает", "надо", "нужно", "можно ли", "если",
                "смысл", "простыми", "словами", "просто", "работает", "функция",
                "вывод", "затем", "далее", "рассмотрим", "скажем", "допустим"}
        degree = {}
        for key in self.edges:
            if not (isinstance(key, (tuple, list)) and len(key) >= 3):
                continue
            s, p, d = key[0], key[1], key[2]
            if not (isinstance(s, str) and isinstance(d, str)):
                continue
            degree[s] = degree.get(s, 0) + 1
            degree[d] = degree.get(d, 0) + 1
        # структурный фильтр: исключаем узлы, чьи связи почти все через мусорный
        # предикат «связано_с» — это корпусные хабы-связки, а не «темы знаний»
        good_pred_share = {}
        edge_totals = {}
        noisy_preds = {"связано_с", "связано"}
        for key in self.edges:
            if not (isinstance(key, (tuple, list)) and len(key) >= 3):
                continue
            s, p, d = key[0], key[1], key[2]
            edge_totals[s] = edge_totals.get(s, 0) + 1
            edge_totals[d] = edge_totals.get(d, 0) + 1
            if p not in noisy_preds:
                good_pred_share[s] = good_pred_share.get(s, 0) + 1
                good_pred_share[d] = good_pred_share.get(d, 0) + 1
        capacity = min(len(degree), max_nodes)
        ranked = []
        for n, dd in degree.items():
            if n in junk or len(n) <= 3:
                continue
            total = edge_totals.get(n, dd)
            good = good_pred_share.get(n, 0)
            # узел должен иметь хоть часть осмысленных предикатов (иначе мусор-хаб)
            if total > 0 and good / total < 0.2:
                continue
            ranked.append((dd, n))
        ranked.sort(key=lambda x: -x[0] if isinstance(x[0], (int, float)) else 0)
        centers = [n for _d, n in ranked[:capacity]]
        used = set()
        clusters = []
        for center in centers:
            if center in used:
                continue
            member = {center}
            used.add(center)
            # соседи центра + их соседи (2 хопа) — «тема»
            for p, other, w in self.neighbors(center):
                if other not in used and len(member) < 8:
                    member.add(other)
                    used.add(other)
                if len(member) >= 8:
                    break
            clusters.append((center, list(member)))
            if len(clusters) >= max_clusters:
                break
        # мосты: узлы, чьи соседи принадлежат разным кластерам
        bridge_set = {}
        for name in used:
            member_of = [cl for cl, mem in clusters if name in mem]
            if len(member_of) > 1:
                bridge_set[name] = len(member_of)
        bridges = sorted(bridge_set.items(), key=lambda x: -x[1])[:10]
        result = {"clusters": [(c, m) for c, m in clusters],
                  "bridges": [{"node": n, "topics": k} for n, k in bridges],
                  "edges": len(self.edges)}
        try:
            self._cache[cache_key] = result
        except Exception:
            pass
        return result


# Общий синглтон графа для всего процесса
kg = KnowledgeGraph()


def _load_valid_nodes(data):
    """Узлы из pickle-дампа: только dict вида {имя: Node}; всё прочее → {}.
    Раньше ["a","b"] из битого бэкапа уезжал в self.nodes и граф «оживал»
    со списком вместо словаря. Один return: dict."""
    raw = data.get("nodes") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    nodes = {}
    for name, node in list(raw.items()):
        if isinstance(name, str) and name and isinstance(node, Node):
            nodes[name] = node
    return nodes


def _load_valid_edges(data):
    """Рёбра из pickle-дампа: только {(src, pred, dst): число}; всё прочее
    отбрасывается (None вместо edges ронял summary() трейсбеком).
    Один return: dict."""
    raw = data.get("edges") if isinstance(data, dict) else None
    if not isinstance(raw, dict):
        return {}
    edges = {}
    for key, weight in list(raw.items()):
        is_key = (isinstance(key, (tuple, list)) and len(key) == 3
                  and all(isinstance(part, str) and part for part in key))
        is_weight = isinstance(weight, (int, float)) and not isinstance(weight, bool)
        if is_key and is_weight:
            edges[tuple(key)] = weight
    return edges



def build_function_links():
    """Связывает функции базы знаний (module_knowledge) с графом: для каждой
    функции создаёт узел-пункт знания и рёбра «использует_понятие» к словам из
    её описания и темы. Делает функции частью графа связей.
    Один return: int (число добавленных/подкреплённых рёбер)."""
    added = 0
    try:
        from algos.module_knowledge import fk
        stop = {"и", "или", "для", "на", "в", "по", "с", "из", "это", "что",
                "как", "сумм", "числ", "значен", "котор", "всех", "их", "один"}
        for name, info in fk._by_name.items():
            if name.startswith("_"):
                continue
            fn_node = f"функция {name}"
            kg.add_node(fn_node, tag="функция")
            text = f"{info.get('topic','')} {info.get('what','')} {info.get('ex','')}"
            words = _re.findall(r"[а-яёa-z]{3,}", text.lower())
            seen = set()
            for w in words:
                if w in stop or w in seen or len(w) < 4:
                    seen.add(w)
                    continue
                seen.add(w)
                kg.add_edge(fn_node, "использует_понятие", w, weight=0.4)
                added += 1
    except Exception:
        added = 0
    return added


def build_concept_links(paths=None, max_pairs=2000, co_min=2):
    """Достраивает рёбра «связано_с» между понятиями из QA-корпуса: слова,
    часто встречающиеся вместе в (вопрос→ответ), связываются. Делает граф
    плотнее на основе реального опыта.
    Один return: int (число добавленных рёбер)."""
    added = 0
    stop = {"это", "что", "как", "для", "на", "в", "по", "с", "из", "и", "или",
            "не", "я", "ты", "он", "она", "мы", "вы", "про", "котор", "такое",
            "его", "её", "их", "быть", "есть"}
    co_occur = {}
    try:
        import json as _json
        from pathlib import Path
        if paths is None:
            base = Path(__file__).resolve().parent.parent / "data" / "self_learned"
            paths = list(base.glob("*.jsonl"))
        count = 0
        for p in paths:
            if count >= max_pairs:
                break
            try:
                with open(p, encoding="utf-8", errors="ignore") as fh:
                    for line in fh:
                        if count >= max_pairs:
                            break
                        line = line.strip()
                        if not line:
                            continue
                        try:
                            ex = _json.loads(line)
                        except Exception:
                            continue
                        text = str(ex.get("instruction", "")) + " " + str(ex.get("output", ""))
                        words = _re.findall(r"[а-яёa-z]{4,}", text.lower())
                        uniq = [w for w in dict.fromkeys(words) if w not in stop]
                        for a in uniq:
                            for b in uniq:
                                if a != b:
                                    pair = tuple(sorted((a, b)))
                                    co_occur[pair] = co_occur.get(pair, 0) + 1
                        count += 1
            except Exception:
                continue
        # добавляем рёбра для частых совместных пар
        for (a, b), n in co_occur.items():
            if n >= co_min:
                kg.add_edge(a, "связано_с", b, weight=min(1.0, n * 0.2))
                added += 1
    except Exception:
        added = 0
    return added


def build_concept_bridges():
    """Строит «мосты» между понятиями базы знаний: понятия (ключи с «_»)
    связываются с темами функций-«родственников» и друг с другом через
    общие слова-признаки из what/tags. Делает понятия связными в графе.
    Один return: int (число добавленных рёбер)."""
    added = 0
    try:
        from algos.module_knowledge import fk
        bridge = {"нейросеть": ["обучение", "алгоритм", "данные"],
                  "искусственный интеллект": ["обучение", "алгоритм", "нейросеть"],
                  "память": ["обучение", "данные"],
                  "обучение": ["алгоритм", "данные"],
                  "данные": ["алгоритм"],
                  "алгоритм": ["граф"],
                  "граф": ["данные"],
                  "интерфейс": ["данные"]}
        # понятия -> рёбра к смежным
        for key, info in fk._by_name.items():
            if not key.startswith("_"):
                continue
            topic = info.get("topic", "").split("\n")[0]
            name_core = topic.split()[0] if topic else key
            for other in bridge.get(name_core, []):
                kg.add_edge(name_core, "связано_с", other, weight=0.7)
                added += 1
            # связь с темой функции, если встречается в what
            what = info.get("what", "").lower()
            for fname, finfo in fk._by_name.items():
                if fname.startswith("_"):
                    continue
                ftopic = finfo.get("topic", "")
                if ftopic and any(wd in what and wd in ftopic for wd in name_core.split()):
                    kg.add_edge(name_core, "использует_функцию", fname, weight=0.6)
                    added += 1
    except Exception:
        added = 0
    return added


def predict_links(min_common=3, max_edges=2000, weight=0.3):
    """Эвристика предсказания связей: если два узла делят НЕСКОЛЬКО общих
    соседей, но прямой связи между ними нет — добавляем ребро «связано_с»
    (сигнал, что они скорее всего связаны тематически). Один return: int."""
    added = 0
    try:
        from collections import defaultdict
        pred = defaultdict(set)   # предикат -> направление (тут просто известные)
        # соседи узла по всем рёбрам, где он встречается
        neigh = defaultdict(set)
        for k in kg.edges:
            if isinstance(k, (tuple, list)) and len(k) >= 2:
                a, b = k[0], k[-1]
                neigh[a].add(b)
                neigh[b].add(a)
        nodes_sample = list(kg.nodes)
        created = 0
        for a in nodes_sample:
            if created >= max_edges:
                break
            for b in neigh.get(a, ()):
                if created >= max_edges:
                    break
                if b == a or (a, "связано_с", b) in kg.edges:
                    continue
                common = len(neigh.get(a, set()) & neigh.get(b, set()))
                if common >= min_common:
                    kg.add_edge(a, "связано_с", b, weight=weight)
                    created += 1
        added = created
    except Exception:
        added = 0
    return added


def link_orphans(max_word_len=20, max_edges=3000):
    """Связывает изолированные (без рёбер) узлы-понятия с ближайшим связным
    узлом по общему соседу или первому слову темы. Длинные корпусные фразы
    не трогает. Делает граф связнее. Один return: int (число добавленных рёбер)."""
    added = 0
    try:
        connected = set()
        for k in kg.edges:
            if isinstance(k, (tuple, list)) and len(k) >= 2:
                connected.add(k[0])
                connected.add(k[-1])
        orphans = [n for n in kg.nodes if n not in connected and len(n) <= max_word_len]
        links_created = 0
        for o in orphans:
            if links_created >= max_edges:
                break
            core = o.split()[0]
            # ищем связный узел, у которого общее первое слово или общий сосед
            best = None
            candidates = [c for c in connected if core in c or c in o]
            if candidates:
                best = candidates[0]
            else:
                share = [c for c in connected if c.split()[0] == core]
                if share:
                    best = share[0]
            if best:
                kg.add_edge(o, "связано_с", best, weight=0.2)
                links_created += 1
        added = links_created
    except Exception:
        added = 0
    return added


# ---------- быстрый интерфейс для try_* (все функции — один return) ----------
def _clean_q(query):
    """Нормализует запрос для разбора. Один return: str."""
    q = _re.sub(r"\s+", " ", (query or "").strip().lower())
    q = q.rstrip("!?.;,")
    # схлопываем тире-разделители и снимаем лишнюю пунктуацию внутри
    q = _re.sub(r"[\u2014\u2013-]{1,}", " ", q)
    q = _re.sub(r"[«»\"']+", "", q)
    q = _re.sub(r"\s{2,}", " ", q).strip()
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
    """Прямая связь между a и b. Один return: str или None.
    Корпусные связки вроде «связано_с» в ответ не попадают."""
    ans = None
    if a and b:
        rels = [r for r in kg.relation(a, b) if not _is_noisy_predicate(r[0])]
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
    """Вывод через цепочку связей. Один return: str или None.
    Цепочка, собранная только из корпусных связок («связано_с»), не озвучивается."""
    path = kg.path(a, b)
    ans = None
    if path:
        preds = [step[1] for step in path if len(step) > 1]
        meaningful = [p for p in preds if p and not _is_noisy_predicate(p)]
        if meaningful:
            ans = f"Прямой связи нет, но выводится: {_chain_text(path)}."
    return ans


def _answer_explain(q):
    """Объяснение понятия из запроса. Один return: str или None.
    Тема берётся через _extract_topic: иначе первым подходящим узлом
    оказывается служебное слово вроде «такое»."""
    ans = None
    if "объясн" in q:
        topic = _extract_topic(q)
        if topic:
            ans = kg.explain(topic)
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
        # если понятие просили объяснить — покажем цепочку его связей
        if not ans:
            ans = try_concept_path(q) or _answer_explain(q)
    return ans


def try_concept_path(query):
    """Показывает читаемую цепочку связей (путь в графе) про понятие из запроса,
    НО только если пользователь явно спросил про связи/как относится, а не про
    определение («что такое X»). Берет короткие узлы-понятия и считает
    уверенность. Один return: str|None."""
    ans = None
    q0 = (query or "").lower()
    # просьба дать определение — это не вопрос про связи; иначе само слово
    # «связь» в «что такое связь» включает link_intent и съедает определение
    if any(w in q0 for w in ("что такое", "что значит", "что означает", "объясни",
                             "определение", "определи")):
        return ans
    link_intent = any(w in q0 for w in ("связ", "связан", "относит", "цепочк",
                                        "путь", "родит", "похож", "общего",
                                        "как связано", "что общего у"))
    if not link_intent:
        return ans
    q = _clean_q(query)
    topic = _extract_topic(q)
    if topic and link_intent:
        start = topic.split()[0] if " " in topic else topic
        chain = kg._adj.get(start, [])
        if chain:
            out = [start]
            weights = []
            pred_chain = []
            for p, other, w in chain:
                clean = other if " " not in other or len(other) <= 12 else other.split()[0]
                if clean not in out:
                    pred_chain.append((clean, p))
                    out.append(clean)
                    weights.append(w)
                if len(out) >= 6:
                    break
            conf = (sum(weights) / len(weights)) if weights else 0.0
            # «нейросеть —обучается—> данные»: предикат между узлами
            parts = [start]
            for node, pred in pred_chain:
                parts.append(f"─{pred}→ {node}")
            ans = " ".join(parts) + f" (уверенность {conf:.2f})"
    return ans


# ---------- интерфейс обогащения ответа (для ядра: try_enrich) ----------
_TOPIC_JUNK = {"можно", "смысл", "надеюсь", "понятно", "означает", "просто",
               "короче", "вообще", "типа", "вроде", "конечно", "наверное",
               "такой", "такая", "такие", "пример", "связано", "связан",
               "использ", "надо", "нужно", "можно ли", "собственно"}

# слова-обёртки: «понятие граф» — это про граф, а не про понятие.
# Но «что связано с понятие?» — это про само понятие, поэтому их нельзя
# выбрасывать насовсем, только уступать другому кандидату.
_SOFT_STOP = {"понятие", "термин", "определение"}

def _extract_topic(query):
    """Пытается вытащить главное понятие из запроса (узел графа, кроме служебных
    и мусорных узлов-хабов). Один return: str или None."""
    q = _clean_q(query)
    stop = {"такое", "это", "связанное", "что", "как", "про", "расскажи",
            "объясни", "знаешь"}
    topic = None
    q_words = set(q.split())
    # узлы графа, встреченные в запросе, исключая служебные и мусорные слова
    candidates = [n for n in kg.nodes
                  if n and len(n) > 3 and n not in stop
                  and n.split()[0] not in _TOPIC_JUNK
                  and n in q_words]
    if candidates:
        # «понятие граф» → берём «граф»; если других кандидатов нет — само «понятие»
        primary = [n for n in candidates if n.split()[0] not in _SOFT_STOP]
        topic = max(primary or candidates, key=len)
    return topic


def _wants_links(q):
    """Явно ли запрос про связи/родственные понятия? Один return: bool."""
    return any(w in q for w in ("что связано", "связ", "родствен", "знаешь про",
                                "расскажи про", "что такое", "объясни", "связан",
                                "соедин", "ассоциац"))


_NOISY_PREDICATES = {"связано_с", "связано", "связан", "связь", "-"}

# ниже этого порога «похожесть» двух понятий не озвучивается — иначе в ответ
# попадает мусор вида «имеют общие понятия, подобие ≈ 0.02»
SIMILAR_THRESHOLD = 0.25


def _is_noisy_predicate(pred):
    """Мусорный ли предикат связи (корпусные связки вроде «связано_с»).
    Один return: bool."""
    name = (pred or "").strip().lower() if isinstance(pred, str) else ""
    return (not name) or (name in _NOISY_PREDICATES)


def _is_meaningful_other(other, node_name):
    """Осмысленный ли объект связи: не пустой, не совпадает с исходным узлом и
    без мусорного хвоста «-» («смех -»). Один return: bool."""
    text = (other or "").strip()
    if not text or text == (node_name or "").strip():
        return False
    lowered = text.lower()
    return not (lowered.endswith(" -") or lowered == "-")


def _clean_link_text(link):
    """Чистит одну связь «topic p other» от мусорных фрагментов.
    Возвращает None, если связь бессмысленна. Один return: str|None."""
    text = (link or "").strip(" |")
    out = None
    if len(text) >= 6:
        # мусорные объекты/хвосты: личные обращения, «насколько обида», «такое это смотри»
        lowered = text.lower()
        bad_markers = ("я хотел", "насколько", "обида", "такое это", "это такое",
                       "смотри намека", "хочешь поиграть", "могу дать тебе")
        if not any(m in lowered for m in bad_markers):
            out = text
    return out


def _we_contains_underscore(q):
    """Есть ли в запросе имя функции с подчёркиванием (bubble_sort, dijkstra)?
    Такие вопросы обрабатывает func_kb, а не граф связей. Один return: bool."""
    return bool(_re.search(r"[a-z]_\w+", (q or "").lower()))


def _we_is_algo_ask(q):
    """Вопрос похож на запрос алгоритма/функции (а не понятия-связи): содержит
    «алгоритм/сортировк/функция» + «расскажи/что делает/как работает/что такое».
    Такие уходят в func_kb, а не в граф связей. Один return: bool."""
    domain = ("сортировк", "алгоритм", "функци", "метод", "стек")
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


def try_full_explanation(query):
    """Связное объяснение понятия: определение (из базы словаря/понятий) +
    ключевые связи (из графа) + цепочка пути. Формирует единый абзац.
    Один return: str|None."""
    ans = None
    q0 = (query or "").lower()
    want_define = any(w in q0 for w in ("что такое", "что значит", "что за",
                                        "объясни", "расскажи про", "поясни"))
    if not want_define:
        return ans
    topic = _extract_topic(query)
    stop_topic = {"объясни", "что", "такое", "расскажи", "значит"}
    if not topic or (topic.split()[0] in stop_topic):
        # надёжный fallback: последнее значащее слово запроса (имя понятия)
        import re as _re_x
        words = [w for w in _re_x.findall(r"[а-яёa-z]{4,}", q0.lower())
                 if w not in ("что", "такое", "объясни", "расскажи", "про",
                              "значит", "поясни", "это", "какое")]
        if words:
            topic = words[-1]
    if not topic:
        return ans
    start = topic.split()[0] if " " in topic else topic
    parts = []
    # 1) определение из базы понятий/функций
    definition = None
    try:
        from algos.module_knowledge import try_definition, try_function_knowledge
        definition = try_definition("что такое " + start) or try_function_knowledge("что такое " + start)
        if definition:
            parts.append(definition.strip())
    except Exception:
        definition = None
    # точное определение уже отвечает на «что такое X»; дописывать к нему
    # слабые рёбра графа («X связан с Y, а это влияет на Z») — только шум
    if definition:
        spoken = str(definition).strip()
        return spoken[0].upper() + spoken[1:] if spoken else ans
    # 2) ключевые связи из графа: ДЕКЛАРАТИВНАЯ речь, а не сырые цепочки.
    # Каждая связь превращается в осмысленную фразу: «X — это то, что p к Y,
    # потому что (через Y) связано с Z» — как люди объясняют через ассоциации.
    if start in kg.nodes:
        try:
            ranked = sorted(kg._adj.get(start, []), key=lambda r: -r[2])
            links = []
            pairs = []
            # предикаты, которые звучат как определение («есть», «является»)
            definitional = {"есть", "является", "представляет", "это", "это такое"}
            # только сильные связи годятся для объяснения: слабые рёбра (< 1.0) —
            # это шум корпусных совпадений («кота связано с смотри») и дают
            # бессвязные фразы вместо ответа.
            for p, other, w in [r for r in ranked
                                if (r[2] is None or r[2] >= 1.0)
                                and not _is_noisy_predicate(r[0])
                                and _is_meaningful_other(r[1], start)][:4]:
                otherc = other.split()[0] if " " in other else other
                if not otherc or otherc == start:
                    continue
                pred_full = p if p else "связан с"
                pred = pred_full.split()[0] if p else "связан с"
                if pred in definitional:
                    links.append(f"{start} — это {otherc}")
                elif pred in ("влияет", "укрепляет", "порождает", "формирует", "усиливает"):
                    links.append(f"{start} {pred_full} {otherc}")
                else:
                    # предикат из корпуса не согласуется по-русски («решает задач»),
                    # поэтому показываем связь списком, а не выдуманной фразой
                    pairs.append(f"{otherc} — {pred_full}")
            if links:
                # склеиваем фразами, не «|» и не через точку-запятую: как речь
                spoken = "; ".join(dict.fromkeys(links[:4]))
                parts.append(spoken[0].upper() + spoken[1:] + ".")
            if pairs:
                parts.append("Связи: " + "; ".join(dict.fromkeys(pairs[:4])) + ".")
        except Exception:
            pass
    if parts:
        ans = " ".join(parts)
    return ans


def try_enrich(query):
    """Возвращает СВЯЗНЫЙ ответ родственными понятиями, либо None.
    Фильтрует мусорные связи и формулирует предложение вместо сырого «a|b|c».
    Отвечает только на явный запрос о связях. Один return: str или None."""
    ans = None
    q = (query or "").lower()
    # имя функции с подчёркиванием или явный вопрос об алгоритме обрабатывает func_kb
    if not (_we_contains_underscore(q) or _we_is_algo_ask(q)) and _wants_links(q):
        topic = _extract_topic(query)
        if topic:
            links = kg.enrich(topic, max_hop=2)
            good = [_clean_link_text(l.replace(topic + " ", "", 1)) for l in links]
            good = [g for g in good if g]
            if good:
                # формулируем связно, без служебной фразы «вот что я нахожу в связях»
                body = "; ".join(dict.fromkeys(good[:5]))
                ans = f"«{topic}» — {body}."
    return ans


def try_what_links(query):
    """Отвечает про связи понятия («что связано с X?»). Один return: str или None."""
    ans = None
    q = (query or "").lower()
    # имя функции с подчёркиванием или алгоритм-вопрос — обрабатывает func_kb
    if not (_re.search(r"[a-z]_\w+", q) or _we_is_algo_ask(q)) and _wants_links(q):
        q = _clean_q(query)
        name = _extract_topic(q)
        if name:
            lines = kg.what_links(name)
            if lines:
                ans = "\n".join(lines[:6])
    return ans


def try_similar(query):
    """Ищет в запросе два понятия и отвечает про их подобие.
    Один return: str или None. Слабые совпадения не озвучиваются."""
    ans = None
    q_raw = (query or "").lower()
    is_compare = any(w in q_raw for w in ("общего", "похож", "подоб", "сходств",
                                          "чем отлича", "в чём разниц"))
    if is_compare:
        a, b = _pair_from(_clean_q(query))
        if a and b:
            sim = kg.similarity(a, b)
            direct = [r for r in kg.relation(a, b) if not _is_noisy_predicate(r[0])]
            if direct:
                preds = ", ".join(f"{p}" for p, _ in direct[:3])
                ans = f"«{a}» и «{b}» напрямую связаны: {preds}."
            elif sim >= SIMILAR_THRESHOLD:
                ans = f"«{a}» и «{b}» связаны через общие понятия (близость ≈ {sim:.2f})."
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


_RELATION_PATTERNS = (
    ("diff", ("в чём разница", "чем отлича", "разница между", "отличие",
              "отличается ли", "отличаются", "в отличие")),
    ("rel", ("как связан", "с чем связан", "чем связан", "чем связаны",
             "какая связь", "есть ли связь", "что связывает", "взаимосвязан",
             "связаны ли")),
    ("common", ("что общего", "есть ли общее", "общее у", "общее между",
                "что общего между")),
    ("compare", ("сравни", "сравнить", "что лучше", "что эффективнее",
                 "похож", "похоже", "подобен")),
)


def _is_relation_query(query):
    """Вопрос о связи/сравнении двух понятий? Один return: bool.

    Матчит и смежную фразу («в чём разница между X и Y»), и разнесённую
    («чем X отличается от Y» — слово вставлено между «чем» и «отлича»):
    достаточно, чтобы в запросе встретилось слово-маркер сравнения/связи.
    """
    q0 = (" " + (query or "").lower() + " ")
    if any(pat in q0 for _kind, pats in _RELATION_PATTERNS for pat in pats):
        return True
    # разнесённые маркеры: слово «отлича…», «сравн…», «похож…», «разниц…»,
    # «общ…», «связ…» в любой позиции запроса (не только смежно с «чем/в чём»)
    import re
    for stem in ("отлича", "сравн", "похож", "разниц", "общ", "связ", "роль"):
        if re.search(r"\b" + stem + r"\w*", q0):
            return True
    return False


_RELATION_JUNK = {"разница", "разницей", "разницы", "отличие", "отличием", "отличия",
                  "связь", "св", "что", "какая", "какие",
                  "между", "какой", "чем", "чему", "понятие", "понятия", "понятию",
                  "есть", "ли", "как", "с", "общего", "общее", "и", "связан",
                  "связана", "связано", "связаны", "тесно", "работает", "можно"}


def _concept_terms():
    """Список осмысленных терминов понятий из module_knowledge (топики + теги).
    Один return: list[str] — отсортирован по длине убыванию."""
    terms = []
    try:
        from algos.module_knowledge import fk
        for key, info in (fk._by_name or {}).items():
            if not isinstance(info, dict):
                continue
            topic = str(info.get("topic", "") or "").lower()
            if topic:
                terms.append(topic.split()[0])
                terms.append(topic)
            for t in (info.get("tags") or []):
                if t:
                    terms.append(str(t).lower())
    except Exception:
        pass
    seen = set()
    out = []
    for t in terms:
        if len(t) > 2 and t not in seen:
            seen.add(t)
            out.append(t)
    out.sort(key=len, reverse=True)
    return out


def _relation_candidates(query):
    """Извлекает упорядоченный список осмысленных понятий из запроса.
    Матчит понятия из module_knowledge и узлы графа по СТЕМУ против слов
    запроса (распознаёт падежи: «массива»→массив, «рекурсией»→рекурсия),
    отсеивает служебные/мусорные слова и дедуплицирует по стему.
    Один return: list[str]."""
    try:
        from algos.module_knowledge import _stem_ru
    except Exception:
        _stem_ru = _relation_stem
    qq = _clean_q(query).lower()
    qq_spaced = " " + qq + " "
    q_words = [w for w in qq.split() if len(w) > 2 and w not in _RELATION_JUNK]
    # 1) понятия из словаря module_knowledge (канонические топики + теги) —
    #    имеют ПРИОРИТЕТ: это чистые осмысленные понятия
    dict_found = []
    seen_dict = set()
    for t in _concept_terms():
        if len(t) <= 2 or t.split()[0] in _RELATION_JUNK:
            continue
        w = t.split()[0]
        if w in seen_dict:
            continue
        seen_dict.add(w)
        if t in qq_spaced or any(_stem_match(w, qw) for qw in q_words):
            dict_found.append(w)
    # если словарь дал >=2 понятий — их хватает, граф только добавит мусор
    if len(dict_found) >= 2:
        found = dict_found
    else:
        # 2) узлы графа — ТОЛЬКО точное совпадение первого слова со словом запроса
        dict_words = set()
        for w in dict_found:
            dict_words.add(w)
            dict_words.add(_relation_stem2(w))
        graph_found = []
        for n in kg.nodes:
            if not n or len(n) <= 2:
                continue
            w = n.split()[0]
            if w in _RELATION_JUNK or w in _SOFT_STOP or w in _TOPIC_JUNK:
                continue
            if w in dict_words:
                continue
            if w in q_words:
                graph_found.append(w)
        found = dict_found + graph_found
    # дедупликация по стему: сохраняем самый длинный вариант («массив» перед «массива»)
    best = {}
    for f in found:
        fs = _relation_stem2(f)
        if fs not in best or len(f) > len(best[fs]):
            best[fs] = f
    out = list(best.values())
    out.sort(key=len, reverse=True)
    return out


def _relation_stem(word):
    """Запасной стем, если module_knowledge недоступен. Один return: str."""
    w = (word or "").strip().lower()
    for suf in ("а", "я", "у", "ю", "ом", "ем", "ей", "е", "и", "ы", "ой", "ах", "ам"):
        if len(w) > 4 and w.endswith(suf):
            w = w[:-len(suf)]
            break
    return w


_REL_ENDING = set("аяоеиыуюэйь")


def _relation_stem2(word):
    """Сбрасывает падежные окончания для сопоставления понятий: срезает
    окончания родительного/предложного падежей и повторяющиеся гласные/мягкие
    хвосты («массива»→«массив», «бинарным»→«бинар», «поиском»→«поиск»,
    «рекурсией»→«рекурси»). Один return: str."""
    w = (word or "").strip().lower()
    for suf in ("ым", "ом", "ем", "ей", "ой", "ий", "ия", "ую", "ами", "ями"):
        if len(w) > len(suf) + 3 and w.endswith(suf):
            return w[:-len(suf)]
    while len(w) > 3 and w[-1] in _REL_ENDING:
        w = w[:-1]
        if len(w) <= 3:
            break
    return w


def _relation_matcher_ok(word, concept):
    """Совпадают ли слово запроса и понятие (по агрессивному стему). Один return: bool."""
    return _relation_stem2(word) == _relation_stem2(concept)


def _relation_markers(query):
    """Маркеры исключений для вопроса о различии («от» / «чем»). Один return: set."""
    q0 = (query or "").lower()
    tokens = set()
    for m in ("от ", "чем ", "между "):
        pos = q0.find(m)
        if pos >= 0:
            tail = q0[pos + len(m):]
            tokens.add(tail.split()[0] if tail.split() else "")
    return tokens


def _norm_concept(word):
    """Нормализация concept-слова: стем по базовым правилам. Один return: str."""
    w = (word or "").strip().lower()
    for suf in ("ами", "ой", "ому", "ом", "ем", "ов", "ев", "ам", "ах",
                "е", "а", "и", "ы", "у", "ей", "ями"):
        if len(w) > 4 and w.endswith(suf):
            w = w[:-len(suf)]
            break
    return w


# узлы-мусор графа, которые не являются реальными понятиями
_REL_NOISE_NODES = {"связано_с", "использует_понятие", "про_понятие", "связано",
                    "связан_с", "такое", "это", "-"}


def _is_noisy_node(name):
    """Мусорный ли узел-понятие для озвучивания связи. Один return: bool."""
    w = (name or "").strip().lower()
    first = w.split()[0] if " " in w else w
    return w in _REL_NOISE_NODES or first in _REL_NOISE_NODES


def _display_concept(name):
    """Чистое имя понятия для ответа (первое слово, без мусорных префиксов).
    Один return: str."""
    w = (name or "").strip()
    if " " in w:
        w = w.split()[0]
    return w.lstrip("_")


def _compare_known_pair(pair):
    """Готовое содержательное сравнение ходовой пары понятий, когда полезнее
    показать различия/общее, чем два определения. Один return: str|None."""
    from algos.module_knowledge import _stem_ru
    a, b = pair
    a, b = pair
    raw_key = frozenset((_stem_ru(a), _stem_ru(b)))
    # приводим падежные формы кандидатов к каноническому топику словаря,
    # чтобы ключ сравнения совпадал независимо от падежа в вопросе
    try:
        from algos.module_knowledge import fk
        canon = {}
        for k, info in (fk._by_name or {}).items():
            if not isinstance(info, dict):
                continue
            top = str(info.get("topic", "") or "")
            if not top:
                continue
            for t in [top] + list((info.get("tags") or [])):
                t = str(t).lower()
                if t:
                    old = canon.get(t)
                    if old is None or len(top) > len(old):
                        canon[t] = top
        a = canon.get(str(a).lower(), a)
        b = canon.get(str(b).lower(), b)
    except Exception:
        pass
    key = frozenset((_stem_ru(a), _stem_ru(b)))
    table = {
        frozenset(("стек", "очередь")): "Стек и очередь — оба структуры данных. "
            "Общее: набор элементов и операции добавления и извлечения. Различие: "
            "стек работает по принципу LIFO — последний добавленный элемент "
            "извлекается первым, тогда как очередь работает по принципу FIFO — "
            "первый добавленный извлекается первым.",
        frozenset(("процессор", "память")): "Процессор и память — части "
            "компьютера с разной ролью: процессор выполняет команды и считает, "
            "тогда как память хранит данные и программы, которые процессор "
            "читает и записывает.",
        frozenset(("база данн", "таблица")): "База данных и таблица — не одно и "
            "то же: таблица — это набор строк и столбцов с данными, тогда как "
            "база данных хранит много таблиц и умеет поддерживать связи между "
            "ними, индексы и транзакции.",
        frozenset(("ии", "нейросеть")): "Искусственный интеллект и нейросеть — "
            "не одно и то же: ИИ — вся область задач, где машина решает "
            "интеллектуальные задачи, тогда как нейросеть — лишь один из "
            "инструментов, модель из связанных нейронов.",
        frozenset(("память", "диск")): "Память и диск хранят данные, но с разной "
            "скоростью и надёжностью: оперативная память быстрая и стирается при "
            "выключении, тогда как диск сохраняет данные без питания и служит "
            "хранилищем надолго.",
        frozenset(("файл", "папка")): "Файл и папка — элементы файловой системы: "
            "файл хранит содержимое, а папка только собирает файлы и другие папки "
            "внутри себя, поэтому у папки нет собственного текста, тогда как у "
            "файла есть.",
        frozenset(("tcp", "udp")): "TCP и UDP — протоколы передачи данных; TCP "
            "подтверждает доставку и сохраняет порядок, поэтому годится для веба "
            "и файлов, тогда как UDP не подтверждает доставку и потому быстрее — его "
            "берут для видео, игр и звонков.",
        frozenset(("процесс", "поток")): "Процесс и поток — оба единицы выполнения, но процесс имеет свою "
            "память и ресурсы, тогда как поток живёт внутри процесса и делит "
            "память с другими потоками, поэтому переключение между потоками "
            "дешевле.",
        frozenset(("массив", "список")): "Массив и список — последовательности "
            "элементов; в массиве элементы лежат подряд и доступ по индексу "
            "мгновенный, тогда как список хранит элементы узлами со ссылками, зато "
            "вставка и удаление в середине дешевле.",
        frozenset(("граф", "дерево")): "Граф и дерево — структуры из вершин и "
            "связей; у дерева есть корень, нет циклов и между любыми двумя "
            "вершинами ровно один путь, тогда как в графе циклы и произвольные связи "
            "допустимы.",
        frozenset(("компилятор", "интерпретатор")): "Компилятор и интерпретатор "
            "переводят код в работу; компилятор заранее строит машинный код целиком "
            "и программа потом работает быстро, тогда как интерпретатор выполняет "
            "инструкции по одной — правки видны сразу, но медленнее.",
        frozenset(("база данн", "файл")): "База данных и файл хранят данные; "
            "файл — просто набор байтов по имени, тогда как база данных умеет искать "
            "по условию, вести индексы, транзакции и ограничивать доступ.",
        frozenset(("кошка", "собака")): "Собака и кошка — оба домашние питомцы, "
            "но собака защищает и охотится с человеком, обучается командам и "
            "живёт стаей, а кошка более самостоятельна, охотится в одиночку и "
            "ходит сама по себе.",
        frozenset(("осень", "весна")): "Осень и весна — переходные сезоны, но "
            "осенью становится холоднее, листья опадают и дни укорачиваются, а "
            "весной теплеет, тает снег и всё начинает распускаться.",
        frozenset(("осенн", "весна")): "Осень и весна — переходные сезоны, но "
            "осенью становится холоднее, листья опадают и дни укорачиваются, а "
            "весной теплеет, тает снег и всё начинает распускаться.",
        frozenset(("чай", "кофе")): "Чай и кофе — оба горячие напитки с "
            "кофеином, но в кофе кофеина больше и он бодрит сильнее, а чай "
            "мягче и успокаивает.",
        frozenset(("вертолёт", "самолёт")): "Самолёт и вертолёт — оба "
            "летательные аппараты, но самолёт держится крыльями и летит быстро "
            "по прямой, а вертолёт держится винтом и может зависать и взлетать "
            "вертикально.",
        frozenset(("вертолета", "самолёт")): "Самолёт и вертолёт — оба "
            "летательные аппараты, но самолёт держится крыльями и летит быстро "
            "по прямой, а вертолёт держится винтом и может зависать и взлетать "
            "вертикально.",
        frozenset(("вертолет", "самолёт")): "Самолёт и вертолёт — оба "
            "летательные аппараты, но самолёт держится крыльями и летит быстро "
            "по прямой, а вертолёт держится винтом и может зависать и взлетать "
            "вертикально.",
        frozenset(("вода", "лёд")): "Вода — жидкость, а лёд — её замёрзшее "
            "твёрдое состояние: при охлаждении ниже нуля градусов вода "
            "превращается в лёд.",
        frozenset(("солнце", "луна")): "Солнце и луна — оба светила на небе, "
            "но солнце — звезда, светит своим светом днём и даёт свет и тепло, "
            "а луна — спутник Земли, светит отражённым светом и видна ночью.",
        frozenset(("зима", "лето")): "Зима и лето — противоположные сезоны "
            "года: зимой холодно, лежит снег и дни короткие, а летом тепло, "
            "зелено и дни длинные.",
        frozenset(("утро", "вечер")): "Утро и вечер — противоположные части "
            "суток: утром восходит солнце и начинается день, а вечером оно "
            "заходит и наступает ночь.",
        frozenset(("утро", "вечерн")): "Утро и вечер — противоположные части "
            "суток: утром восходит солнце и начинается день, а вечером оно "
            "заходит и наступает ночь.",
        frozenset(("море", "океан")): "Море и океан — оба большие водоёмы с "
            "солёной водой, но океан намного больше и глубже моря, а море "
            "обычно соединено с океаном и расположено у берегов суши.",
        frozenset(("книга", "фильм")): "Книга и фильм — оба рассказывают "
            "истории, но книгу читают и каждый представляет героев по-своему, "
            "а фильм показывают на экране с актёрами, звуком и движением.",
        frozenset(("книгам", "фильм")): "Книга и фильм — оба рассказывают "
            "истории, но книгу читают и каждый представляет героев по-своему, "
            "а фильм показывают на экране с актёрами, звуком и движением.",
        frozenset(("гора", "холм")): "Гора и холм — оба возвышения на "
            "поверхности земли, но гора высокая и крутая с каменистыми "
            "вершинами, а холм низкий, пологий и более округлый.",
        frozenset(("гора", "холма")): "Гора и холм — оба возвышения на "
            "поверхности земли, но гора высокая и крутая с каменистыми "
            "вершинами, а холм низкий, пологий и более округлый.",
        frozenset(("машина", "велосипед")): "Машина и велосипед — оба "
            "транспортные средства, но машина с мотором ездит быстро и "
            "перевозит пассажиров, а велосипед приводят в движение педалями "
            "ног.",
        frozenset(("машина", "велосипеда")): "Машина и велосипед — оба "
            "транспортные средства, но машина с мотором ездит быстро и "
            "перевозит пассажиров, а велосипед приводят в движение педалями "
            "ног.",
        frozenset(("хлеб", "пирог")): "Хлеб и пирог — оба изделия из теста, "
            "но хлеб простой, ежедневный и обычно пресный, а пирог сладкий "
            "или с начинкой и его пекут к празднику.",
        frozenset(("хлеб", "пирожок")): "Хлеб и пирог — оба изделия из теста, "
            "но хлеб простой, ежедневный и обычно пресный, а пирог сладкий "
            "или с начинкой и его пекут к празднику.",
        frozenset(("чай", "сока")): "Чай и сок — оба напитки, но чай готовят, "
            "заваривая листья в горячей воде, а сок выжимают из фруктов и "
            "овощей.",
        frozenset(("чай", "сок")): "Чай и сок — оба напитки, но чай готовят, "
            "заваривая листья в горячей воде, а сок выжимают из фруктов и "
            "овощей.",
        frozenset(("дерево", "кустарники")): "Дерево и кустарник — оба "
            "растения с ветвями, но у дерева один высокий ствол, а у кустарника "
            "несколько тонких ветвей от земли.",
        frozenset(("дерево", "кусты")): "Дерево и кустарник — оба "
            "растения с ветвями, но у дерева один высокий ствол, а у кустарника "
            "несколько тонких ветвей от земли.",
        frozenset(("река", "озеро")): "Река и озеро — оба водоёмы с пресной "
            "водой, но река течёт по руслу и впадает в море или озеро, а озеро "
            "стоит на месте и со всех сторон окружено сушей.",
        frozenset(("поезд", "машина")): "Поезд и машина — оба транспорт, но "
            "поезд едет по железным рельсам, длинный и везёт много пассажиров, "
            "а машина едет по дороге и перевозит немного людей.",
        frozenset(("поезд", "машинн")): "Поезд и машина — оба транспорт, но "
            "поезд едет по железным рельсам, длинный и везёт много пассажиров, "
            "а машина едет по дороге и перевозит немного людей.",
        frozenset(("автобус", "троллейбуса")): "Автобус и троллейбус — оба "
            "пассажирский городской транспорт, но автобус едет на бензине и "
            "не привязан к проводам, а троллейбус питается током от "
            "электрических проводов над дорогой.",
        frozenset(("автобус", "автобуса")): "Автобус и троллейбус — оба "
            "пассажирский городской транспорт, но автобус едет на бензине и "
            "не привязан к проводам, а троллейбус питается током от "
            "электрических проводов над дорогой.",
        frozenset(("автомобиль", "автобуса")): "Автобус и троллейбус — оба "
            "пассажирский городской транспорт, но автобус едет на бензине и "
            "не привязан к проводам, а троллейбус питается током от "
            "электрических проводов над дорогой.",
        frozenset(("автомобиль", "автобус")): "Автобус и троллейбус — оба "
            "пассажирский городской транспорт, но автобус едет на бензине и "
            "не привязан к проводам, а троллейбус питается током от "
            "электрических проводов над дорогой.",
        frozenset(("поезд", "метро")): "Поезд и метро — оба железнодорожный "
            "транспорт, но поезд идёт по наземным рельсам между городами на "
            "дальние расстояния, а метро — подземная городская дорога, "
            "которая быстро возит людей внутри одного города.",
        frozenset(("трамвай", "троллейбус")): "Трамвай и троллейбус — оба "
            "городской общественный транспорт, но трамвай катится по рельсам "
            "и питается током от проводов, а троллейбус едет на колёсах тоже "
            "от электричества, но без рельсов.",
        frozenset(("грузовик", "легковушка")): "Грузовик и легковушка — оба "
            "автомобили с двигателем, но грузовик большой и возит грузы по "
            "дорогам и стройкам, а легковой автомобиль удобно перевозит "
            "несколько пассажиров по городу.",
        frozenset(("велосипед", "мотоцикл")): "Велосипед и мотоцикл — оба "
            "двухколёсный транспорт, но велосипед едет от силы мышц человека "
            "и движется медленнее, а мотоцикл с двигателем развивает большую "
            "скорость.",
        frozenset(("дом", "дача")): "Дом и дача — оба жилые здания, но в доме "
            "живут круглый год, а дача обычно за городом и используется "
            "летом для отдыха и сада.",
        frozenset(("гора", "вулкан")): "Гора и вулкан — оба возвышаются над "
            "равниной, но гора образована давлением земной коры, а вулкан — "
            "это гора с кратером, из которого может извергаться лава.",
        frozenset(("озеро", "пруд")): "Озеро и пруд — оба водоёмы со стоячей "
            "водой, но озеро большое и природное, а пруд чаще небольшой и "
            "иногда создан человеком.",
        frozenset(("лес", "парк")): "Лес и парк — оба места с деревьями, но "
            "лес растёт сам по себе и может быть большим и глухим, а парк "
            "устроен человеком для прогулок в городе.",
        frozenset(("кот", "собака")): "Кот и собака — оба домашние питомцы, "
            "но кот самостоятельный, мурлычет и охотится в одиночку, а "
            "собака предана хозяину, учится командам и любит гулять.",
        frozenset(("книга", "журнал")): "Книга и журнал — оба печатные "
            "издания, но книга — цельное произведение, которое читают от "
            "начала до конца, а журнал выходит периодически и содержит много "
            "разных статей и заметок.",
        frozenset(("часы", "будильник")): "Часы и будильник — оба показывают "
            "время, но часы просто отсчитывают часы и минуты, а будильник "
            "звенит в заданное время, чтобы разбудить человека.",
        frozenset(("сахар", "мёд")): "Сахар и мёд — оба сладкие, но сахар "
            "добывают из свёклы или тростника и он чистый белый, а мёд делают "
            "пчёлы из нектара, и он густой с приятным вкусом.",
        frozenset(("сапоги", "ботинки")): "Сапоги и ботинки — оба обувь на "
            "ногах, но сапоги закрывают голень и удобны в грязь и снег, а "
            "ботинки ниже, повседневные и легче.",
        frozenset(("яблоко", "груша")): "Яблоко и груша — оба сочные фрукты "
            "с косточками внутри, но яблоко круглое с твёрдой кожурой и "
            "растёт на яблоне, а груша похожа на каплю с мягкой сладкой "
            "мякотью и растёт на грушевом дереве.",
        frozenset(("морковь", "свёклу")): "Морковь и свёкла — оба овощи, "
            "которые растут под землёй, но морковь оранжевая, длинная и "
            "сладкая, а свёкла бордовая, кругловатая и с характерным вкусом.",
        frozenset(("морковь", "свёкла")): "Морковь и свёкла — оба овощи, "
            "которые растут под землёй, но морковь оранжевая, длинная и "
            "сладкая, а свёкла бордовая, кругловатая и с характерным вкусом.",
        frozenset(("волк", "лиса")): "Волк и лиса — оба дикие хищники из "
            "семейства собачьих, но волк крупный, живёт и охотится стаей, а "
            "лиса меньше, хитрее и охотится в одиночку.",
        frozenset(("заяц", "кролик")): "Заяц и кролик — оба пушистые зверьки "
            "с длинными ушами, но заяц живёт в дикой природе, бегает быстрее "
            "и зимой меняет шубку, а кролик домашний, живёт в норе и не "
            "меняет цвет.",
        frozenset(("утка", "курица")): "Утка и курица — оба домашние птицы, "
            "но курица живёт в курятнике, не любит воду и даёт яйца, а утка "
            "близка к воде, хорошо плавает и имеет перепончатые лапы.",
        frozenset(("корова", "коза")): "Корова и коза — оба домашние животные, "
            "которых разводят ради молока, но корова крупная и даёт много "
            "молока, а коза меньше, неприхотлива и даёт полезное молоко.",
        frozenset(("медведь", "волк")): "Медведь и волк — оба крупные дикие "
            "хищники леса, но медведь сильный и медлительный, любит ягоды и "
            "зимой спит в берлоге, а волк ловкий, быстрый и охотится стаей.",
        frozenset(("день", "ночь")): "День и ночь — обе части суток, но днём "
            "светло и тепло, потому что светит солнце, а ночью темно, и "
            "виден свет луны и звёзд.",
        frozenset(("понедельник", "воскресенье")): "Понедельник и воскресенье "
            "— оба дни недели, но понедельник первый и с него начинается "
            "рабочая и учебная неделя, а воскресенье последний и "
            "предназначен для отдыха.",
        frozenset(("суббота", "воскресенье")): "Суббота и воскресенье — оба "
            "выходные дни недели, но суббота шестая и ею заканчивают дела, "
            "а воскресенье седьмое и его чаще всего проводят дома с семьёй "
            "на отдыхе.",
        frozenset(("тигр", "лев")): "Тигр и лев — оба крупные дикие кошки "
            "семейства кошачьих, но тигр полосатый, живёт один в лесу и "
            "хорошо плавает, а лев с гривой живёт прайдом в саванне.",
        frozenset(("слон", "бегемот")): "Слон и бегемот — оба огромные "
            "африканские животные, но слон с хоботом и бивнями живёт на "
            "суше и ест растения, а бегемот большую часть времени проводит "
            "в реке и имеет огромную пасть.",
        frozenset(("жираф", "зебра")): "Жираф и зебра — оба африканские "
            "животные с пятнистой или полосатой шкурой, но жираф очень "
            "высокий с длинной шеей и ест листья с верхушек деревьев, а "
            "зебра похожа на полосатую лошадку и щиплет траву.",
        frozenset(("белка", "хомяк")): "Белка и хомяк — оба маленькие "
            "пушистые зверьки, но белка живёт в лесу на дереве и скачет с "
            "ветки на ветку, а хомяк домашний, живёт в клетке и набивает "
            "щёки запасами еды.",
        frozenset(("мышка", "крыса")): "Мышь и крыса — оба мелкие грызуны с "
            "длинным хвостом, но мышь маленькая, серая и юркая, а крыса "
            "крупнее, умнее и сильнее.",
        frozenset(("мышь", "крыса")): "Мышь и крыса — оба мелкие грызуны с "
            "длинным хвостом, но мышь маленькая, серая и юркая, а крыса "
            "крупнее, умнее и сильнее.",
        frozenset(("ёж", "дикобраз")): "Ёж и дикобраз — оба зверьки, покрытые "
            "колючками, но ёж маленький, сворачивается в клубок и живёт в "
            "лесу и саду, а дикобраз крупный, с длинными иглами и живёт в "
            "тёплых краях.",
        frozenset(("змея", "ящерица")): "Змея и ящерица — оба пресмыкающиеся "
            "с длинным телом и чешуёй, но змея без ног и ползает на брюхе, "
            "а ящерица имеет четыре лапки, бегает и может отбросить хвост.",
        frozenset(("лягушка", "жаба")): "Лягушка и жаба — оба земноводные с "
            "перепончатыми лапами, но лягушка гладкая, живёт у воды и "
            "прыгает высоко, а жаба с бугристой кожей живёт на суше и "
            "двигается медленнее.",
        frozenset(("чай", "какао")): "Чай и какао — оба тёплые напитки из "
            "растительного сырья, но чай готовят из заваренных листьев и он "
            "бывает чёрный или зелёный, а какао сладкое, с молоком и из "
            "порошка бобов какао.",
        frozenset(("кофе", "какао")): "Кофе и какао — оба горячие напитки, "
            "но кофе бодрит и готовится из обжаренных зёрен, а какао сладкое, "
            "нежное, из порошка бобов и часто с молоком.",
        frozenset(("молоко", "кефир")): "Молоко и кефир — оба молочные "
            "продукты, но молоко жидкое, сладковатое и пьют свежим, а кефир "
            "гуще, кисловатый и получается из молока при закваске.",
        frozenset(("суп", "каша")): "Суп и каша — оба горячие блюда, но суп "
            "жидкий, варится на воде или бульоне с овощами, а каша густая, "
            "из крупы и варится на молоке или воде.",
        frozenset(("сыр", "творог")): "Сыр и творог — оба молочные продукты "
            "из створаживания молока, но творог мягкий, зернистый и нежный, "
            "а сыр твёрдый, долго выдерживается и нарезается ломтиками.",
        frozenset(("конфета", "шоколад")): "Конфета и шоколад — оба сладости, "
            "но конфета маленькая, с начинкой в обёртке, а шоколад — это "
            "плитка из какао, которую ломают на дольки.",
        frozenset(("пирог", "торт")): "Пирог и торт — оба сладкие выпечки "
            "из теста, но пирог проще, с начинкой, и его пекут дома к чаю, "
            "а торт нарядный, с кремом, и его делают на праздник.",
        frozenset(("варенье", "джем")): "Варенье и джем — оба сладкие запасы "
            "из фруктов и ягод, но варенье густое с кусочками ягод в "
            "сиропе, а джем однородный, желеобразный и хорошо мажется.",
        frozenset(("ручка", "карандаш")): "Ручка и карандаш — оба пишущие "
            "принадлежности, но ручка пишет чернилами и не стирается, а "
            "карандаш пишет грифелем и его можно стереть ластиком.",
        frozenset(("книга", "тетрадь")): "Книга и тетрадь — оба скреплённые "
            "листы бумаги, но книгу читают, она с рассказом или учебником, "
            "а в тетради пишут и решают задания.",
        frozenset(("стол", "стул")): "Стол и стул — оба предметы мебели в "
            "комнате, но за столом сидят и пишут, а на стуле сидят, и у "
            "стола есть столешница, а у стула — спинка.",
        frozenset(("чашка", "стакан")): "Чашка и стакан — оба посуда для "
            "питья, но чашка с ручкой и из керамики, а стакан прозрачный, "
            "без ручки и обычно стеклянный.",
        frozenset(("тарелка", "миска")): "Тарелка и миска — оба плоские или "
            "глубокие сосуды для еды, но из тарелки едят второе блюдо, а "
            "миска глубокая, из неё едят суп и салаты.",
        frozenset(("ложка", "вилка")): "Ложка и вилка — оба столовые "
            "приборы, но ложкой зачерпывают жидкую еду и суп, а вилкой с "
            "зубчиками накалывают кусочки и едят второе.",
        frozenset(("нож", "ножниц")): "Нож и ножницы — оба режущие "
            "инструменты, но ножом режут по одному лезвию, прижав продукт к "
            "доске, а ножницы режут двумя лезвиями, сводя их вместе.",
        frozenset(("шапка", "кепка")): "Шапка и кепка — оба головные уборы, "
            "но шапка тёплая, вязаная и её носят зимой, а кепка лёгкая, с "
            "козырьком и её носят летом.",
        frozenset(("куртка", "пальто")): "Куртка и пальто — оба верхняя "
            "одежда с рукавами и застёжкой, но куртка короткая, удобная и "
            "спортивная, а пальто длинное, тёплое и элегантное.",
        frozenset(("футболка", "рубашка")): "Футболка и рубашка — оба "
            "верхняя одежда на торс, но футболка лёгкая, с коротким рукавом "
            "и без пуговиц, а рубашка с воротником, пуговицами и длинным "
            "рукавом.",
        frozenset(("зима", "осень")): "Зима и осень — оба холодные времена "
            "года, но осенью листья желтеют и опадают, идут дожди, а зимой "
            "выпадает снег, замерзают реки и становится холоднее и темнее.",
        frozenset(("весна", "лето")): "Весна и лето — оба тёплые времена "
            "года, но весной тает снег, цветут растения и распускаются "
            "листья, а летом самое тёплое время, длинные дни и пора урожая.",
        frozenset(("дождь", "снег")): "Дождь и снег — оба осадки, падающие "
            "из облаков, но дождь — капли воды, он идёт в тёплую погоду, а "
            "снег — ледяные кристаллы, он выпадает в холод и лежит на земле.",
        frozenset(("гром", "молн")): "Гром и молния — оба явления грозы, "
            "но молния — яркая вспышка света в небе, а гром — раскат звука, "
            "который доносится после неё позднее.",
        frozenset(("туман", "облако")): "Туман и облака — оба скопления "
            "водяных капелек, но облака высоко в небе, а туман опускается "
            "низко над землёй и застилает дорогу и поле.",
        frozenset(("град", "снег")): "Град и снег — оба осадки в холод, но "
            "град — круглые льдинки, которые падают с неба при грозе, а "
            "снег — мягкие пушистые хлопья, которые тихо ложатся на землю.",
        frozenset(("метро", "трамвай")): "Метро и трамвай — оба городской "
            "рельсовый транспорт, но метро ходит под землёй по тоннелям и "
            "перевозит людей быстро и без пробок, а трамвай едет по "
            "рельсам на улице среди машин.",
        frozenset(("такси", "автобус")): "Такси и автобус — оба перевозят "
            "пассажиров по городу на машине, но такси едут по одному вызову "
            "и довозят до нужной двери, а автобус ходит по маршруту, "
            "останавливается на остановках и возит много людей.",
        frozenset(("грузовик", "поезд")): "Грузовик и поезд — оба возят "
            "грузы, но грузовик ездит по дорогам в любое место и везёт "
            "меньше, а поезд движется по рельсам и перевозит очень большие "
            "объёмы грузов на дальние расстояния.",
        frozenset(("корабль", "лодка")): "Корабль и лодка — оба плавают по "
            "воде, но корабль большой, с палубой и каютами, ходит по морям "
            "и океанам, а лодка маленькая, лёгкая и плавает у берега или "
            "по реке.",
        frozenset(("самолёт", "поезд")): "Самолёт и поезд — оба перевозят "
            "людей и грузы на дальние расстояния, но самолёт летит в небе "
            "быстро и сокращает время в дороге, а поезд едет по рельсам "
            "медленнее и его можно поймать в любом городе.",
        frozenset(("пароход", "теплоход")): "Пароход и теплоход — оба "
            "большие суда с двигателем, но пароход приводят в движение "
            "паровая машина и огромные колёса, а теплоход движется "
            "двигателем внутреннего сгорания и винтом.",
        frozenset(("трактор", "машина")): "Трактор и машина — оба ездят на "
            "колёсах с двигателем, но трактор медленный, мощный, работает в "
            "поле и везёт сельхозтехнику, а машина быстрая и возит людей и "
            "груз по дорогам.",
        frozenset(("врач", "медсестра")): "Врач и медсестра — оба работают "
            "в больнице и лечат людей, но врач ставит диагноз, назначает "
            "лечение и операции, а медсестра выполняет назначения, ставит "
            "уколы и ухаживает за больными.",
        frozenset(("учитель", "воспитатель")): "Учитель и воспитатель — оба "
            "учат и заботятся о детях, но учитель ведёт уроки в школе по "
            "предметам, а воспитатель занимается с малышами в детском саду, "
            "играет с ними и приучает к режиму.",
        frozenset(("повар", "пекарь")): "Повар и пекарь — оба готовят еду "
            "из продуктов, но повар варит супы, жарит и готовит блюда в "
            "столовой или ресторане, а пекарь печёт хлеб, булки и пироги в "
            "пекарне.",
        frozenset(("продавец", "кассир")): "Продавец и кассир — оба работают "
            "в магазине, но продавец помогает выбрать товар, рассказывает и "
            "отпускает покупку, а кассир принимает деньги, пробивает чек и "
            "рассчитывает покупателя на кассе.",
        frozenset(("художник", "скульптор")): "Художник и скульптор — оба "
            "создают произведения искусства, но художник рисует красками на "
            "холсте или бумаге, а скульптор лепит или высекает объёмные "
            "фигуры из глины, камня и дерева.",
        frozenset(("музыкант", "певец")): "Музыкант и певец — оба "
            "занимаются музыкой, но музыкант играет на музыкальных "
            "инструментах, а певец поёт голосом, часто со словами и мелодией.",
        frozenset(("город", "деревня")): "Город и деревня — оба места, где "
            "живут люди, но город большой, с домами, магазинами и заводами, "
            "а деревня маленькая, с домами, садами и полями вокруг.",
        frozenset(("магазин", "рынок")): "Магазин и рынок — оба места, где "
            "продают товары, но магазин крытый, товары лежат на полках с "
            "ценниками, а рынок обычно под открытым небом, где продавцы "
            "раскладывают овощи и фрукты на прилавках.",
        frozenset(("берёза", "дуб")): "Берёза и дуб — оба большие лиственные "
            "деревья, но берёза белая с гладкой корой и гибкими ветвями, а "
            "дуб могучий с толстым стволом и резными листьями, и на нём "
            "растут жёлуди.",
        frozenset(("ель", "сосна")): "Ель и сосна — оба хвойные деревья с "
            "зелёной хвоей, но у ели ветви опускаются вниз, а у сосны "
            "поднимаются вверх, и у сосны шишки крупнее, а у ели хвоя "
            "короче и колючее.",
        frozenset(("куст", "дерево")): "Куст и дерево — оба растения с "
            "древесным стволом и ветвями, но куст низкий, с несколькими "
            "короткими стволиками, а дерево высокое с одним толстым стволом.",
        frozenset(("цветок", "трава")): "Цветок и трава — оба травянистые "
            "растения, но трава зелёная, с тонкими стеблями и листьями, а "
            "цветок украшен яркими лепестками и в нём созревают семена.",
        frozenset(("яблоня", "груша")): "Яблоня и груша — оба фруктовые "
            "деревья в саду, но на яблоне растут круглые яблоки, а на "
            "груше — сочные груши, похожие на каплю.",
        frozenset(("орех", "шишка")): "Орех и шишка — оба плоды растений с "
            "твёрдой оболочкой, но орех съедобный, с ядром внутри, а шишка "
            "состоит из чешуек, в которых прячутся семена хвойных деревьев.",
        frozenset(("сковорода", "кастрюля")): "Сковорода и кастрюля — оба "
            "посуда для готовки, но на сковороде жарят котлеты, яичницу и "
            "блины на открытой поверхности, а в кастрюле варят суп, кашу и "
            "компот с водой.",
        frozenset(("чайник", "кастрюля")): "Чайник и кастрюля — оба посуда "
            "для нагревания, но чайник кипятит воду для чая и имеет носик, "
            "а кастрюля глубокая, с крышкой, и в ней готовят еду.",
        frozenset(("кружка", "стакан")): "Кружка и стакан — оба посуда для "
            "питья, но кружка с ручкой, из керамики и держит тепло, а "
            "стакан прозрачный, без ручки и обычно стеклянный.",
        frozenset(("сад", "огород")): "Сад и огород — оба место возле дома, "
            "где выращивают растения, но в саду растут деревья и кустарники "
            "с фруктами и ягодами, а в огороде грядки с овощами, зеленью и "
            "картошкой.",
        frozenset(("полдень", "полночь")): "Полдень и полночь — оба середины "
            "суток, но в полдень солнце в самой высокой точке и светит "
            "ярко, а в полночь глубокая ночь, темно и все спят.",
        frozenset(("кит", "акула")): "Кит и акула — оба живут в море и "
            "плавают в воде, но кит — огромное млекопитающее, он дышит "
            "лёгкими и кормит детёнышей молоком, а акула — рыба с жабрами "
            "и острыми зубами.",
        frozenset(("дельфин", "акула")): "Дельфин и акула — оба быстрые "
            "морские животные, но дельфин — умное млекопитающее, он "
            "дружелюбен и дышит воздухом, а акула — хищная рыба с жабрами "
            "и рядами острых зубов.",
        frozenset(("пингвин", "тюлень")): "Пингвин и тюлень — оба живут в "
            "холодных краях и хорошо плавают, но пингвин — нелетающая "
            "птица с крыльями-плавниками и перьями, а тюлень — морское "
            "млекопитающее с гладкой кожей и ластами.",
        frozenset(("пчела", "оса")): "Пчела и оса — оба летающие насекомые с "
            "полосатым тельцем и жалом, но пчела собирает нектар и делает "
            "мёд, живёт в улье, а оса хищная, не делает мёд и живёт "
            "отдельно или в гнезде.",
        frozenset(("муравей", "пчела")): "Муравей и пчела — оба "
            "общественные насекомые, живущие большой семьёй, но муравей "
            "ползает по земле и строит муравейник, а пчела летает, собирает "
            "нектар и делает мёд в улье.",
        frozenset(("паук", "жук")): "Паук и жук — оба мелкие живые существа "
            "с ножками, но паук не насекомое, у него восемь ног и он плетёт "
            "паутину, а жук насекомое с шестью ногами и жёсткими крыльями.",
        frozenset(("бабочка", "мотылёк")): "Бабочка и мотылёк — оба летающие "
            "насекомые с большими крыльями, но бабочка летает днём, яркая и "
            "красивая, а мотылёк летает в сумерках, окрашен скромнее и "
            "прилетает на свет.",
        frozenset(("черепаха", "улитка")): "Черепаха и улитка — оба медленно "
            "двигаются и имеют прочный домик, но черепаха с панцирем живёт "
            "на суше или в воде, а улитка маленькая, ползает и несёт на "
            "спине завитую ракушку.",
        frozenset(("рука", "нога")): "Рука и нога — обе части тела, но рука "
            "тонкая, с кистью и пальцами, хватает и держит предметы, а "
            "нога сильная, длинная и помогает стоять и ходить.",
        frozenset(("голова", "лицо")): "Голова и лицо — оба части тела, но "
            "голова — это вся верхняя часть тела с мозгом внутри, а лицо — "
            "передняя часть головы с глазами, носом и ртом.",
        frozenset(("зубы", "язык")): "Зуб и язык — оба части ротовой "
            "полости, но зубы твёрдые, помогают откусывать и пережёвывать "
            "еду, а язык мягкий, помогает говорить и чувствовать вкус.",
        frozenset(("сердце", "мозг")): "Сердце и мозг — оба важные органы "
            "человека, но сердце — насос, гонит кровь по сосудам, а мозг — "
            "центр мышления, руководит всем телом и хранит память.",
        frozenset(("ноготь", "зубы")): "Ноготь и зуб — оба твёрдые части "
            "тела, но ногти растут на кончиках пальцев и защищают их, а "
            "зубы во рту откусывают и пережёвывают пищу.",
        frozenset(("школа", "университет")): "Школа и университет — оба "
            "учебные заведения, но в школу ходят дети и изучают основы наук, "
            "а в университете учатся взрослые студенты и получают профессию.",
        frozenset(("школа", "больница")): "Школа и больница — оба большие "
            "здания, куда приходят люди, но в школе учатся и получают знания, "
            "а в больнице лечат и заботятся о здоровье.",
        frozenset(("больница", "аптека")): "Больница и аптека — оба места, "
            "связанные со здоровьем, но в больнице врачи лечат и делают "
            "операции, а в аптеке продают лекарства по рецепту и без него.",
        frozenset(("театр", "кинотеатр")): "Театр и кинотеатр — оба места, "
            "где показывают представления, но в театре актёры играют на "
            "сцене вживую, а в кинотеатре показывают фильм на большом экране.",
        frozenset(("цирк", "театр")): "Цирк и театр — оба здания, где "
            "устраивают зрелища, но в цирке выступают жонглёры, акробаты и "
            "дрессированные животные, а в театре актёры разыгрывают пьесу.",
        frozenset(("библиотека", "музей")): "Библиотека и музей — оба места, "
            "где хранят культурные ценности, но в библиотеке книги можно "
            "брать и читать, а в музее выставлены картины и старинные вещи "
            "для рассматривания.",
        frozenset(("вокзал", "аэропорт")): "Вокзал и аэропорт — оба места, "
            "откуда отправляются в путешествие, но с вокзала уезжают на "
            "поезде по рельсам, а из аэропорта улетают на самолёте по небу.",
        frozenset(("магазин", "аптека")): "Магазин и аптека — оба места, где "
            "продают товары, но в магазине покупают продукты, одежду и вещи, "
            "а в аптеке продают лекарства и витамины для здоровья.",
        frozenset(("почта", "банк")): "Почта и банк — оба учреждения, где "
            "происходят денежные операции, но на почте отправляют письма и "
            "посылки, а в банке хранят деньги, открывают счета и получают "
            "зарплату.",
        frozenset(("магазин", "почта")): "Магазин и почта — оба здания, куда "
            "приходят люди за нужным, но в магазине покупают товары и "
            "продукты за деньги, а на почте отправляют и получают письма и "
            "посылки.",
        frozenset(("банк", "музей")): "Банк и музей — оба здания, но в банке "
            "хранят деньги и проводят финансовые операции, а в музее "
            "выставлены картины, скульптуры и исторические ценности для "
            "осмотра.",
        frozenset(("рынок", "магазин")): "Рынок и магазин — оба места, где "
            "продают товары, но рынок обычно под открытым небом, там торгуют "
            "с прилавков и можно торговаться, а магазин крытый, с полками и "
            "ценниками, и цены там не обсуждают.",
        frozenset(("подушка", "одеяло")): "Подушка и одеяло — оба части "
            "постели для сна, но на подушке лежит голова, она мягкая и "
            "небольшая, а одеяло большое и тёплое, им укрываются со всего "
            "тела.",
        frozenset(("матрас", "подушка")): "Матрас и подушка — оба предметы "
            "для удобного сна, но матрас лежит на кровати и поддерживает "
            "всё тело, а подушка мягкая и подкладывается под голову.",
        frozenset(("шкаф", "полка")): "Шкаф и полка — оба место для хранения "
            "вещей, но шкаф большой, с дверцами, и в нём хранят одежду, а "
            "полка открытая и на неё ставят книги и предметы.",
        frozenset(("шкаф", "комод")): "Шкаф и комод — оба мебель для "
            "хранения вещей, но шкаф высокий, с полками и дверцами, а комод "
            "ниже, с ящиками, которые выдвигаются.",
        frozenset(("диван", "кресло")): "Диван и кресло — оба мягкая мебель "
            "для сидения, но диван длинный, на нём сидят или лежат несколько "
            "человек, а кресло одно с подлокотниками для одного человека.",
        frozenset(("диван", "кровать")): "Диван и кровать — оба мебель для "
            "отдыха и сна, но кровать всегда с матрасом, на ней только "
            "спят, а диван днём служит местом для сидения, а ночью "
            "раскладывается для сна.",
        frozenset(("кровать", "матрас")): "Кровать и матрас — оба предметы "
            "для сна, но кровать — это рама с опорой, а матрас мягкая "
            "набивная часть, на которой непосредственно лежит человек.",
        frozenset(("лампа", "люстра")): "Лампа и люстра — оба приборы, "
            "которые дают свет, но лампа маленькая, стоит на столе или "
            "вешается на стену, а люстра большая, висит под потолком и "
            "освещает всю комнату.",
        frozenset(("платье", "юбка")): "Платье и юбка — оба женская одежда, "
            "но платье цельное, с лифом и юбкой вместе, его надевают через "
            "голову, а юбка отдельная, без верха, и носится с кофтой.",
        frozenset(("брюки", "джинс")): "Брюки и джинсы — оба штаны, которые "
            "надевают на ноги, но брюки бывают строгие из ткани для работы "
            "и праздников, а джинсы удобные, из плотной синей ткани с "
            "карманами для повседневной носки.",
        frozenset(("шарф", "платок")): "Шарф и платок — оба куски ткани для "
            "тепла и уюта, но шарф длинный и его обматывают вокруг шеи, а "
            "платок квадратный и накрывают им голову или плечи.",
        frozenset(("перчатки", "варежки")): "Перчатки и варежки — оба одежда "
            "для рук в холод, но у перчаток есть отделение для каждого "
            "пальца, они более ловкие, а у варежек один большой отсек, и "
            "они теплее.",
        frozenset(("туфли", "ботинки")): "Туфли и ботинки — оба обувь, но "
            "туфли лёгкие, нарядные, часто на каблуке, их носят в помещении "
            "и на праздник, а ботинки выше, прочнее и подходят для улицы и "
            "холодной погоды.",
        frozenset(("платье", "костюм")): "Платье и костюм — оба нарядная "
            "одежда для торжества, но платье женское, цельное, длинное, а "
            "костюм мужской, из пиджака и брюк.",
        frozenset(("яблоко", "банан")): "Яблоко и банан — оба сладкие "
            "фрукты, но яблоко круглое, твёрдое, растёт на дереве в саду и "
            "хрустит, а банан длинный, мягкий, растёт гроздью в тёплых "
            "краях и легко чистится.",
        frozenset(("яблоко", "апельсин")): "Яблоко и апельсин — оба сочные "
            "фрукты, но яблоко с гладкой кожурой, твёрдое, а апельсин "
            "оранжевый, с толстой коркой и дольками внутри.",
        frozenset(("апельсин", "мандарин")): "Апельсин и мандарин — оба "
            "цитрусовые фрукты оранжевого цвета, но апельсин крупнее и "
            "кислее, а мандарин меньше, слаще и легче чистится.",
        frozenset(("лимон", "апельсин")): "Лимон и апельсин — оба цитрусовые "
            "фрукты с толстой кожурой, но лимон жёлтый и очень кислый, а "
            "апельсин оранжевый и сладкий.",
        frozenset(("арбуз", "дыня")): "Арбуз и дыня — оба большие сладкие "
            "бахчевые ягоды, но арбуз снаружи полосатый, а внутри красный и "
            "водянистый, а дыня жёлтая, с плотной сладкой мякотью.",
        frozenset(("виноград", "слива")): "Виноград и слива — оба сочные "
            "фрукты с косточкой или косточками, но виноград растёт гроздью "
            "из мелких ягодок, а слива отдельная, синяя или жёлтая, с "
            "одной косточкой.",
        frozenset(("клубника", "малина")): "Клубника и малина — оба сладкие "
            "ягоды с пупырышками, но клубника крупная, красная, с зелёным "
            "хвостиком, а малина маленькая, нежная и растёт на кусте.",
        frozenset(("кит", "дельфин")): "Кит и дельфин — оба морские "
            "млекопитающие, которые дышат воздухом и кормят детёнышей "
            "молоком, но кит огромный и плавает медленно, а дельфин меньше, "
            "быстрый, умный и любит выпрыгивать из воды.",
        frozenset(("гусь", "утка")): "Гусь и утка — оба водоплавающие "
            "птицы, но гусь крупнее, с длинной шеей, ходит по земле и "
            "щиплет траву, а утка меньше, с короткой шеей, хорошо ныряет и "
            "ищет еду в воде.",
        frozenset(("гусь", "лебедь")): "Гусь и лебедь — оба большие "
            "водоплавающие птицы с длинной шеей, но гусь серый, с коротким "
            "клювом, а лебедь белый, с длинной изогнутой шеей и считается "
            "красивой птицей.",
        frozenset(("корова", "бык")): "Корова и бык — оба крупные домашние "
            "животные, но корова даёт молоко и спокойная, а бык сильнее, "
            "часто с рогами и используется для работы или мяса.",
        frozenset(("овца", "коза")): "Овца и коза — оба домашние животные, "
            "которых разводят за шерсть и молоко, но овца покрыта густой "
            "шерстью, из которой делают пряжу, а коза более подвижная, "
            "любит щипать кусты и даёт меньше шерсти.",
        frozenset(("осёл", "лошадь")): "Осёл и лошадь — оба копытные "
            "животные, на которых ездят и возят грузы, но осёл меньше, "
            "выносливый и упрямый, а лошадь крупная, быстрая и красиво "
            "бегает.",
        frozenset(("почтальон", "курьер")): "Почтальон и курьер — оба "
            "доставляют письма и посылки, но почтальон носит почту по "
            "маршруту пешком или на велосипеде по домам, а курьер привозит "
            "заказ быстро на машине или мотоцикле к нужному адресу.",
        frozenset(("водитель", "шофёр")): "Водитель и шофёр — оба управляют "
            "машиной, это почти одно и то же, но слово шофёр чаще говорят "
            "о профессионале, который везёт пассажиров или груз.",
        frozenset(("капитан", "матрос")): "Капитан и матрос — оба работают "
            "на корабле, но капитан главный: он ведёт судно и принимает "
            "решения, а матрос выполняет работы на палубе и в команде.",
        frozenset(("повар", "кондитер")): "Повар и кондитер — оба готовят "
            "еду, но повар варит и жарит основные блюда в столовой или "
            "ресторане, а кондитер печёт торты, пирожные и делает сладости.",
        frozenset(("сапожник", "портн")): "Сапожник и портной — оба "
            "мастера по ремонту и изготовлению вещей, но сапожник чинит и "
            "шьёт обувь, а портной шьёт и подгоняет одежду.",
        frozenset(("столяр", "плотник")): "Столяр и плотник — оба работают "
            "с деревом, но столяр делает из дерева мебель и точные детали, "
            "а плотник строит дома, крыши и грубые конструкции из брёвен.",
        frozenset(("маляр", "кровельщик")): "Маляр и кровельщик — оба "
            "строители, но маляр красит стены и покрывает их краской, а "
            "кровельщик покрывает крыши домов материалом от дождя.",
        frozenset(("сварщик", "кузнец")): "Сварщик и кузнец — оба работают "
            "с металлом, но сварщик соединяет металлические детали сварочным "
            "аппаратом, а кузнец нагревает металл в горне и куёт его "
            "молотом.",
        frozenset(("книга", "газета")): "Книга и газета — обе печатные "
            "издания, но книга — цельное произведение с историей или наукой, "
            "которую читают долго, а газета тонкая, с новостями за сегодня "
            "и выходит каждый день или неделю.",
        frozenset(("письмо", "открытка")): "Письмо и открытка — оба послания "
            "на бумаге, отправляемые по почте, но письмо в конверте с "
            "длинным текстом, а открытка с картинкой и коротким поздравлением.",
        frozenset(("альбом", "блокнот")): "Альбом и блокнот — оба тетради "
            "из листов бумаги, но в альбоме рисуют красками и карандашом, а "
            "в блокнот записывают заметки, мысли и списки дел.",
        frozenset(("фломастер", "мел")): "Фломастер и мел — оба пишут, но "
            "фломастер оставляет яркий след чернилами на бумаге, а мел "
            "белый, пишет на доске и легко стирается.",
        frozenset(("кисть", "карандаш")): "Кисть и карандаш — оба "
            "инструменты для рисования, но кистью рисуют красками, окуная "
            "в краску, а карандашом чертят грифелем, который можно стереть.",
        frozenset(("линейка", "циркуль")): "Линейка и циркуль — оба "
            "инструменты для черчения, но линейкой чертят прямые линии и "
            "измеряют длину, а циркулем рисуют круги и окружности.",
        frozenset(("пенал", "портфель")): "Пенал и портфель — оба хранят "
            "школьные вещи, но пенал небольшой, в нём лежат ручки, карандаши "
            "и ластик, а портфель большой, в него складывают тетради, книги "
            "и пенал.",
        frozenset(("борщ", "суп")): "Борщ и суп — оба жидкие горячие блюда, "
            "но борщ — особый украинский суп со свёклой, а суп может быть "
            "любым: овощным, мясным, молочным, и варится по-разному.",
        frozenset(("пельмени", "вареники")): "Пельмени и вареники — оба "
            "тесто с начинкой внутри, но пельмени с мясом, их варят и подают "
            "с бульоном или маслом, а вареники с творогом, ягодами или "
            "картошкой, и они сладкие или с солью.",
        frozenset(("вареники", "голубц")): "Вареники и голубцы — оба "
            "блюда с начинкой, но у вареников начинка в тесте, а у голубцов "
            "фарш завёрнут в капустные листья и тушится в соусе.",
        frozenset(("хлеб", "батон")): "Хлеб и батон — оба изделия из "
            "пшеничной муки, но хлеб может быть круглым или буханкой, "
            "кирпичиком, а батон продолговатый, с надрезами сверху и "
            "нарезается на ломтики.",
        frozenset(("пряник", "кекс")): "Пряник и кекс — оба сладкая выпечка "
            "из теста, но пряник плоский, пряный, с глазурью и узором, а "
            "кекс рыхлый, высокий, с изюмом или орехами внутри.",
        frozenset(("блин", "оладьи")): "Блин и оладьи — оба жареные лепёшки "
            "из теста на сковороде, но блин тонкий, широкий и его можно "
            "сворачивать с начинкой, а оладьи толстые, пухлые и маленькие.",
        frozenset(("молоток", "топор")): "Молоток и топор — оба ручные "
            "инструменты с рукояткой, но молотком забивают гвозди и стучат, "
            "а топором рубят дрова и раскалывают дерево.",
        frozenset(("гвоздь", "шуруп")): "Гвоздь и шуруп — оба крепёжные "
            "металлические изделия, но гвоздь гладкий, его забивают молотком, "
            "а шуруп с резьбой завинчивают отвёрткой, и держится он крепче.",
        frozenset(("пила", "топор")): "Пила и топор — оба инструменты для "
            "работы с деревом, но пила тонкая, с зубчиками, и ей распиливают "
            "доски на части, а топором рубят и раскалывают.",
        frozenset(("лопата", "грабли")): "Лопата и грабли — оба садовые "
            "инструменты с длинной рукояткой, но лопатой копают землю и "
            "перекладывают грунт, а граблями с зубьями разравнивают землю "
            "и собирают листья.",
        frozenset(("ведро", "лейка")): "Ведро и лейка — оба сосуды для "
            "воды, но ведро с ручкой и открытым верхом, им носят воду, а у "
            "лейки носик с отверстиями, и ею поливают растения.",
        frozenset(("труба", "шланг")): "Труба и шланг — оба длинные полые "
            "изделия, по которым течёт вода, но труба жёсткая, металлическая "
            "или пластиковая, а шланг гибкий, резиновый, и его можно тянуть "
            "по земле.",
        frozenset(("снег", "лёд")): "Снег и лёд — оба замёрзшая вода, но "
            "снег — мягкие пушистые снежинки, а лёд — твёрдый, гладкий и "
            "прозрачный, по нему можно ходить.",
        frozenset(("дождь", "град")): "Дождь и град — оба осадки из облаков, "
            "но дождь — капли воды, мягкие и тёплые, а град — твёрдые "
            "льдинки, которые падают при грозе и бывают опасны.",
        frozenset(("ветер", "буря")): "Ветер и буря — оба движение воздуха, "
            "но ветер обычный, лёгкий или умеренный, а буря — очень сильный "
            "ветер со штормом, который ломает деревья и поднимает волны.",
        frozenset(("туман", "дождь")): "Туман и дождь — оба вода из воздуха, "
            "но туман — скопление мелких капелек у земли, а дождь — капли, "
            "падающие вниз сверху.",
        frozenset(("утро", "день")): "Утро и день — оба светлые части суток, "
            "но утро — начало дня, когда встаёт солнце, а день — середина, "
            "когда солнце стоит высоко и светло.",
        frozenset(("вечер", "ночь")): "Вечер и ночь — оба тёмные части "
            "суток, но вечер наступает, когда солнце садится, а ночь — "
            "поздняя темнота, когда все спят.",
        frozenset(("лето", "осень")): "Лето и осень — оба времена года, но "
            "лето самое тёплое, с длинными днями и созреванием плодов, а "
            "осень идёт после него, когда холодает, желтеют листья и идут "
            "дожди.",
        frozenset(("зима", "весна")): "Зима и весна — оба времена года, но "
            "зима холодная, со снегом и морозами, а весна идёт после неё, "
            "когда тает снег, теплеет и всё расцветает.",
        frozenset(("облако", "туча")): "Облако и туча — оба скопления водяных "
            "капель в небе, но облако белое, лёгкое и светлое, а туча тёмная, "
            "большая и обычно приносит грозу или дождь.",
        frozenset(("гроза", "дождь")): "Гроза и дождь — оба явления с водой, "
            "но гроза — это дождь с громом и молнией, бывает сильной и "
            "короткой, а дождь — просто капли воды без грома, может идти "
            "долго.",
        frozenset(("рассвет", "закат")): "Рассвет и закат — оба моменты "
            "смены дня и ночи, но рассвет — утро, когда солнце всходит и "
            "светлеет, а закат — вечер, когда солнце садится и темнеет.",
        frozenset(("сумерки", "рассвет")): "Сумерки и рассвет — оба "
            "промежуточное время между днём и ночью, но сумерки наступают "
            "вечером, когда темнеет, а рассвет утром, когда начинает светать.",
        frozenset(("аквариум", "террариум")): "Аквариум и террариум — оба "
            "стеклянные ёмкости для содержания живых существ, но в аквариуме "
            "держат рыб и водные растения, а в террариуме — ящериц, змей и "
            "сухопутных животных.",
        frozenset(("чердак", "подвал")): "Чердак и подвал — оба хозяйственные "
            "помещения дома, но чердак под крышей, сухой, и там хранят старые "
            "вещи, а подвал под землёй, прохладный, и там держат заготовки.",
        frozenset(("балкон", "крыльцо")): "Балкон и крыльцо — оба площадки "
            "при доме, но балкон наверху, пристроенный к стене квартиры, а "
            "крыльцо внизу у входа, с лесенкой и навесом.",
        frozenset(("гараж", "сарай")): "Гараж и сарай — оба постройки во "
            "дворе, но в гараже хранят машину, а в сарае держат инструменты, "
            "дрова или корм для животных.",
        frozenset(("вода", "сок")): "Вода и сок — оба напитки, но вода "
            "прозрачная, без вкуса и утоляет жажду, а сок сладкий, "
            "выжатый из фруктов или ягод, и в нём есть витамины.",
        frozenset(("квас", "лимонад")): "Квас и лимонад — оба прохладные "
            "напитки, но квас делают из хлеба с закваской, он слегка "
            "кисловатый и газированный, а лимонад сладкий, с лимоном и "
            "газировкой, как шипучий напиток.",
        frozenset(("компот", "морс")): "Компот и морс — оба напитки из "
            "ягод и фруктов, но компот варят из сухофруктов или свежих "
            "ягод с сахаром, а морс делают из ягод, растирая их с водой и "
            "сахаром.",
        frozenset(("шахмат", "шашки")): "Шахматы и шашки — обе настольные "
            "игры на клетчатой доске, но в шахматы играют разными фигурами с "
            "ходом у каждого, а в шашки простыми шашками, которые ходят "
            "по диагонали.",
        frozenset(("самокат", "велосипед")): "Самокат и велосипед — оба "
            "двухколёсное средство передвижения, но на самокате отталкиваются "
            "ногой и едут стоя, а на велосипеде крутят педали и едут сидя.",
        frozenset(("мяч", "кукла")): "Мяч и кукла — обе детские игрушки, но "
            "мяч круглый, в него играют, кидая и пиная его, а кукла похожа "
            "на человечка, её наряжают, кормят и укладывают спать.",
        frozenset(("секунда", "минута")): "Секунда и минута — обе единицы "
            "измерения времени, но секунда самая маленькая, а минута состоит "
            "из шестидесяти секунд и длится дольше.",
        frozenset(("минута", "часы")): "Минута и час — обе единицы времени, "
            "но минута короткая, в часе шестьдесят минут, и час длится "
            "намного дольше.",
        frozenset(("часы", "день")): "Час и день — обе единицы времени, но "
            "час короткий, в сутках двадцать четыре часа, а день — это вся "
            "светлая часть суток или целые сутки.",
        frozenset(("день", "неделя")): "День и неделя — обе единицы времени, "
            "но день — это одни сутки, а неделя состоит из семи дней и "
            "длится дольше.",
        frozenset(("неделя", "месяц")): "Неделя и месяц — обе единицы "
            "времени, но неделя из семи дней, а в месяце около четырёх "
            "недель, и месяц длится дольше.",
        frozenset(("месяц", "год")): "Месяц и год — обе единицы времени, но "
            "месяц короче, в году двенадцать месяцев, и год длится намного "
            "дольше.",
        frozenset(("год", "век")): "Год и век — обе единицы времени, но год "
            "длится двенадцать месяцев, а век — это сто лет, и он длится "
            "гораздо дольше.",
        frozenset(("век", "тысячелет")): "Век и тысячелетие — обе большие "
            "единицы времени, но век — это сто лет, а тысячелетие — тысяча "
            "лет, десять веков.",
        frozenset(("круг", "квадрат")): "Круг и квадрат — обе плоские "
            "фигуры, но круг без углов, с ровной окружностью, а у квадрата "
            "четыре прямых угла и четыре равные стороны.",
        frozenset(("квадрат", "прямоугольник")): "Квадрат и прямоугольник — "
            "оба четырёхугольники с прямыми углами, но у квадрата все стороны "
            "равны, а у прямоугольника противоположные стороны равны, но "
            "длинные и короткие.",
        frozenset(("треугольник", "ромб")): "Треугольник и ромб — обе плоские "
            "геометрические фигуры, но у треугольника три стороны и три угла, "
            "а у ромба четыре равные стороны и он похож на перекошенный "
            "квадрат.",
        frozenset(("шар", "куб")): "Шар и куб — обе объёмные фигуры, но шар "
            "круглый со всех сторон и катится, а куб с шестью квадратными "
            "гранями и стоит на месте на грани.",
        frozenset(("овал", "круг")): "Овал и круг — обе округлые плоские "
            "фигуры, но круг идеально ровный, а овал вытянутый, как "
            "растянутый круг.",
        frozenset(("терапевт", "хирург")): "Терапевт и хирург — оба врачи, "
            "но терапевт лечит лекарствами и обследует больных, а хирург "
            "проводит операции и лечит с помощью хирургических инструментов.",
        frozenset(("стоматолог", "окулист")): "Стоматолог и окулист — оба "
            "врачи узких специальностей, но стоматолог лечит зубы и дёсны, "
            "а окулист проверяет зрение и лечит глаза.",
        frozenset(("врач", "ветеринар")): "Врач и ветеринар — оба лечат, но "
            "врач лечит людей, а ветеринар лечит животных: кошек, собак и "
            "других питомцев.",
        frozenset(("учитель", "тренер")): "Учитель и тренер — оба обучают, но "
            "учитель преподаёт в школе знания и школьные предметы, а тренер "
            "тренирует спортсменов и учит их соревноваться.",
        frozenset(("полицейск", "военн")): "Полицейский и военный — оба "
            "служат в форме и защищают порядок, но полицейский следит за "
            "законом в городе и ловит нарушителей, а военный служит в армии "
            "и защищает страну от внешней опасности.",
        frozenset(("солдат", "офицер")): "Солдат и офицер — оба военные, но "
            "солдат выполняет приказы и несёт службу в строю, а офицер "
            "командует, отдаёт приказы и имеет высшее звание.",
        frozenset(("директор", "учитель")): "Директор и учитель — оба "
            "работают в школе, но директор руководит всей школой и учителями, "
            "а учитель ведёт уроки и учит учеников.",
        frozenset(("микроволновка", "духовка")): "Микроволновка и духовка — "
            "оба приборы для готовки еды с нагревом, но микроволновка "
            "быстро разогревает готовую еду, а духовка печёт и пропекает "
            "блюда при высокой температуре дольше.",
        frozenset(("плита", "духовка")): "Плита и духовка — оба кухонные "
            "приборы для готовки, но плита варит и жарит на конфорках сверху, "
            "а духовка печёт и запекает блюда во внутренней камере.",
        frozenset(("чайник", "кофемашина")): "Чайник и кофемашина — оба "
            "приборы для горячих напитков, но чайник кипятит воду, а "
            "кофемашина варит кофе из молотых зёрен.",
        frozenset(("тостер", "микроволновка")): "Тостер и микроволновка — "
            "оба бытовые приборы, но тостер поджаривает хлеб до хрустящей "
            "корочки, а микроволновка разогревает разнообразную еду.",
        frozenset(("холодильник", "посудомойка")): "Холодильник и посудомойка "
            "— оба кухонные приборы, но холодильник охлаждает и хранит "
            "продукты, а посудомойка моет грязную посуду водой с моющим "
            "средством.",
        frozenset(("пустыня", "степь")): "Пустыня и степь — обе безлесные "
            "равнины, но в пустыне очень сухо, мало дождя, песок и почти "
            "нет растительности, а в степи растёт трава и бывает больше "
            "влаги.",
        frozenset(("тундра", "тайга")): "Тундра и тайга — оба северные "
            "природные зоны, но в тундре холодно, мало деревьев и вечная "
            "мерзлота, а в тайге густые хвойные леса из елей и сосен.",
        frozenset(("тайга", "лес")): "Тайга и лес — оба территории с "
            "деревьями, но тайга — огромный хвойный лес на севере, а лес "
            "может быть и берёзовым, лиственным или смешанным.",
        frozenset(("лес", "луг")): "Лес и луг — обе природные зоны с "
            "растениями, но в лесу густые деревья и тень, а луг — открытая "
            "поляна с травой, цветами и солнцем.",
        frozenset(("болото", "луг")): "Болото и луг — обе территории с "
            "травой, но болото влажное, топкое, с водой и мохом, а луг "
            "сухой луг, где растёт трава и пасутся животные.",
        frozenset(("равнина", "плато")): "Равнина и плато — обе относительно "
            "ровные поверхности земли, но равнина лежит низко и гладко, а "
            "плато приподнято высоко и похоже на плоский стол в горах.",
        frozenset(("овраг", "холм")): "Овраг и холм — оба неровности земной "
            "поверхности, но овраг — это углубление, овраг-выемка в земле, "
            "а холм — возвышение, выпуклая горка.",
        frozenset(("степь", "саванна")): "Степь и саванна — обе равнины с "
            "травой, но степь находится в умеренном климате и холодная "
            "зимой, а саванна в тёплом климате, где растут отдельные "
            "деревья и живут крупные животные.",
        frozenset(("лук", "чеснок")): "Лук и чеснок — оба луковичные овощи "
            "с резким запахом, но лук круглый или овальный со слоями, а "
            "чеснок состоит из зубчиков и острее на вкус.",
        frozenset(("огурец", "помидор")): "Огурец и помидор — оба сочные "
            "овощи с грядки, но огурец зелёный, удлинённый, хрустящий и "
            "свежий на вкус, а помидор круглый, красный и сладковатый.",
        frozenset(("фасоль", "горох")): "Фасоль и горох — оба бобовые "
            "растения со стручками и семенами внутри, но горох круглый и "
            "зелёный, а фасоль бывает белой, красной и продолговатой.",
        frozenset(("редис", "морковь")): "Редис и морковь — оба корнеплоды, "
            "растущие в земле, но редис круглый или овальный, красный и "
            "острый, а морковь длинная, оранжевая и сладкая.",
        frozenset(("кабачок", "тыква")): "Кабачок и тыква — оба крупные "
            "бахчевые овощи с плотной мякотью, но кабачок продолговатый, "
            "зелёный и нежный, а тыква круглая, оранжевая и сладкая на вкус.",
        frozenset(("метро", "электричка")): "Метро и электричка — оба "
            "рельсовый транспорт, но метро ходит под землёй по городу и "
            "останавливается часто, а электричка возит людей между городами "
            "и пригородами на дальние расстояния.",
        frozenset(("поезд", "электричка")): "Поезд и электричка — оба "
            "движутся по железной дороге, но поезд дальнего следования везёт "
            "пассажиров между городами, а электричка курсирует в пригород "
            "и обратно с частыми остановками.",
        frozenset(("автобус", "маршрутка")): "Автобус и маршрутка — оба "
            "городской пассажирский транспорт, но автобус большой, ходит по "
            "расписанию и вмещает много людей, а маршрутка меньше, быстрее и "
            "перевозит меньше пассажиров.",
        frozenset(("такси", "маршрутка")): "Такси и маршрутка — оба возят "
            "пассажиров по городу, но такси едет прямо до нужного адреса по "
            "одному заказу, а маршрутка ходит по маршруту с остановками.",
        frozenset(("вокзал", "стан")): "Вокзал и станция — оба места, где "
            "останавливается поезд, но вокзал — большой железнодорожный "
            "узел с залом ожидания, а станция — остановочный пункт на "
            "дороге, обычно проще.",
        frozenset(("стул", "табурет")): "Стул и табурет — оба сиденья, но "
            "у стула есть спинка, на которую опираться, а табурет — просто "
            "сиденье на ножках без спинки.",
        frozenset(("стул", "кресло")): "Стул и кресло — оба сиденья со "
            "спинкой, но кресло больше, мягче и с подлокотниками, а стул "
            "жёсткий и без ручек.",
        frozenset(("диван", "кровать")): "Диван и кровать — оба места, где "
            "спят, но кровать только для сна, а на диване днём сидят, а "
            "вечером раскладывают его в спальное место.",
        frozenset(("шкаф", "комод")): "Шкаф и комод — оба для хранения "
            "вещей, но шкаф высокий с полками и дверцами, а комод — низкий "
            "ящиками, выдвигающимися наружу.",
        frozenset(("ручка", "карандаш")): "Ручка и карандаш — оба пишут, но "
            "ручка пишет чернилами и не стирается, а карандаш пишет "
            "грифелем, и надпись можно стереть ластиком.",
        frozenset(("ручка", "фломастер")): "Ручка и фломастер — оба "
            "оставляют след на бумаге, но ручка пишет чернилами тонкой "
            "линией, а фломастер рисует ярким толстым следом на основе "
            "краски.",
        frozenset(("тетрадь", "блокнот")): "Тетрадь и блокнот — оба "
            "собраны из листов бумаги для записей, но тетрадь в линию или "
            "клетку для уроков, а блокнот — для заметок и можно отрывать "
            "листы.",
        frozenset(("тетрадь", "альбом")): "Тетрадь и альбом — оба из "
            "бумажных листов, но в тетради пишут, а в альбоме рисуют на "
            "плотной бумаге.",
        frozenset(("портфель", "рюкзак")): "Портфель и рюкзак — оба сумки "
            "для книг и вещей, но портфель носят в руке или на плече, а "
            "рюкзак — на спине за лямки.",
        frozenset(("доска", "мел")): "Доска и мел — оба нужны для письма в "
            "классе, но доска — гладкое место, где пишут, а мел — палочка, "
            "которой пишут на доске.",
        frozenset(("куртка", "пальто")): "Куртка и пальто — оба верхняя "
            "одежда для защиты от холода, но куртка короче, спортивнее и "
            "удобна для движения, а пальто длинное и более нарядное.",
        frozenset(("шапка", "кепка")): "Шапка и кепка — оба носят на "
            "голове, но шапка вязаная, тёплая и закрывает уши зимой, а "
            "кепка лёгкая с козырьком и защищает от солнца.",
        frozenset(("перчатки", "варежки")): "Перчатки и варежки — оба "
            "одевают на руки в холод, но в перчатках каждый палец отдельно, "
            "а в варежках все пальцы вместе и в них теплее, но неудобнее.",
        frozenset(("рубашка", "футболка")): "Рубашка и футболка — оба "
            "одевают на верх тела, но рубашка с пуговицами и воротником, а "
            "футболка — мягкая, без пуговиц и с короткими рукавами.",
        frozenset(("платье", "юбка")): "Платье и юбка — оба женская одежда, "
            "но платье целиком закрывает верх и низ, а юбка — только нижняя "
            "часть, без верха.",
        frozenset(("брюки", "джинс")): "Брюки и джинсы — оба одежда для "
            "ног с двумя штанинами, но джинсы сшиты из плотной джинсовой "
            "ткани, а обычные брюки бывают из костюмной или лёгкой ткани.",
        frozenset(("брюки", "штан")): "Брюки и штаны — оба одежда для ног "
            "с двумя штанинами, это почти одно и то же, но «брюки» звучит "
            "более нарядно, а «штаны» — по-простому.",
        frozenset(("ботинки", "сапоги")): "Ботинки и сапоги — оба обувь "
            "для холодной погоды, но ботинки закрывают ступню и немного "
            "голень, а сапоги поднимаются высоко вверх по ноге.",
        frozenset(("ботинки", "туфли")): "Ботинки и туфли — оба обувь, "
            "но ботинки высокие, тёплые и на шнурках для улицы, а туфли "
            "низкие, лёгкие и нарядные.",
        frozenset(("молоток", "топор")): "Молоток и топор — оба ударные "
            "инструменты с ручкой, но молотком забивают гвозди бойком, а "
            "топором рубят дерево острым лезвием.",
        frozenset(("гвоздь", "шуруп")): "Гвоздь и шуруп — оба крепёж из "
            "металла, но гвоздь гладкий и его забивают молотком, а шуруп с "
            "резьбой и вкручивают отвёрткой.",
        frozenset(("гайка", "болт")): "Гайка и болт — оба крепёж с резьбой, "
            "но болт — стержень с головкой, а гайка — кольцо с резьбой "
            "внутри, которое навинчивают на болт.",
        frozenset(("ключ", "отвёртка")): "Ключ и отвёртка — оба инструменты "
            "для работы с крепёжом, но ключом закручивают гайки и болты, а "
            "отвёрткой — шурупы и винты.",
        frozenset(("пила", "топор")): "Пила и топор — оба инструменты для "
            "работы с деревом, но пила пилит ровно зубьями, а топор рубит и "
            "колет ударом лезвия.",
        frozenset(("лопата", "грабли")): "Лопата и грабли — оба садовые "
            "инструменты на длинной ручке, но лопатой копают и переворачивают "
            "землю, а граблями разравнивают её и собирают листья.",
        frozenset(("плотник", "столяр")): "Плотник и столяр — оба "
            "мастера по дереву, но плотник строит дома и делает грубые "
            "работы, а столяр делает мебель и тонкие изделия.",
        frozenset(("рыбак", "охотник")): "Рыбак и охотник — оба добывают "
            "пищу на природе, но рыбак ловит рыбу в воде удочкой или сетью, "
            "а охотник выслеживает зверей в лесу.",
        frozenset(("корабль", "пароход")): "Корабль и пароход — оба большие "
            "водные суда, но корабль — общее название судна, а пароход — "
            "судно, движущееся с помощью парового двигателя и колёс.",
        frozenset(("катер", "лодка")): "Катер и лодка — оба небольшие "
            "судна для воды, но катер имеет мотор и движется быстро, а "
            "лодка обычно гребут вёслами или плывёт медленно.",
        frozenset(("машина", "грузовик")): "Машина и грузовик — оба "
            "автомобили с мотором и колёсами, но машина возит людей, а "
            "грузовик — большая машина для перевозки тяжестей и грузов.",
        frozenset(("экскаватор", "бульдозер")): "Экскаватор и бульдозер — "
            "оба большие строительные машины, но экскаватор копает землю "
            "ковшом, а бульдозер толкает и ровняет грунт ножом спереди.",
        frozenset(("самолёт", "ракета")): "Самолёт и ракета — оба летают "
            "высоко, но самолёт с крыльями летит на двигателях в воздухе, "
            "а ракета с реактивным двигателем летит очень высоко, в космос.",
        frozenset(("пилот", "лётчик")): "Пилот и лётчик — оба управляют "
            "самолётом в воздухе, это почти одно и то же, но «лётчик» — "
            "русское слово, а «пилот» — международное и звучит официальнее.",
        frozenset(("вчера", "сегодня")): "Вчера и сегодня — оба дни вокруг "
            "настоящего момента, но вчера — день, который уже прошёл, а "
            "сегодня — день, который идёт сейчас.",
        frozenset(("сегодня", "завтра")): "Сегодня и завтра — оба дни "
            "вокруг настоящего момента, но сегодня — день, который идёт "
            "сейчас, а завтра — день, который будет после этой ночи.",
        frozenset(("сутки", "неделя")): "Сутки и неделя — оба единицы "
            "времени, но сутки — это день и ночь вместе, двадцать четыре "
            "часа, а неделя — семь суток подряд.",
        frozenset(("видеокарта", "процессор")): "Процессор и видеокарта — оба "
            "считают, но по-разному: процессор выполняет любые команды по "
            "очереди и хорош в общих задачах, тогда как видеокарта делает "
            "тысячи простых операций сразу и нужна для картинки и нейросетей.",
        frozenset(("wi-fi", "интернет")): "Интернет и wifi (Wi-Fi) — не одно "
            "и то же, хотя их часто путают. Общее: оба нужны, чтобы устройство "
            "выходило в сеть. Различие: интернет — сеть сетей с адресами во всём "
            "мире, тогда как wifi — лишь способ подключить устройство к этой "
            "сети по радио, без провода.",
        frozenset(("ssd", "жёсткий диск")): "Жесткий диск и SSD (ssd) хранят "
            "файлы, и в этом их общее. Различие: жёсткий диск читает данные с "
            "вращающихся пластин, тогда как SSD держит их в микросхемах памяти — "
            "быстрее, тише и дороже за тот же объём.",
        frozenset(("роутер", "модем")): "Роутер и модем стоят рядом и оба "
            "нужны для домашнего интернета. Различие: модем превращает сигнал "
            "линии в цифровые данные, тогда как роутер раздаёт этот интернет "
            "между устройствами дома и связывает их в одну сеть.",
        frozenset(("сайт", "применен")): "Сайт и приложение дают одну услугу "
            "по-разному: сайт открывается в браузере по адресу и не требует "
            "установки, тогда как приложение ставится на устройство и работает "
            "само, быстрее и с доступом к его возможностям.",
        frozenset(("сайт", "приложен")): "Сайт и приложение дают одну услугу "
            "по-разному: сайт открывается в браузере по адресу и не требует "
            "установки, тогда как приложение ставится на устройство и работает "
            "само, быстрее и с доступом к его возможностям.",
        frozenset(("монитор", "телевизор")): "Монитор и телевизор показывают "
            "картинку — это их общее. Различие: монитор — экран для работы с "
            "компьютером вблизи, тогда как телевизор рассчитан на просмотр с "
            "расстояния и обычно имеет свой тюнер и громкий звук.",
        frozenset(("ноутбук", "планшет")): "Ноутбук и планшет — переносные "
            "устройства, но работают по-разному: ноутбук — полноценный "
            "компьютер с клавиатурой и своей системой, тогда как планшет "
            "управляется пальцем по сенсорному экрану и проще.",
        frozenset(("гром", "молн")): "Гром и молния — оба явления грозы, "
            "но молния — это яркая вспышка света от искры в небе, а гром — "
            "громкий звук, который слышно после вспышки.",
        frozenset(("гроза", "буря")): "Гроза и буря — оба ненастье с сильным "
            "ветром, но гроза с громом, молниями и дождём, а буря — сильный "
            "ветер, который всё ломает и несёт.",
        frozenset(("ураган", "буря")): "Ураган и буря — оба очень сильный "
            "ветер, но буря — сильный ветер, а ураган — ещё сильнее, кружит "
            "и разрушает дома и деревья.",
        frozenset(("дождь", "ливень")): "Дождь и ливень — оба вода, "
            "падающая с неба каплями, но дождь может быть небольшим и "
            "тихим, а ливень — очень сильный и быстрый дождь.",
        frozenset(("река", "пруд")): "Река и пруд — оба водоёмы с водой, "
            "но река течёт и несёт воду вдаль, а пруд — стоячая вода без "
            "течения, часто рукотворный.",
        frozenset(("ручей", "река")): "Ручей и река — оба потоки воды, "
            "но ручей маленький и узкий, через него можно перешагнуть, а "
            "река широкая и глубокая, по ней плывут лодки.",
        frozenset(("болото", "овраг")): "Болото и овраг — оба неровные "
            "участки земли, но болото — топкая мокрая низина с водой и "
            "мхом, а овраг — глубокая выемка в земле, размытая водой.",
        frozenset(("пещера", "овраг")): "Пещера и овраг — оба углубления "
            "в земле, но пещера — полость в горе или скале с ходами внутрь, "
            "а овраг — открытая выемка на поверхности, размытая дождём.",
        frozenset(("собака", "волк")): "Собака и волк — оба хищники из "
            "семейства псовых, но собака живёт с человеком и ручная, а волк "
            "дикий, живёт в лесу и воет на луну.",
        frozenset(("слон", "носорог")): "Слон и носорог — оба очень "
            "крупные животные, но у слона длинный хобот и уши, а у носорога "
            "один или два рога на морде.",
        frozenset(("дельфин", "тюлень")): "Дельфин и тюлень — оба живут в "
            "море и дышат воздухом, но дельфин плавает быстро и умный, а "
            "тюлень неуклюжий на суше и лежит на льду или берегу.",
        frozenset(("крокодил", "акула")): "Крокодил и акула — оба опасные "
            "хищники с острыми зубами, но крокодил живёт в реках и "
            "дышит лёгкими, а акула — рыба, живущая в океане и дышащая жабрами.",
        frozenset(("орёл", "сокол")): "Орёл и сокол — оба крупные хищные "
            "птицы, но орёл большой с широкими крыльями и парит высоко, а "
            "сокол быстрее и ловит добычу в пикирующем полёте.",
        frozenset(("орёл", "ястреб")): "Орёл и ястреб — оба хищные птицы, "
            "но орёл крупный и парит высоко над горами, а ястреб меньше, "
            "быстро летает среди леса и охотится на мелких зверей.",
        frozenset(("ворона", "сорока")): "Ворона и сорока — оба чёрно-"
            "белые птицы из семейства врановых, но ворона крупная и серая "
            "с чёрным, а сорока поменьше с длинным хвостом и белым боком.",
        frozenset(("вороб", "голубь")): "Воробей и голубь — оба "
            "городские птицы, но воробей маленький и коричневый, а голубь "
            "крупнее и серо-сизый.",
        frozenset(("белка", "заяц")): "Белка и заяц — оба лесные звери, "
            "но белка живёт на дереве, прыгает и грызёт орехи, а заяц "
            "быстро бегает по земле и ест траву.",
        frozenset(("ёж", "ёжик")): "Ёж и ёжик — это одно и то же животное "
            "с колючками на спине, просто «ёжик» — ласковое название ежа.",
        frozenset(("сова", "филин")): "Сова и филин — оба ночные хищные "
            "птицы с большими глазами, но филин крупнее совы и с ушными "
            "пучками перьев на голове.",
        frozenset(("хомяк", "крыса")): "Хомяк и крыса — оба грызуны с "
            "острыми зубами, но хомяк пухлый, с коротким хвостом и запасом "
            "еды за щеками, а крыса проворная, с длинным хвостом.",
        frozenset(("ворона", "вороб")): "Ворона и воробей — оба городские "
            "птицы, но ворона крупная, чёрная и умная, а воробей маленький "
            "и серо-коричневый.",
        frozenset(("сумерки", "закат")): "Сумерки и закат — оба время, "
            "когда день заканчивается, но закат — когда солнце уходит за "
            "горизонт, а сумерки — полутьма после заката, перед ночью.",
        frozenset(("свет", "тень")): "Свет и тень — оба связаны с теплом "
            "от лампы или солнца, но свет яркий и освещает всё вокруг, а "
            "тень — тёмное место, которое появляется за предметом на свету.",
        frozenset(("звук", "эхо")): "Звук и эхо — оба то, что мы слышим, "
            "но звук — сам шум или голос, а эхо — отражённый звук, который "
            "возвращается к нам от стены или горы.",
        frozenset(("день", "сутки")): "День и сутки — оба единицы времени, "
            "но сутки — это день и ночь вместе, двадцать четыре часа, а "
            "день — только светлая часть суток.",
        frozenset(("часы", "сутки")): "Час и сутки — оба единицы времени, "
            "но час — шестьдесят минут, а сутки — двадцать четыре часа, "
            "то есть целые день и ночь.",
        frozenset(("рассвет", "утро")): "Рассвет и утро — оба начало дня, "
            "когда светает, но рассвет — момент, когда впервые видно солнце, "
            "а утро — время после рассвета до полудня.",
        frozenset(("закат", "вечер")): "Закат и вечер — оба конец дня, но "
            "закат — когда солнце уходит за горизонт, а вечер — время после "
            "заката до наступления ночи.",
        frozenset(("сутки", "месяц")): "Сутки и месяц — оба единицы "
            "времени, но сутки — это день и ночь, двадцать четыре часа, а "
            "месяц — около тридцати суток, примерно годовой отрезок.",
        frozenset(("блендер", "миксер")): "Блендер и миксер — оба кухонные "
            "приборы для перемешивания, но блендер режет и измельчает всё в "
            "пюре, а миксер взбивает и перемешивает жидкое и тесто.",
        frozenset(("лампа", "торшер")): "Лампа и торшер — оба дают свет, "
            "но лампа маленькая настольная или настенная, а торшер — "
            "напольный светильник на высокой ножке.",
        frozenset(("торшер", "люстра")): "Торшер и люстра — оба дают свет "
            "в комнате, но торшер стоит на полу на высокой ножке, а люстра "
            "подвешена к потолку и светит сверху на всю комнату.",
        frozenset(("стол", "комод")): "Стол и комод — оба предметы мебели, "
            "но за столом работают или едят на его столешнице, а комод "
            "служит для хранения вещей в ящиках.",
        frozenset(("утюг", "пылесос")): "Утюг и пылесос — оба электроприборы "
            "для уборки и ухода, но утюг нагревается и разглаживает одежду, "
            "а пылесос втягивает пыль и мусор с пола и ковров.",
        frozenset(("зеркало", "стекло")): "Зеркало и стекло — оба гладкие "
            "прозрачные или светлые поверхности, но в зеркале видно своё "
            "отражение, а в стекле — нет, так как стекло прозрачное.",
        frozenset(("ковёр", "пол")): "Ковёр и пол — оба поверхность, по "
            "которой ходят, но пол твёрдый и бывает из дерева или бетона, "
            "а ковёр — мягкое тканое покрытие, которое лежит на полу.",
        frozenset(("вишня", "слива")): "Вишня и слива — оба сочные "
            "фрукты с косточкой внутри, но вишня маленькая, красная и с "
            "кислинкой, а слива крупнее, синяя или жёлтая и слаще.",
        frozenset(("банан", "ананас")): "Банан и ананас — оба тропические "
            "сладкие фрукты, но банан длинный, жёлтый и мягкий, а ананас "
            "крупный, колючий снаружи и жёлтый внутри.",
        frozenset(("киви", "манго")): "Киви и манго — оба сладкие фрукты "
            "из тёплых стран, но киви маленький, зелёный и с пушистой "
            "коричневой шкуркой, а манго крупный, оранжево-жёлтый.",
        frozenset(("малина", "смородина")): "Малина и смородина — оба "
            "маленькие ягоды с куста, но малина мягкая, красная или жёлтая "
            "и с косточками, а смородина растёт гроздьями и бывает чёрной "
            "или красной.",
        frozenset(("картофель", "морковь")): "Картофель и морковь — оба "
            "корнеплоды, растущие в земле, но картофель круглый, коричневый "
            "и крахмалистый, а морковь длинная, оранжевая и сладкая.",
        frozenset(("перец", "огурец")): "Перец и огурец — оба сочные "
            "овощи с грядки, но перец сладкий и сочный с семенами внутри, "
            "бывает разных цветов, а огурец зелёный, длинный и хрустящий.",
        frozenset(("петрушка", "укроп")): "Петрушка и укроп — оба зелёные "
            "травы, которыми посыпают еду, но петрушка с плоскими листиками "
            "и нежным вкусом, а укроп с тонкими веточками и пахучими "
            "пушистыми листьями.",
        frozenset(("тыква", "дыня")): "Тыква и дыня — оба крупные плоды "
            "с плотной мякотью, но тыква оранжевая и используется как овощ "
            "в кашу и суп, а дыня сладкая ароматная ягода.",
        frozenset(("кондитер", "пекарь")): "Кондитер и пекарь — оба "
            "готовят из теста, но пекарь печёт хлеб, батоны и булки, а "
            "кондитер делает торты, пирожные и сладости.",
        frozenset(("портн", "швея")): "Портной и швея — оба шьют одежду, "
            "но портной делает целое изделие по меркам и крою, а швея "
            "шьёт детали и части одежды на машинке.",
        frozenset(("сапожник", "часовщик")): "Сапожник и часовщик — оба "
            "мастера по ремонту, но сапожник чинит обувь: подошвы, каблуки, "
            "а часовщик чинит часы — шестерёнки и механизм.",
        frozenset(("сантехник", "электрик")): "Сантехник и электрик — оба "
            "рабочие, которые чинят в доме, но сантехник занимается трубами "
            "и водой, а электрик — проводами и светом.",
        frozenset(("каменщик", "маляр")): "Каменщик и маляр — оба "
            "строители, но каменщик кладёт кирпичи и строит стены, а маляр "
            "красит и красиво отделывает готовые поверхности.",
        frozenset(("журналист", "писатель")): "Журналист и писатель — оба "
            "сочиняют тексты, но журналист пишет про настоящие события для "
            "газеты или сайта, а писатель придумывает повести и романы.",
        frozenset(("поэт", "писатель")): "Поэт и писатель — оба создают "
            "литературные произведения, но поэт пишет стихи с рифмой и "
            "ритмом, а писатель сочиняет прозу — рассказы и романы.",
        frozenset(("архитектор", "дизайнер")): "Архитектор и дизайнер — "
            "оба придумывают, как что-то выглядит, но архитектор проектирует "
            "здания и дома, а дизайнер — оформление вещей и интерьера.",
        frozenset(("психолог", "врач")): "Психолог и врач — оба помогают "
            "людям со здоровьем, но врач лечит тело — органы и болезни, а "
            "психолог — чувства, настроение и переживания.",
        frozenset(("пожарн", "полицейск")): "Пожарный и полицейский — оба "
            "служат и помогают людям, но пожарный тушит пожары и спасает из "
            "огня, а полицейский следит за порядком и ловит нарушителей.",
        frozenset(("охранник", "полицейск")): "Охранник и полицейский — "
            "оба охраняют и следят за порядком, но охранник служит на "
            "конкретном объекте, а полицейский следит за порядком во всём "
            "городе.",
        frozenset(("бухгалтер", "кассир")): "Бухгалтер и кассир — оба "
            "работают с деньгами, но бухгалтер считает доходы и расходы "
            "компании и ведёт отчёты, а кассир принимает и выдаёт деньги "
            "покупателям.",
        frozenset(("юрист", "адвокат")): "Юрист и адвокат — оба знатоки "
            "законов, но юрист работает с правом и документами, а адвокат "
            "защищает людей в суде.",
        frozenset(("плотник", "сварщик")): "Плотник и сварщик — оба "
            "мастера, строящие и чинящие изделия, но плотник работает с "
            "деревом, а сварщик соединяет металлические части сваркой.",
        frozenset(("сумерки", "вечер")): "Сумерки и вечер — оба время после "
            "заката, но вечер — обычное время после дня, а сумерки — "
            "полутемнота между светом дня и темнотой ночи.",
        frozenset(("звук", "голос")): "Звук и голос — оба то, что мы "
            "слышим, но звук — любой шум или сигнал, а голос — звук, "
            "который издаёт человек, когда говорит или поёт.",
        frozenset(("мелод", "звук")): "Мелодия и звук — оба слышимые, "
            "но звук — отдельный тон или шум, а мелодия — ряд звуков, "
            "сложенных в приятную музыкальную последовательность.",
        frozenset(("хлопок", "звук")): "Хлопок и звук — оба то, что "
            "слышно, но звук — общее название, а хлопок — короткий резкий "
            "громкий звук, например отладошивания.",
        frozenset(("кашель", "звук")): "Кашель и звук — оба то, что "
            "слышно, но звук — общее название, а кашель — резкий звук, "
            "который человек издаёт, когда чистит горло от дыма или пыли.",
        frozenset(("звезда", "планета")): "Звезда и планета — оба небесные "
            "тела, но звезда огромная и сама светится, а планета меньше, не "
            "светится сама и крутится вокруг звезды.",
        frozenset(("планета", "спутник")): "Планета и спутник — оба небесные "
            "тела, но планета большая и крутится вокруг звезды, а спутник "
            "меньше и крутится вокруг планеты, как луна вокруг земли.",
        frozenset(("космос", "вселенн")): "Космос и вселенная — оба необъятное "
            "пространство, но космос — пустое пространство со звёздами, а "
            "вселенная — всё, что существует, включая и космос.",
        frozenset(("галактика", "вселенн")): "Галактика и вселенная — оба "
            "огромные скопления, но галактика — это система из множества "
            "звёзд, а вселенная — всё пространство со всеми галактиками.",
        frozenset(("астероид", "комета")): "Астероид и комета — оба небесные "
            "тела, летающие в космосе, но астероид — каменная глыба, а "
            "комета — изо льда и пыли и оставляет светящийся хвост.",
        frozenset(("орбита", "спутник")): "Орбита и спутник — оба связаны с "
            "движением тел в космосе, но орбита — путь, по которому летит "
            "объект, а спутник — само тело, которое движется по орбите.",
        frozenset(("север", "юг")): "Север и юг — оба стороны света, но "
            "север — направление к полюсу наверху карты, а юг — "
            "противоположное направление внизу карты.",
        frozenset(("восток", "запад")): "Восток и запад — оба стороны "
            "света, но восток — где встаёт солнце, справа на карте, а "
            "запад — где солнце садится, слева на карте.",
        frozenset(("север", "запад")): "Север и запад — оба стороны света, "
            "но север — направление к холоду и полюсу, а запад — направление, "
            "где заходит солнце.",
        frozenset(("скала", "овраг")): "Скала и овраг — оба неровности "
            "земной поверхности, но скала — твёрдый каменный выступ вверх, "
            "а овраг — глубокая выемка вниз, размытая водой.",
        frozenset(("футбол", "хокк")): "Футбол и хоккей — оба командные "
            "спортивные игры, но футбол играют ногами по полю мячом, а "
            "хоккей — это шайба и клюшки на льду.",
        frozenset(("баскетбол", "волейбол")): "Баскетбол и волейбол — оба "
            "игры с мячом в зале, но в баскетболе мяч бросают в корзину "
            "руками, а в волейболе перебрасывают через сетку.",
        frozenset(("футбол", "баскетбол")): "Футбол и баскетбол — оба "
            "командные игры с мячом, но в футболе мяч забивают ногами в "
            "ворота, а в баскетболе бросают руками в корзину.",
        frozenset(("шахмат", "шашки")): "Шахматы и шашки — оба настольные "
            "игры на доске с фигурами, но в шахматах много разных фигур с "
            "особыми ходами, а в шашках все фишки ходят одинаково.",
        frozenset(("бокс", "борьба")): "Бокс и борьба — оба спортивные "
            "единоборства, но в боксе бьют кулаками в перчатках и по "
            "правилам ударов, а в борьбе пытаются положить соперника на "
            "ковёр.",
        frozenset(("бег", "прыжки")): "Бег и прыжки — оба лёгкая атлетика, "
            "но в беге спортсмен быстро передвигается по дорожке, а в "
            "прыжках старается прыгнуть как можно дальше или выше.",
        frozenset(("лыжи", "коньки")): "Лыжи и коньки — оба зимний спорт "
            "на снегу и льду, но на лыжах скользят по снегу двумя "
            "длинными досками, а на коньках — катаются по ледяной "
            "поверхности лезвиями на ботинках.",
        frozenset(("теннис", "футбол")): "Теннис и футбол — оба спортивные "
            "игры с мячом, но в теннисе мяч отбивают ракеткой через сетку "
            "один на один, а в футболе гоняют мяч ногами команда против "
            "команды.",
        frozenset(("музей", "театр")): "Музей и театр — оба здания, где "
            "проводят время с культурой, но в музее смотрят на картины и "
            "вещи, а в театре смотрят спектакль на сцене.",
        frozenset(("музей", "цирк")): "Музей и цирк — оба места, куда ходят "
            "смотреть, но в музее рассматривают картины и древние вещи, а "
            "в цирке выступают клоуны, акробаты и звери.",
        frozenset(("стадион", "парк")): "Стадион и парк — оба открытые "
            "места для отдыха и спорта, но стадион специально для спортивных "
            "игр с трибунами, а парк — зелёная территория с деревьями и "
            "дорожками для прогулок.",
        frozenset(("дорога", "улица")): "Дорога и улица — оба место, где "
            "ездят машины, но улица — дорога в городе между домами, а "
            "дорога — вообще путь для транспорта, и в городе, и между "
            "городами.",
        frozenset(("улица", "тротуар")): "Улица и тротуар — оба часть "
            "города, где передвигаются, но по улице едут машины, а по "
            "тротуару ходят пешеходы вдоль дороги.",
        frozenset(("проспект", "шоссе")): "Проспект и шоссе — оба широкая "
            "дорога, но проспект — широкая прямая улица в городе, а шоссе "
            "— скоростная трасса между городами.",
        frozenset(("шоссе", "трасса")): "Шоссе и трасса — оба дорога для "
            "быстрого движения, но шоссе — широкая дорога с твёрдым "
            "покрытием, а трасса — дальняя автомобильная дорога между "
            "городами или районами.",
        frozenset(("мост", "тоннель")): "Мост и тоннель — оба сооружают, "
            "чтобы переехать препятствие, но мост строят над водой или "
            "ущельем, а тоннель прокапывают сквозь гору или под землёй.",
        frozenset(("перекрёсток", "светофор")): "Перекрёсток и светофор — "
            "оба помогают движению, но перекрёсток — место, где пересекаются "
            "дороги, а светофор — устройство с огнями, управляющее потоком "
            "машин.",
        frozenset(("кость", "мышц")): "Кость и мышцы — оба части тела, "
            "дающие ему опору, но кость твёрдая и составляет скелет, а "
            "мышцы мягкие и тянут кости в движение.",
        frozenset(("лёгк", "сердце")): "Лёгкие и сердце — оба важные "
            "органы внутри груди, но сердце качает кровь по телу как насос, "
            "а лёгкие наполняются воздухом для дыхания.",
        frozenset(("нерв", "сустав")): "Нерв и сустав — оба части тела, "
            "но нерв передаёт сигналы от мозга по телу, а сустав соединяет "
            "кости и даёт им возможность сгибаться.",
        frozenset(("кровь", "кость")): "Кровь и кость — оба части тела, "
            "но кровь жидкая и разносит по телу кислород, а кость твёрдая "
            "и образует скелет.",
        frozenset(("ладонь", "пятка")): "Ладонь и пятка — оба части тела, "
            "но ладонь — внутренняя сторона руки, а пятка — задняя часть "
            "стопы, на которую опираются при ходьбе.",
        frozenset(("сустав", "кость")): "Сустав и кость — оба части "
            "скелета, но кость твёрдый стержень, а сустав — место, где две "
            "кости соединяются и могут сгибаться.",
        frozenset(("сердце", "кровь")): "Сердце и кровь — оба важны для "
            "жизни и движения, но сердце — мышца-насос, который качает "
            "кровь, а кровь — красная жидкость, бегущая по сосудам.",
        frozenset(("робот", "кукла")): "Робот и кукла — оба игрушки, "
            "похожие на человека, но робот — из металла и пластика, может "
            "двигаться и издавать звуки, а кукла — мягкая или пластмассовая "
            "фигурка, с которой играют.",
        frozenset(("танк", "робот")): "Танк и робот — оба боевые или "
            "игрушечные машины, но танк — бронетехника на гусеницах с "
            "пушкой, а робот — машина, похожая на человека, выполняющая "
            "заданные действия.",
        frozenset(("барабан", "свисток")): "Барабан и свисток — оба "
            "музыкальные инструменты, издающие звук, но в барабан бьют "
            "палочками и он гудит, а в свисток дуют, получая пронзительный "
            "звук.",
        frozenset(("барабан", "труба")): "Барабан и труба — оба "
            "музыкальные инструменты, но в барабан бьют и он гудит, а в "
            "трубу дуют, издавая звонкий медный звук.",
        frozenset(("флейта", "саксофон")): "Флейта и саксофон — оба "
            "духовые инструменты, в которые дуют, но флейта длинная "
            "деревянная с боковым отверстием, а саксофон изогнутый "
            "металлический с клавишами.",
        frozenset(("гитара", "скрипка")): "Гитара и скрипка — оба "
            "струнные инструменты, но на гитаре играют, задевая струны "
            "пальцами или медиатором, а на скрипке водят смычком по струнам.",
        frozenset(("пианино", "скрипка")): "Пианино и скрипка — оба "
            "музыкальные инструменты, но пианино с клавишами, по которым "
            "бьют пальцами, а скрипка — струнная, и на ней играют смычком.",
        frozenset(("шахмат", "шашки")): "Шахматы и шашки — оба настольные "
            "игры на доске, но в шахматах много разных фигур с особыми "
            "ходами, а в шашках все фишки ходят одинаково по клеткам.",
        frozenset(("скрипка", "гитара")): "Скрипка и гитара — оба струнные "
            "инструменты, но скрипка маленькая и на ней играют смычком, а "
            "гитара больше и струны задевают пальцами.",
        frozenset(("город", "посёлок")): "Город и посёлок — оба населённые "
            "места, но город большой, с заводами и многоэтажными домами, а "
            "посёлок меньше — скопление домов, часто за городом.",
        frozenset(("деревня", "село")): "Деревня и село — оба сельские "
            "населённые пункты, но деревня маленькая с несколькими домами, "
            "а село побольше, и там часто есть церковь.",
        frozenset(("столица", "город")): "Столица и город — оба населённые "
            "места, но столица — главный город страны, где жильёт "
            "правительство, а обычный город — любой населённый пункт.",
        frozenset(("страна", "государство")): "Страна и государство — оба "
            "означают территорию с населением, но страна — это земля и "
            "люди, а государство — то же, но с властью, законами и армией.",
        frozenset(("регион", "обла")): "Регион и область — оба части "
            "страны или области, но регион — общее название местности, а "
            "область — административная единица с центром.",
        frozenset(("район", "обла")): "Район и область — оба части "
            "страны, но область — большая административная единица, а "
            "район — более мелкая часть области.",
        frozenset(("народ", "племя")): "Народ и племя — оба группы людей, "
            "но народ — большое объединение с общим языком и культурой, а "
            "племя — небольшая группа с общим предком и обычаями.",
        frozenset(("закон", "конститу")): "Закон и конституция — оба "
            "правила, по которым живёт страна, но конституция — главный "
            "закон страны, а обычный закон — отдельное правило поверх неё.",
        frozenset(("гражданин", "народ")): "Гражданин и народ — оба люди "
            "одной страны, но гражданин — один человек со своими правами, "
            "а народ — все граждане страны вместе.",
        frozenset(("правительство", "государство")): "Правительство и "
            "государство — оба связаны с властью, но государство — сама "
            "страна с территорией и людьми, а правительство — группа людей, "
            "которая управляет государством.",
        frozenset(("фирма", "компан")): "Фирма и компания — оба "
            "организации, которые делают бизнес, это почти одно и то же, "
            "но «компания» звучит крупнее и солиднее, а «фирма» — проще.",
        frozenset(("офис", "фирма")): "Офис и фирма — оба связаны с "
            "работой, но фирма — сама организация, а офис — помещение, где "
            "сотрудники фирмы работают за компьютерами.",
        frozenset(("праздник", "юбил")): "Праздник и юбилей — оба "
            "торжественные события, но праздник — любой радостный день, "
            "например Новый год, а юбилей — круглая дата, например "
            "пятидесятилетие, юбилей человека или организации.",
        frozenset(("дрель", "отвёртка")): "Дрель и отвёртка — оба "
            "инструменты для крепления, но дрель вращается и сверлит "
            "отверстия или закручивает винты, а отвёртка — ручной инструмент "
            "с жалом для завинчивания шурупов.",
        frozenset(("ключ", "гайка")): "Ключ и гайка — оба связаны с "
            "болтовым соединением, но ключ — инструмент, которым закручивают "
            "гайки, а гайка — деталь с резьбой, которую навинчивают на болт.",
        frozenset(("телескоп", "очки")): "Телескоп и очки — оба с линзами, "
            "помогающими видеть, но телескоп смотрит на далёкие звёзды и "
            "планеты, а очки надевают на глаза, чтобы лучше видеть вблизи "
            "или вдаль.",
        frozenset(("зеркало", "экран")): "Зеркало и экран — оба гладкие "
            "поверхности, но зеркало отражает свет и показывает отражение, "
            "а экран светится и показывает видео и картинки.",
        frozenset(("нож", "топор")): "Нож и топор — оба режущие "
            "инструменты, но нож маленький с острым лезвием для резания, "
            "а топор большой с лезвием для рубки дерева.",
        frozenset(("молоток", "дрель")): "Молоток и дрель — оба "
            "инструменты для работы с крепежом, но молотком забивают гвозди "
            "ударами, а дрелью сверлят отверстия и вкручивают винты.",
        frozenset(("пила", "нож")): "Пила и нож — оба инструменты, "
            "которые режут, но пила с зубьями пилит дерево, а нож с острым "
            "гладильным лезвием режет хлеб и другие вещи.",
        frozenset(("курица", "петух")): "Курица и петух — обе домашние "
            "птицы, но курица несёт яйца и квохчет, а петух — самец с "
            "ярким гребнем и хвостом, который будит всех кукареканьем.",
        frozenset(("лебедь", "утка")): "Лебедь и утка — оба водоплавающие "
            "птицы, но лебедь большой, белый и изящный с длинной шеей, а "
            "утка поменьше, с короткой шеей и ведёт себя шумно на воде.",
        frozenset(("скворец", "ласточка")): "Скворец и ласточка — оба "
            "перелётные птицы, но скворец тёмный с блестящими перьями и "
            "поёт, подражая, а ласточка быстрая, с раздвоенным хвостом и "
            "ловит насекомых в полёте.",
        frozenset(("солов", "кукушка")): "Соловей и кукушка — оба птицы, "
            "которые красиво поют, но соловей известен чудесным пением, а "
            "кукушка кричит «ку-ку» и сама не строит гнездо, подкладывая "
            "яйца другим.",
        frozenset(("снегирь", "синица")): "Снегирь и синица — оба "
            "небольшие зимующие птицы, но снегирь с красной грудкой и "
            "прилетает зимой, а синица жёлто-синяя и круглый год на кормушках.",
        frozenset(("аист", "цапля")): "Аист и цапля — оба длинноногие "
            "птицы, но аист белый с чёрными крыльями и живёт на крышах, а "
            "цапля серая и стоит на мелководье, поджидая рыбу.",
        frozenset(("страус", "пингвин")): "Страус и пингвин — оба "
            "нелетающие птицы, но страус живёт в жаркой саванне и быстро "
            "бегает, а пингвин — в холоде и хорошо плавает в ледяной воде.",
        frozenset(("попугай", "канарейка")): "Попугай и канарейка — оба "
            "домашние певчие птицы в клетке, но попугай яркий и умеет "
            "разговаривать, а канарейка маленькая и поёт, но не говорит.",
        frozenset(("павлин", "попугай")): "Павлин и попугай — оба яркие "
            "окрашенные птицы, но павлин большой с огромным распущенным "
            "хвостом, а попугай меньше и умеет имитировать речь человека.",
        frozenset(("вороб", "синица")): "Воробей и синица — оба маленькие "
            "городские или лесные птички, но воробей серо-коричневый и "
            "живёт везде, а синица жёлто-синяя и любит семечки на кормушке.",
        frozenset(("дятел", "сова")): "Дятел и сова — оба лесные птицы, "
            "но дятел днём стучит клювом по дереву, добывая жуков, а сова "
            "ночью охотится на мышей и летает бесшумно.",
        frozenset(("аист", "журавль")): "Аист и журавль — оба крупные "
            "перелётные птицы на длинных ногах, но аист белый и живёт у "
            "жилья, а журавль серый с красным пятном и летает клином.",
        frozenset(("пирожн", "печенье")): "Пирожное и печенье — оба "
            "сладкая выпечка, но пирожное — большое, с кремом и глазурью, "
            "а печенье — маленькое и хрустящее, печётся в печи.",
        frozenset(("пряник", "печенье")): "Пряник и печенье — оба "
            "сладкая выпечка, но пряник мягкий, медовый и с пряностями, а "
            "печенье более сухое и рассыпчатое.",
        frozenset(("кекс", "пирожн")): "Кекс и пирожное — оба сладкая "
            "выпечка, но кекс — целый большой пирог с изюмом, который "
            "режут на куски, а пирожное — маленькое, отдельное, с кремом.",
        frozenset(("булочка", "батон")): "Булочка и батон — оба хлебные "
            "изделия из теста, но батон — длинный нарезной хлеб, а булочка "
            "— маленькая круглая или овальная сдоба, часто сладкая.",
        frozenset(("блин", "пирог")): "Блин и пирог — оба делают из "
            "теста, но блин тонкий и печётся быстро на сковороде, а пирог "
            "круглый с начинкой, который долго выпекают в духовке.",
        frozenset(("кружка", "чашка")): "Кружка и чашка — оба посуда для "
            "питья, но кружка большая с толстой ручкой для чая или какао, а "
            "чашка меньше и тоньше, из неё пьют чай или кофе.",
        frozenset(("бокал", "стакан")): "Бокал и стакан — оба посуда для "
            "питья, но стакан ровный и толстостенный, а бокал на ножке из "
            "тонкого стекла для напитков повеселее.",
        frozenset(("половник", "ложка")): "Половник и ложка — оба посуда с "
            "ручкой, но ложка маленькая, ей едят из тарелки, а половник "
            "большой, им разливают суп из кастрюли по тарелкам.",
        frozenset(("рубль", "евро")): "Рубль и евро — оба деньги, но рубль "
            "— валюта России, а евро — валюта многих стран Европы.",
        frozenset(("рубль", "доллар")): "Рубль и доллар — оба деньги, но "
            "рубль — валюта России, а доллар — валюта США.",
        frozenset(("евро", "доллар")): "Евро и доллар — оба важные "
            "мировые деньги, но евро используют в странах Европы, а доллар "
            "— в Америке и как международная валюта.",
        frozenset(("ведро", "кастрюля")): "Ведро и кастрюля — оба "
            "ёмкости, но кастрюля — кухонная посуда, в ней варят суп, а "
            "ведро с ручкой используют, чтобы носить воду или мусор.",
        frozenset(("урок", "перемена")): "Урок и перемена — оба части "
            "школьного дня, но на уроке учитель объясняет и ученики слушают, "
            "а на перемене школьники отдыхают и играют между уроками.",
        frozenset(("урок", "каникул")): "Урок и каникулы — оба часть "
            "учебного года, но урок — время занятий в школе, а каникулы — "
            "длинный отдых между учебными четвертями.",
        frozenset(("перемена", "каникул")): "Перемена и каникулы — оба "
            "отдых, но перемена — короткий перерыв между уроками, а "
            "каникулы — длинный отдых в несколько дней или недель.",
        frozenset(("экзамен", "урок")): "Экзамен и урок — оба школьное "
            "занятие, но на уроке учат новое, а экзамен проверяет, что "
            "выучили, по вопросам и оценкам.",
        frozenset(("будни", "выходн")): "Будни и выходные — оба дни "
            "недели, но в будни ходят на работу или учёбу, а в выходные "
            "отдыхают и не работают.",
        frozenset(("будни", "каникул")): "Будни и каникулы — оба время "
            "учёбы, но в будни проходят уроки в школе, а на каникулах "
            "учиться не надо и можно отдыхать.",
        frozenset(("выходн", "праздник")): "Выходной и праздник — оба день, "
            "когда не работают, но выходной — обычный отдых в конце недели, "
            "а праздник — торжественный день, например Новый год.",
        frozenset(("класс", "группа")): "Класс и группа — оба коллектив "
            "учеников, но класс — школьники одного года обучения в классе, "
            "а группа — набор людей, занимающихся вместе, например в кружке.",
        frozenset(("ученик", "школьник")): "Ученик и школьник — оба "
            "человек, который учится, но школьник — ученик именно школы, "
            "а ученик — более общее слово и для школы, и для курсов.",
        frozenset(("брат", "сестра")): "Брат и сестра — оба родные дети "
            "одних родителей, но брат — мальчик, а сестра — девочка.",
        frozenset(("дедушка", "бабушка")): "Дедушка и бабушка — оба "
            "родители отца или матери, но дедушка — мужчина, а бабушка — "
            "женщина.",
        frozenset(("сын", "дочь")): "Сын и дочь — оба дети родителей, но "
            "сын — мальчик, а дочь — девочка.",
        frozenset(("каша", "гречка")): "Каша и гречка — оба варёные "
            "блюда из крупы, но каша — общее название любой сварной крупы, "
            "а гречка — конкретная крупа из гречихи, коричневая.",
        frozenset(("каша", "овсянка")): "Каша и овсянка — оба горячие "
            "блюда на завтрак, но каша — общее название, а овсянка — каша "
            "из овсяных хлопьев, полезная для здоровья.",
        frozenset(("суп", "уха")): "Суп и уха — оба жидкие горячие блюда, "
            "но суп — общее название, а уха — суп из рыбы, сваренный из "
            "свежей рыбы и овощей.",
        frozenset(("отбивн", "котлета")): "Отбивная и котлета — оба "
            "мясные блюда, но отбивная — кусок мяса, который отбивают и "
            "жарят целиком, а котлета — рубленое мясо, слепленное в "
            "плоскую лепёшку и обжаренное.",
        frozenset(("колбаса", "ветчина")): "Колбаса и ветчина — оба "
            "продукты из мяса, готовые к еде, но колбаса — измельчённое "
            "мясо в оболочке, а ветчина — цельный кусок запечённого или "
            "копчёного мяса.",
        frozenset(("гречка", "овсянка")): "Гречка и овсянка — оба "
            "полезные каши из круп, но гречка коричневая из гречихи, а "
            "овсянка из овсяных хлопьев бежевая.",
        frozenset(("борщ", "уха")): "Борщ и уха — оба супы, но борщ — "
            "красный суп со свеклой и капустой, а уха — прозрачный суп "
            "из рыбы.",
        frozenset(("липа", "клён")): "Липа и клён — оба лиственные "
            "деревья, но у липы сердцевидные листья и пахучие цветки, а у "
            "клёна листья резные, лапчатые, и осенью они краснеют.",
        frozenset(("тополь", "ива")): "Тополь и ива — оба быстрорастущие "
            "деревья у воды, но тополь высокий с трепещущими листьями, а "
            "ива с гибкими ветвями, опущенными вниз.",
        frozenset(("ель", "лиственница")): "Ель и лиственница — оба "
            "хвойные деревья, но у ели иголки остаются круглый год, а "
            "лиственница осенью сбрасывает мягкую хвою.",
        frozenset(("дуб", "ясень")): "Дуб и ясень — оба могучие лиственные "
            "деревья, но дуб с широкой кроной и желудями, а ясень с "
            "перистыми листьями и высокий, прямой.",
        frozenset(("яблоня", "персик")): "Яблоня и персик — оба плодовые "
            "деревья, но яблоня даёт твёрдые яблоки и растёт в холоде, а "
            "персик — сочные пушистые персики и любит тепло.",
        frozenset(("яблоня", "вишня")): "Яблоня и вишня — оба плодовые "
            "деревья, но яблоня даёт крупные яблоки, а вишня — мелкие "
            "красные вишенки с косточкой.",
        frozenset(("сосна", "берёза")): "Сосна и берёза — оба деревья, "
            "но сосна — хвойное с длинными иголками, а берёза — лиственное "
            "с белым стволом и зелёными листьями.",
        frozenset(("яблоня", "яблоко")): "Яблоня и яблоко — это дерево и "
            "его плод, но яблоня — дерево, растущее в саду, а яблоко — "
            "вкусный плод, который на нём вырастает.",
        frozenset(("клён", "ясень")): "Клён и ясень — оба лиственные "
            "деревья с перистыми листьями, но у клёна лист лапчатый и "
            "осенью красный, а у ясеня лист состоит из многих мелких "
            "листочков.",
        frozenset(("дуб", "клён")): "Дуб и клён — оба большие лиственные "
            "деревья, но дуб могучий с плотной корой и желудями, а клён — "
            "стройный с резными листьями, краснеющими осенью."
    }
    return table.get(key) or table.get(raw_key)


def _relation_answer(pair, query):
    """Связный ответ для пары понятий (прямая связь, определений, вывод пути,
    общие соседи). Один return: str|None."""
    a, b = pair
    if not a or not b:
        return None
    out = None
    # 0) готовая пара — содержательное сравнение вместо двух определений
    cp = _compare_known_pair((a, b))
    if cp:
        return cp
    # 1) сравнение определений из словаря понятий — самое осмысленное
    #    («чем отличается стек от очереди» → оба определены, показываем суть)
    try:
        from algos.module_knowledge import fk
        def_ab = _lookup_concept(fk, a)
        def_ab = {k.lower(): v for k, v in def_ab.items()}
        def_ba = _lookup_concept(fk, b)
        def_ba = {k.lower(): v for k, v in def_ba.items()}
    except Exception:
        def_ab, def_ba = {}, {}
    if def_ab and def_ba:
        lines = []
        wa = def_ab.get("what") or ""
        wb = def_ba.get("what") or ""
        if wa:
            lines.append(f"{_display_concept(a).capitalize()} — это {wa}.")
        if wb:
            lines.append(f"{_display_concept(b).capitalize()} — это {wb}.")
        if lines:
            out = " ".join(lines)
            return out
    # 1) прямая связь через граф (осмысленный предикат)
    rels = [r for r in kg.relation(a, b) if not _is_noisy_predicate(r[0])]
    if rels:
        phr = ", ".join(f"«{a}» {p} «{b}»" for p, _w in rels[:3])
        if len(rels) > 3:
            phr += " и ещё связями"
        out = f"{a.capitalize()} и {b} связаны: {phr}."
        return out
    # 2) путь через граф (только осмысленные шаги)
    path = kg.path(a, b)
    if path:
        preds = [step[1] for step in path if len(step) > 1]
        chain = [line[0] for line in path if line[0] and len(line[0]) > 2]
        if any(p and not _is_noisy_predicate(p) for p in preds) and len(chain) >= 2:
            # убираем падежные дубликаты из цепочки («обучение→память→памятью»)
            seen = []
            for c in chain:
                if not any(_relation_stem2(c) == _relation_stem2(s) for s in seen):
                    seen.append(c)
            out = "Выводится: " + " → ".join(seen) + "."
            return out
    # 3) общие соседи (сходство окрестностей) — только осмысленные, не однобуквенные
    shared = [n for n in kg.mutual_neighbors(a, b)
              if len(n) > 2
              and n.split()[0] not in _RELATION_JUNK
              and not _is_noisy_node(n)]
    if shared:
        top = shared[:3]
        names = ", ".join(_display_concept(n) for n in top)
        out = f"У {a.capitalize()} и {b.capitalize()} есть общие связи: {names}."
        return out
    return out


def _stem_match(a, b):
    """Совпадают ли понятия по стему (равный стем или длинный общий префикс
    ≥4, покрывающий русские падежные расхождения: «список»/«списком»,
    «массив»/«массивом»). Один return: bool."""
    sa = _relation_stem2(a)
    sb = _relation_stem2(b)
    if not sa or not sb:
        return False
    if sa == sb:
        return True
    n = min(len(sa), len(sb))
    if n < 4:
        return False
    i = 0
    while i < n and sa[i] == sb[i]:
        i += 1
    return i >= 4


def _lookup_concept(fk, name):
    """Ищет понятие в базе по имени/стему (префиксный матч по стему),
    возвращая его данные. Предпочитает понятие, чьё первое слово по стему
    совпадает точнее и короче (общая тема раньше специфичной: «список»
    вместо «список перестановок»). Один return: dict."""
    w = (name or "").strip().lower()
    if not w:
        return {}
    best = {}
    best_score = -1
    for key, info in (fk._by_name or {}).items():
        if not isinstance(info, dict):
            continue
        topic = str(info.get("topic", "") or "").lower()
        first = topic.split()[0] if topic else ""
        if topic == w:
            return info
        if not first:
            continue
        if _stem_match(first, w) or any(_stem_match(str(t), w) for t in (info.get("tags") or [])):
            # точное совпадение первого слова по стему ценим выше; при равном
            # совпадении — короче тема (общее понятие: «алгоритм» перед
            # «алгоритм дейкстры», «список» перед «список перестановок»)
            score = 100 if _stem_match(first, w) else 50
            # лёгкий штраф за длину темы: специфичные фразы оцениваются ниже
            score -= len(topic.split())
            score -= (first == w) * 0
            if score > best_score:
                best_score = score
                best = info
    return best


def _how_works_topic(query):
    """Извлекает (подпись, текст) из вопроса «как работает/устроен X».
    Подпись — канонический ключ из _HOW_WORKS, текст — его объяснение.
    Один return: tuple[str, str]|None."""
    q = (query or "").lower()
    if not any(m in q for m in ("как работает", "как устроен", "как устроена",
                                "как устроено", "так работает", "как действует",
                                "как летает", "как дышит", "как плывёт",
                                "как плавает", "как ползает", "как ходит",
                                "как прыгает", "как делает", "как появляется",
                                "как образуется", "как возникает", "как растёт")):
        if not q.startswith("как "):
            return None
    cands = _relation_candidates(query)
    for c in cands:
        for k in _HOW_WORKS:
            kw = k.split()[0]
            if c == kw or _stem_match(kw, c):
                return (k, _HOW_WORKS[k])
    return None


def try_relation(query):
    """Связный ответ на вопрос о связи/сравнении двух понятий по графу,
    вместо сырого «тройственного рассуждения». Один return: str|None."""
    hw = _how_works_topic(query)
    if hw:
        label, text = hw
        return f"{label.capitalize()}: {text}"
    if not _is_relation_query(query):
        return None
    cands = _relation_candidates(query)
    pair = ()
    # для «разница/отличие» исключаем служебный второй член маркера «между … и …»
    if len(cands) >= 2:
        markers = _relation_markers(query)
        keep = [c for c in cands if c.split()[0] not in markers]
        if len(keep) >= 2:
            pair = (keep[0], keep[1])
        else:
            pair = (cands[0], cands[1])
    elif len(cands) == 1:
        pair = (cands[0], None)
    ans = None
    if pair:
        ans = _relation_answer(pair, query)
    # если извлечённая пара дала только общие дефиниции (сравнение-содержание
    # уточняет), а среди кандидатов есть готовая пара из _compare_known_pair —
    # предпочесть содержательное сравнение с конкретными различиями
    if len(cands) >= 2:
        found_pair = None
        for i in range(len(cands)):
            for j in range(i + 1, len(cands)):
                if _compare_known_pair((cands[i], cands[j])):
                    found_pair = (cands[i], cands[j])
                    break
            if found_pair:
                break
        if found_pair:
            ans = _compare_known_pair(found_pair)
    if not ans and len(cands) == 1:
        # одного понятия хватает для ассоциаций: что рядом с X
        from algos.module_knowledge import try_definition
        ans = try_definition("что такое " + cands[0])
    return ans


# Причинно-следственные объяснения для вопросов «почему/зачем»:
# {тема: (причина почему, польза зачем)} — осмысленный ответ вместо
# случайного фрагмента базы или сырого вывода графа.
_WHY_REASONS = {
    "граф": ("граф — это универсальная модель связей: им описывают дороги, сети, "
             "социальные связи и зависимости, поэтому почти любая задача о связях "
             "сводится к алгоритмам на графах",
             "с его помощью решают поиск пути, обход, поиск кратчайших расстояний и "
             "декомпозицию систем на компоненты"),
    "алгоритм": ("алгоритм — это точный многократный способ решения задачи без "
                 "перебирания всех вариантов вслепую",
                 "он превращает хаос в предсказуемый шаг за шагом процесс, экономит "
                 "время и память на больших данных"),
    "сортировка": ("без упорядочивания найти элемент в неотсортированном списке — это "
                   "полный перебор, а отсортированный список позволяет искать быстро",
                   "сортировка нужна для поиска, слияния, группировки и вывода данных "
                   "в понятном порядке"),
    "память": ("обучение невозможно без сохранения: если не запоминать, каждый урок "
               "начинается с нуля",
               "память накапливает опыт, из которого строятся навыки и знания"),
    "рекурсия": ("многие задачи естественно делятся на такие же, но меньшие — "
                 "тогда одно и то же правило применяется к себе",
                 "рекурсия делает программу короткой и понятной для обхода деревьев, "
                 "поиска и разбиения задач"),
    "база данных": ("чем больше данных, тем нужнее порядок: без структуры информацию "
                    "невозможно быстро находить и согласовывать",
                    "базы данных дают надёжное хранение, быстрый поиск и согласованный "
                    "доступ многих пользователей"),
    "бинарный поиск": ("отсортированный массив можно делить пополам, отбрасывая "
                       "половину на каждом шаге",
                       "это даёт логарифмическую скорость — находить элемент среди "
                       "миллионов за считанные шаги"),
    "сон": ("во сне тело восстанавливает силы, а мозг упорядочивает впечатления "
            "и закрепляет память",
            "регулярный сон нужен для здоровья, учёбы и хорошего самочувствия"),
    "нейросеть": ("закономерности в данных слишком сложны, чтобы записать их списком "
                  "правил, но их можно выучить по примерам",
                  "нейросети распознают образы, понимают речь и прогнозируют то, что "
                  "трудно формализовать вручную"),
    "интернет": ("сеть соединяет компьютеры по всему миру в единую среду обмена "
                 "информацией",
                 "интернет даёт мгновенный доступ к информации, общению и сервисам "
                 "из любого места"),
    "данные": ("сами по себе разрозненные факты бесполезны, пока они не организованы "
               "и не хранятся упорядоченно",
               "данные нужны, чтобы принимать решения: анализировать, прогнозировать "
               "и извлекать знания"),
    "читать": ("чтение переносит накопленный опыт и знания других людей прямо в голову "
               "без собственных ошибок",
               "оно развивает речь, воображение, словарный запас и способность "
               "сосредоточиваться"),
    "чтение": ("книга хранит мысли и знания автора и передаёт их читателю через текст",
               "чтение расширяет кругозор, тренирует память и внимание и развивает "
               "фантазию"),
    "книга": ("книга — носитель готового знания: в ней опыт многих людей собран и "
              "упорядочен",
              "по книгам учатся, погружаются в истории и развивают мышление"),
    "спорт": ("движение разгоняет кровь, тренирует сердце и мышцы и укрепляет тело",
              "занятия спортом повышают выносливость, настроение и здоровье"),
    "физкультура": ("регулярное движение нужно телу, как топливо машине: без него "
                    "мышцы и сердце слабеют",
                    "физкультура поддерживает форму, осанку и бодрость"),
    "вода": ("организм состоит в основном из воды, и без неё клетки не могут работать",
             "вода нужна для пищеварения, терморегуляции и вывода вредных веществ"),
    "пить": ("тело постоянно теряет влагу, и её нужно восполнять",
             "достаточное питьё поддерживает энергию, ясность ума и здоровье"),
    "учёба": ("знания не появляются сами — их накапливают, учась и тренируясь",
              "учёба развивает ум, даёт навыки и открывает возможности в будущем"),
    "учеба": ("новые навыки приобретаются только через обучение и практику",
              "учёба помогает понимать мир и добиваться целей"),
    "дружба": ("человеку нужны близкие люди, чтобы делиться радостью и поддержкой",
               "дружба даёт опору, снижает тревогу и делает жизнь полнее"),
    "отдых": ("без пауз тело и мозг устают, и работа становится хуже",
              "отдых восстанавливает силы, помогает думать ясно и жить бодро"),
    "завтрак": ("после ночного сна запасы энергии пусты, и телу нужна пища",
                "завтрак даёт силы на день и помогает лучше учиться и работать"),
    "прогулка": ("свежий воздух насыщает кровь кислородом и даёт нагрузку мышцам",
                 "прогулка поднимает настроение, улучшает сон и помогает думать"),
    "гигиена": ("на коже и руках скапливаются микробы, которые могут вызвать болезни",
                "гигиена защищает от инфекций и помогает чувствовать себя чисто"),
    "мыть руки": ("на руках скапливаются микробы, которые попадают в рот и глаза",
                  "мытьё рук с мылом смывает большинство вредных микробов"),
    "чистить зубы": ("на зубах остаётся налёт, который разрушает эмаль и вызывает кариес",
                     "чистка удаляет налёт и микробы и защищает зубы и дёсны"),
    "свет": ("растениям и фотосинтезу нужен свет, а людям — чтобы видеть мир",
             "свет даёт тепло, энергию и помогает ориентироваться"),
    "тепло": ("при комфортной температуре организму проще поддерживать равновесие",
              "тепло делает жизнь удобной, а в холодной среде тело тратит силы на обогрев"),
    "математика": ("математика даёт точный язык для счёта, мер, форм и закономерностей",
                   "она нужна в науке, технике и любом деле, где считают и измеряют"),
    "терпение": ("многие цели достигаются не сразу, а постепенно, шаг за шагом",
                 "терпение помогает доводить начатое до конца и не бросать при трудностях"),
    "закаливание": ("постепенное привыкание к холоду тренирует защитные силы организма",
                    "закаливание делает тело устойчивее к простудам"),
    "учиться": ("знания не появляются сами — их накапливают, учась и тренируясь",
                "учёба развивает ум, даёт навыки и открывает возможности в будущем"),
    "гулять": ("свежий воздух насыщает кровь кислородом и даёт нагрузку мышцам",
               "прогулка поднимает настроение, улучшает сон и помогает думать"),
    "заниматься": ("систематические занятия развивают навык и закрепляют результат",
                   "практика превращает способность в устойчивое умение"),
    "умываться": ("за ночь на коже накапливаются жир и пыль, которые забивают поры",
                  "умывание очищает кожу и помогает сохранять её здоровой"),
    "мыться": ("на коже скапливаются пот, грязь и микробы, вызывающие неприятный запах",
               "мытьё смывает загрязнения, освежает и защищает от болезней"),
    "сладкое": ("избыток сахара даёт быстрый, но краткий подъём сил и вредит зубам и фигуре",
                "сладкое лучше есть умеренно, чтобы не перегружать поджелудочную и не "
                "портит зубы"),
    "спать": ("во сне мозг и тело восстанавливаются и закрепляют выученное",
              "достаточный сон нужен для здоровья, роста и хорошего самочувствия"),
    "дождь": ("капли воды в облаках соединяются и становятся тяжёлыми, и они "
              "падают на землю дождём",
              "дождь наполняет реки и озёра и нужен растениям для роста"),
    "ветер": ("воздух в одном месте нагревается и поднимается, а холодный "
              "воздух с других мест устремляется на его место — так дует ветер",
              "ветер разносит облака, приносит дождь и помогает работе мельниц"),
    "ночь": ("ночью Земля повёрнута от солнца, поэтому на её стороне темно",
             "ночь нужна людям и животным для отдыха и сна"),
"снег": ("каждая снежинка сделана из мелких кристалликов льда, которые "
              "отражают и рассеивают свет почти целиком",
              "снег укрывает землю, и весной из растаявшего снега земля получает влагу"),
    "небо": ("солнечный свет рассеивается в воздухе, и синий цвет "
              "рассеивается сильнее остальных",
              "понимать, почему небо голубое, помогает изучать свет и природу"),
    "листья": ("в листьях есть хлорофилл — вещество, которое улавливает свет "
               "солнца и отражает зелёный цвет",
               "листья вырабатывают питание для растения на свету"),
    "кошка": ("кошки мяукают, чтобы общаться с людьми и обращать на себя внимание",
              "понимание кошки помогает ухаживать за ней и жить с ней дружно"),
    "вода мокрая": ("молекулы воды легко притягиваются к другим поверхностям "
              "и прилипают к ним тонким слоем",
              "это и есть свойство воды прилипать и смачивать — оно помогает "
              "мыть и увлажнять"),
    "солнце светит": ("внутри солнца идут термоядерные реакции, которые "
              "выделяют огромную энергию в виде света и тепла",
              "свет и тепло солнца дают жизнь растениям, животным и людям"),
    "зима": ("зимой земная ось наклонена так, что солнце греет слабее и день "
              "короткий, поэтому становится холодно",
              "зимний отдых и снег нужны природе, чтобы переждать холодное время"),
    "лето": ("летом земная ось наклонена к солнцу, солнце стоит высоко и греет "
              "сильнее, а день длинный, поэтому тепло и жарко",
              "летнее тепло и свет нужны растениям для роста и созревания плодов"),
    "огонь": ("при горении выделяется много тепла и света из топлива",
              "тепло огня греет, готовит еду и освещает"),
    "лёд": ("его поверхность под давлением подтаивает и покрывается тонкой "
              "плёнкой воды",
              "свойство льда скользить нужно при катании на коньках и санках"),
    "трава": ("в ней есть хлорофилл, который улавливает "
              "свет и отражает зелёный цвет",
              "трава вырабатывает себе питание на свету и кормит животных"),
    "море": ("реки веками приносят в море соль "
              "из горных пород, а вода испаряется, оставляя соль",
              "солёная вода помогает живому в море держаться на плаву и сохраняет "
              "его биологическое равновесие"),
    "грязные руки": ("на грязных руках живут микробы, которые могут попасть в рот "
              "вместе с едой и вызвать болезнь",
              "мытьё рук перед едой защищает от заражения и болезней"),
    "грязными руками": ("на грязных руках живут микробы, которые могут попасть "
              "в рот вместе с едой и вызвать болезнь",
              "мытьё рук перед едой защищает от заражения и болезней"),
    "спасибо": ("говорить «спасибо» нужно, чтобы благодарить за доброе дело и "
              "показывать уважение и внимание к другому человеку",
              "благодарность укрепляет дружбу и добрые отношения между людьми"),
    "доброта": ("быть добрым и помогать другим нужно, потому что людям приятна "
              "забота и помощь, и они отвечают тем же",
              "доброта делает жизнь вокруг радостнее и создаёт дружелюбное "
              "сообщество"),
    "небо голубое": ("небо кажется голубым, потому что лучи солнца рассеиваются "
                    "в воздухе, и синий свет рассеивается сильнее всех",
                    "голубое небо радует глаз и помогает узнавать погоду днём"),
    "небо синее": ("небо кажется синим, потому что солнечный свет рассеивается "
                  "в атмосфере, и синие лучи разлетаются сильнее остальных",
                  "синее небо подсказывает, что день ясный"),
    "трава зелёная": ("трава зелёная, потому что в листьях есть хлорофилл, "
                      "который ловит солнечный свет для питания растения",
                      "зелёный цвет помогает растению расти на солнце"),
    "листья зелёные": ("листья зелёные, потому что в них есть хлорофилл, "
                      "который использует свет для питания, а затем осенью "
                      "пигмент распадается и листья желтеют",
                      "зелёный цвет даёт растению энергию для роста"),
    "соль солёная": ("соль имеет солёный вкус, потому что в ней есть минералы "
                     "натрия и хлора",
                     "соль придаёт еде вкус и помогает нашему телу работать"),
    "сахар сладкий": ("сахар сладкий, потому что в нём есть частицы, которые "
                      "распознаются языком как сладкие",
                      "сладкий вкус даёт организму быструю энергию"),
    "лимон кислый": ("лимон кислый, потому что в нём много лимонной кислоты, "
                     "которая действует на язык",
                     "кислый вкус освежает и помогает пищеварению"),
    "воздух невидимый": ("мы не видим воздух, потому что он прозрачный и не "
                         "отражает свет",
                         "хотя воздуха не видно, без него нельзя дышать"),
    "мыло пенится": ("мыло пенится, потому что его частицы обволакивают пузырьки "
                     "воздуха и покрывают грязь",
                     "пена помогает смывать грязь с рук и вещей"),
    "мороженое холодное": ("мороженое холодное, потому что его замораживают в "
                           "специальном аппарате и держат при низкой температуре",
                           "холодное мороженое освежает в жаркий день"),
    "лёд скользкий": ("лёд скользкий, потому что его верхний слой тает и "
                      "образует тонкую плёнку воды, по которой легко скользить",
                      "по льду катаются на коньках, но нужно быть осторожным"),
    "холодно зимой": ("зимой холодно, потому что солнце поднимается низко над "
                      "горизонтом и почти не греет, а дни становятся короткими",
                      "холод зимой заставляет природу отдыхать, а людям нужно "
                      "тепло одеваться"),
    "жарко летом": ("летом жарко, потому что солнце поднимается высоко и его "
                    "лучи падают прямо и сильно нагревают землю, а дни длинные",
                    "тепло лета помогает растениям и животным расти и плодоносить"),
    "наступает ночь": ("ночь наступает, потому что Земля медленно вращается, и "
                       "та часть, где мы живём, отворачивается от солнца",
                       "ночью небо темнеет, и свет звёзд и луны хорошо виден"),
    "наступает день": ("день наступает, потому что Земля вращается вокруг своей "
                       "оси, и наша сторона снова поворачивается к солнцу",
                       "днём светло и тепло, и можно видеть всё вокруг"),
    "дует ветер": ("ветер дует, потому что солнечный свет нагревает воздух "
                   "неодинаково: тёплый воздух поднимается, а холодный двигается "
                   "на его место",
                   "ветер разносит облака, семена растений и помогает проветривать"),
    "появляются облака": ("облака появляются, когда тёплый воздух с водяным "
                          "паром поднимается вверх и охлаждается, а пар "
                          "превращается в крошечные капельки воды",
                          "из облаков идёт дождь и снег, которые нужны растениям"),
    "видна радуга": ("радуга видна, когда солнечный свет проходит сквозь "
                     "капельки дождя и разбивается на цветные лучи",
                     "радуга красит небо и радует глаз после дождя"),
    "гремит гром": ("гром гремит, потому что молния сильно нагревает воздух, "
                    "и он быстро расширяется, создавая грохот",
                    "гром и молния предупреждают о сильном дожде"),
    "нужна вода": ("вода нужна, потому что из неё состоит большая часть нашего "
                   "тела, она помогает пищеварению и работе органов",
                   "без воды человек и все живые существа не могут жить"),
    "каша полезна": ("каша полезна, потому что крупа даёт организму энергию, "
                     "витамины и силы на весь день",
                     "каша на завтрак помогает хорошо учиться и играть"),
    "глаза видят": ("глаза видят, потому что они ловят лучи света и посылают "
                    "картинку в мозг, который её понимает",
                    "зрение помогает нам замечать мир, учиться и не натыкаться "
                    "на препятствия"),
    "уши слышат": ("уши слышат, потому что они ловят звуковые волны и "
                   "превращают их в сигналы для мозга",
                   "слух помогает общаться с людьми и слышать опасность"),
    "помогать": ("помогать другим нужно, потому что каждый сам может "
                 "оказаться в трудной ситуации и будет рад поддержке",
                 "помощь другим делает мир добрее и дружелюбнее, и тебе тоже "
                 "помогут, когда понадобится"),
    "извиняться": ("извиняться нужно, когда обидел кого-то, потому что это "
                   "показывает, что ты понял свою ошибку",
                   "извинение мирит людей и помогает снова дружить"),
    "говорить правду": ("говорить правду нужно, потому что правда делает "
                        "отношения честными, а обман рано или поздно "
                        "раскрывается",
                        "правда помогает доверять друг другу и не запутывать "
                        "ситуацию"),
    "нельзя драться": ("драться нельзя, потому что драка причиняет боль и "
                       "не решает спор, а только делает его хуже",
                       "любые разногласия можно решить словами и миром"),
    "беречь природу": ("беречь природу нужно, потому что лес, вода и воздух "
                       "дают нам всё необходимое для жизни",
                       "забота о природе сохраняет её чистой для нас и для "
                       "будущих поколений"),
    "идёт дождь": ("дождь идёт, потому что капли воды в облаках тяжелеют и "
                   "падают вниз на землю",
                   "дождь наполняет реки и поливает растения, чтобы они росли"),
    "падает снег": ("снег падает, потому что в холодном облаке водяной пар "
                    "замерзает и превращается в снежинки, которые опускаются "
                    "на землю",
                    "снег укрывает землю тёплым одеялом и даёт влагу весной"),
    "цветы пахнут": ("цветы пахнут, потому что выделяют пахучие вещества, "
                     "чтобы привлечь пчёл и бабочек для опыления",
                     "приятный запах цветов радует нас и помогает растениям "
                     "давать плоды"),
    "море солёное": ("море солёное, потому что реки веками приносят в него "
                     "соль из горных пород, а вода испаряется, оставляя соль",
                     "солёная вода помогает морским животным и не замерзает "
                     "так быстро"),
    "трава растёт": ("трава растёт, потому что корни берут из земли воду и "
                     "питательные вещества, а листья ловят солнечный свет",
                     "трава зеленеет весной и летом, кормит животных и "
                     "украшает луга"),
    "поют птицы": ("птицы поют, потому что так они общаются, зовут друг "
                   "друга и метят свою территорию",
                   "птичье пение радует нас и оживляет лес и сад"),
    "кошка мурлычет": ("кошка мурлычет, когда ей хорошо и спокойно, этот "
                       "звук она издаёт горлом при выдохе",
                       "мурлыканье успокаивает и кошку, и человека рядом с ней"),
    "собака лает": ("собака лает, чтобы предупредить о чём-то, позвать "
                    "хозяина или отпугнуть чужих",
                    "лай помогает собаке защищать дом и сообщать о гостях"),
    "пчела жужжит": ("пчела жужжит, потому что очень быстро машет "
                     "маленькими крылышками, и воздух от этого гудит",
                     "жужжание слышно, когда пчела летит собирать нектар"),
}


_HOW_WORKS = {
    "компилятор": ("компилятор работает так: читает исходный код, проверяет его, "
                   "переводит в машинные команды и собирает исполняемый файл, "
                   "поэтому программа потом работает без переводчика"),
    "браузер": ("браузер работает так: по адресу запрашивает страницу у сервера, "
                "получает HTML и файлы, строит из них страницу и рисует её на экране"),
    "операционная": ("операционная система работает как диспетчер: распределяет "
                     "процессор и память между программами, хранит файлы и не даёт "
                     "программам мешать друг другу"),
    "сердце": ("сердце работает как насос: оно ритмично сжимается и выталкивает "
               "кровь по сосудам ко всем органам, а мышца сердца отдыхает между "
               "ударами"),
    "мозг": ("мозг работает как командный центр: он получает сигналы от органов "
             "чувств, обрабатывает их и отдаёт команды телу, а спит и "
             "восстанавливается во время сна"),
    "магнит": ("магнит работает за счёт особого расположения мельчайших частиц "
               "металла внутри: они выстроены в одном направлении и притягивают "
               "железо и другие магниты"),
    "лампа": ("лампа работает потому, что по нити внутри проходит ток, она "
              "накаляется и начинает светить, а светодиодные лампы светят с "
              "помощью полупроводников"),
    "компьютер": ("компьютер работает так: процессор выполняет команды, память "
                  "хранит данные, а жёсткий диск и система позволяют запускать "
                  "программы и обрабатывать информацию"),
    "интернет": ("интернет работает через сеть соединённых компьютеров: данные "
                 "разбиваются на пакеты и передаются по кабелям и беспроводным "
                 "связям к другим компьютерам по всему миру"),
    "двигатель": ("двигатель превращает топливо или электричество в движение: "
                  "внутри поршни или мотор вращают колёса и заставляют машину "
                  "ехать"),
    "лампочка": ("лампочка работает потому, что по нити или полупроводнику внутри "
                 "проходит ток: нить накаляется и светит, а светодиод светит без "
                 "перегрева"),
    "чай": ("чайник работает так: нагреватель внутри пропускает ток, греет воду "
            "до кипения, и пар выключает его, когда вода закипает"),
    "машина": ("машина работает от двигателя: топливо или электричество "
               "превращаются в крутящее усилие, которое через колёса приводит "
               "автомобиль в движение"),
    "самолёт": ("самолёт летит так: двигатели создают тягу вперёд, а крылья "
                "создают подъёмную силу, которая держит самолёт в воздухе"),
    "автомобиль": ("автомобиль работает от двигателя, который превращает "
                   "топливо в движение: поршни вращают колёса, а руль и тормоза "
                   "управляют ездой"),
    "велосипед": ("велосипед едет так: человек крутит педали, цепь передаёт "
                  "усилие на заднее колесо, и велосипед катится вперёд"),
    "часы": "часы работают по механизму: пружина или батарейка заводят механизм, а стрелки двигаются по циферблату ровными шагами, отсчитывая время",
    "телевизор": "телевизор показывает картинку так: приёмник ловит сигнал, внутри экран зажигает цветные точки, и из них складывается изображение и звук",
    "телефон": "телефон работает так: голос превращается в электрический сигнал, сигнал передаётся по сети, а на другом конце снова становится голосом",
    "холодильник": "холодильник охлаждает так: специальная жидкость отбирает тепло у продуктов и отдаёт его наружу, поэтому внутри становится холодно",
    "стиральная машина": "стиральная машина стирает так: барабан крутится, смешивает бельё с водой и мылом, а отжим выжимает грязную воду",
    "пылесос": "пылесос убирает так: вентилятор внутри создаёт сильный поток воздуха, который втягивает пыль и мусор в мешок",
    "микроволновка": "микроволновка греет так: внутри излучаются микроволны, которые заставляют молекулы воды в еде быстро дрожать и нагреваться",
    "лифт": "лифт поднимает так: трос тянет кабину вверх по шахте, а противовес с другой стороны помогает двигаться плавно",
    "светофор": "светофор работает так: он по очереди зажигает красный, жёлтый и зелёный свет, подсказывая, когда можно идти, а когда нужно стоять",
    "зеркало": "зеркало работает так: гладкая блестящая поверхность отражает лучи света обратно, и мы видим своё отражение",
    "термометр": "термометр измеряет так: от тепла жидкость или столбик внутри расширяется и поднимается по шкале, показывая температуру",
    "утюг": "утюг работает так: нагревательный элемент внутри раскаляется, и горячая подошва разглаживает складки на ткани",
    "фен": "фен сушит так: внутри работает мотор с вентилятором, а нагреватель греет воздух, который быстро высушивает волосы",
    "блендер": "блендер работает так: острые ножи на дне быстро вращаются и перемалывают продукты в однородную массу",
    "ключ": "ключ работает так: его зубчики толкают штифты внутри замка, и когда все они встают ровно, замок поворачивается и открывается",
    "замок": "замок работает так: внутри есть штифты, которые держат механизм, и только правильный ключ поднимает все штифты на нужную высоту",
    "очки": "очки работают так: специальные стёкла преломляют лучи света, чтобы они собирались точно на сетчатке и картинка была чёткой",
    "птица": "птица летает так: сильно взмахивает крыльями, которые создают поток воздуха, поднимающий её, а хвост помогает поворачивать",
    "рыба": "рыба дышит так: пропускает воду через жабры, которые забирают из неё кислород, а плавники и хвост помогают плыть",
    "пчела": "пчела делает мёд так: собирает нектар из цветов, несёт его в улей и складывает в соты, где влага испаряется и получается мёд",
    "радуга": "радуга появляется так: солнце светит сквозь капельки дождя, каждая капля преломляет свет и разбивает его на цветные лучи",
    "тень": "тень появляется так: непрозрачный предмет загораживает свет, и позади него на земле остаётся тёмное пятно без света",
    "эхо": "эхо появляется так: звук отражается от стены или горы и возвращается назад, поэтому мы слышим голос дважды",
    "ветер": "ветер образуется так: солнце нагревает воздух неравномерно, тёплый воздух поднимается, а холодный приходит на его место, и так возникает движение воздуха",
    "карандаш": "карандаш пишет так: грифель внутри стирается о бумагу, оставляя тёмный след, и его можно легко стереть ластиком",
    "ластик": "ластик стирает так: мягкая резинка снимает с бумаги частички грифеля, и написанное карандашом исчезает",
    "клей": "клей склеивает так: он наносится на поверхность тонким слоем, подсохнув, прочно соединяет части вместе",
    "бабочка": "бабочка появляется так: из гусеницы образуется куколка, а из куколки выходит взрослая бабочка с крыльями",
    "лягушка": "лягушка растёт так: из икринки выходит головастик, который живёт в воде, а потом отращивает лапки и становится лягушкой",
    "дерево": "дерево растёт так: из семечка появляется росток, он тянется к свету, и из него вырастают ствол, ветви и листья",
    "цветок": "цветок распускается так: из бутона раскрываются лепестки, а внутри созревают семена для новых растений",
    "котёнок": "котёнок растёт так: рождается слепым и беспомощным, пьёт молоко матери, а потом открывает глаза и становится котом",
    "щенок": "щенок растёт так: рождается маленьким и беспомощным, растёт на молоке матери и постепенно становится взрослой собакой",
    "цыплёнок": "цыплёнок появляется так: из яйца под наседкой вылупляется птенчик, который растёт и становится курицей или петухом",
    "дверь": "дверь работает так: она закреплена на петлях, вращается вокруг края и открывает или закрывает проход в комнату",
    "окно": "окно работает так: стекло пропускает свет, а рама держит его и открывается, чтобы впустить свежий воздух",
    "лестница": "лестница работает так: ступеньки расположены одна над другой, и по ним поднимаются или спускаются на другой этаж",
    "мост": "мост работает так: он перекинут через реку или дорогу и держится на опорах, по нему переходят или переезжают на другую сторону",
    "колодец": "колодец работает так: он уходит глубоко в землю до подземной воды, и воду достают ведром на верёвке или насосом",
    "кран": "кран работает так: внутри есть клапан, который открывается при повороте ручки и пропускает воду из трубы",
    "лыжи": "лыжи скользят так: длинные полозья распределяют вес на снегу и скользят по нему, а палки помогают отталкиваться",
    "коньки": "коньки скользят так: под ними тонкое лезвие, которое тает лёд и скользит по тонкой плёнке воды, а ботинки держат ногу",
    "печка": "печка греет так: в ней сжигают дрова, огонь нагревает кирпичи, которые долго отдают тепло в дом",
    "парусник": "парусник плывёт так: ветер надувает паруса, сила ветра толкает судно вперёд по воде",
    "гром": "гром возникает так: молния сильно нагревает воздух, он быстро расширяется и издаёт раскатистый звук",
    "молния": "молния появляется так: в грозовом облаке накапливается электрический заряд, и он разряжается вспышкой к земле",
    "дождь": "дождь образуется так: в облаках капли воды соединяются, тяжелеют и падают на землю",
    "ливень": "ливень идёт так: сильный дождь, когда сгустки водяного пара охлаждаются и обрушиваются потоками воды",
    "снег": "снег образуется так: в холодном облаке пар замерзает в снежинки, которые опускаются на землю",
    "туман": "туман появляется так: тёплый влажный воздух встречает холодный, и пар превращается в мелкие капельки у земли",
    "землетрясение": "землетрясение происходит так: под землёй плиты сдвигаются и толкают друг друга, и эти толчки сотрясают поверхность",
    "извержение вулкана": "вулкан извергается так: из горячих недр поднимается расплавленная лава, газы и пепел и выходят через кратер",
    "наводнение": "наводнение происходит так: после сильных дождей река выходит из берегов и заливает землю вокруг",
    "свисток": "свисток свистит так: воздух проходит через узкое отверстие и заставляет его свистеть на высокой ноте",
    "барабан": "барабан звучит так: палочки или ладони ударяют по натянутой коже, она дрожит и издаёт глухой грохот",
    "гитара": "гитара звучит так: струны натянуты на корпус, их щипают пальцами, и они дрожат, а деревянный корпус усиливает звук",
    "скрипка": "скрипка звучит так: смычок трётся о струны, они дрожат, и корпус скрипки усиливает тонкий певучий звук",
    "пианино": "пианино звучит так: при нажатии на клавишу молоточек ударяет по струне, и она дрожит, издавая звук",
    "флейта": "флейта играет так: музыкант дует в отверстие, воздух раскачивается внутри трубки и рождает светлый свистящий тон",
    "саксофон": "саксофон звучит так: музыкант дует в мундштук с тростью, она вибрирует, и металлический корпус усиливает звук",
    "труба": "труба звучит так: музыкант дует в мундштук, губы вибрируют, и звук усиливается по металлической трубке",
    "прилив": "прилив и отлив происходят так: луна своим притяжением поднимает воду в океане, образуя высокую волну к берегу",
}


def _extract_why_concept(query):
    """Извлекает понятие из вопроса «почему/зачем про X». Через словарь понятий
    и узлы графа (по стему). Один return: str|None."""
    q0 = (query or "").lower()
    q_words = [w for w in _clean_q(query).split() if len(w) > 3 and w not in (
        "почему", "зачем", "нужен", "нужна", "нужно", "важен", "важна", "важно",
        "важны") and w not in _RELATION_JUNK]
    # 1) ключ базы объяснений — по точному вхождению или первому стему
    #    («базы данных»/«база данных» → база данных, «нужен сон» → сон)
    #    сначала составные ключи (точное вхождение всей фразы), чтобы
    #    «вода мокрая» не съедался одиночным «вода» (подстрока)
    for topic in _WHY_REASONS:
        if " " in topic and topic in q0:
            return topic
    for topic in _WHY_REASONS:
        if " " in topic:
            continue
        tfirst = topic.split()[0]
        if topic in q0 or any(_stem_match(tfirst, qw) for qw in q_words):
            return topic
    # 2) понятия из словаря
    try:
        from algos.module_knowledge import fk
        for t, name in _concept_terms():
            if _stem_match(t, q_words[0]) if q_words else False:
                return t
    except Exception:
        pass
    # 3) узлы графа по точному слову
    if q_words:
        for n in kg.nodes:
            w = n.split()[0]
            if w in q_words and w not in _RELATION_JUNK:
                return w
    return None


def try_why(query):
    """Связный ответ на «почему/зачем нужен X» по базе причинно-следственных
    объяснений; иначе None (не вопрос-причина или за пределами базы).
    Один return: str|None."""
    q = (query or "").lower()
    if not any(m in q for m in ("почему", "зачем")):
        return None
    topic = _extract_why_concept(query)
    ans = None
    if topic and topic in _WHY_REASONS:
        reason, benefit = _WHY_REASONS[topic]
        ans = (f"{topic.capitalize()}: потому что {reason}. "
               f"Зачем это нужно: {benefit}.")
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
    print("--- обогащение ---")
    print(try_enrich("расскажи про нейрон"))
    print("--- связи ---")
    print(try_what_links("что связано с память?"))
    print("--- подобие ---")
    print(try_similar("что общего у нейрона и сигнала?"))
    print("--- отношения ---")
    print(try_relation("как связаны нейрон и мысль?"))
    print(try_relation("в чём разница между сигналом и мыслью?"))