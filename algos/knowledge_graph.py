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
        if name not in self.nodes:
            self.nodes[name] = Node(name, tag, facts, weight)
            self._adj[name] = []
        elif facts:
            self.nodes[name].facts = list(dict.fromkeys(self.nodes[name].facts + facts))

    def add_edge(self, src, pred, dst, weight=1.0):
        s, d = self._norm(src), self._norm(dst)
        p = self._norm(pred)
        if not s or not d or s == d or not p:
            return
        try:
            weight = float(weight)
        except Exception:
            weight = 1.0
        self.add_node(s)
        self.add_node(d)
        key = (s, p, d)
        self.edges[key] = max(self.edges.get(key, 0.0), weight)
        # синхронизируем вес в индексе соседей (двусторонне)
        self._set_adj_weight(s, p, d, self.edges[key])
        self._set_adj_weight(d, p, s, self.edges[key])

    def _set_adj_weight(self, from_node, pred, to_node, weight):
        """Обновляет вес связи в _adj для направления from_node->to_node.
        Пустые узлы игнорируются. Один return: None."""
        if not from_node or not to_node:
            return None
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
        if amount <= 0 or not node_a or not node_b:
            return 0
        a, b = self._norm(node_a), self._norm(node_b)
        strengthened = 0
        try:
            depth = int(depth)
        except Exception:
            depth = 0
        targets = [b]
        if depth > 0:
            for p, other, _w in self._adj.get(a, [])[:depth]:
                if other not in targets:
                    targets.append(other)
        for tgt in targets:
            for key, w in list(self.edges.items()):
                if not (isinstance(key, (tuple, list)) and len(key) == 3):
                    continue
                s, p, d = key
                if (s == a and d == tgt) or (s == tgt and d == a):
                    nw = min(2.0, w + amount)
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
        if amount < 0 or floor < 0:
            return 0
        changed = 0
        for key, w in list(self.edges.items()):
            try:
                w = float(w)
            except Exception:
                continue
            nw = max(floor, w - amount)
            if nw != w:
                self.edges[key] = nw
                changed += 1
        return changed

    @staticmethod
    def _norm(name):
        return _re.sub(r"\s+", " ", str(name or "")).strip().lower().rstrip(".!?;")[:200]

    def prune_noise(self, noise_preds=None, max_phrase_words=4):
        """Убирает мусор: рёбра с шумовыми предикатами («это», «есть», «если»)
        и узлы-фразы длиннее max_phrase_words слов (корпусный шум, не понятия).
        Один return: int — число удалённых элементов (узлы+рёбра+предикаты)."""
        removed = 0
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
            and self._norm(k[1]) in noise_preds
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
        for row in self._adj.get(a, []):
            if not (isinstance(row, (tuple, list)) and len(row) >= 3):
                continue
            p, other, w = row
            if other == b and (p, w) not in seen:
                seen.add((p, w))
                rels.append((p, w))
        for row in self._adj.get(b, []):
            if not (isinstance(row, (tuple, list)) and len(row) >= 3):
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
        nxt = []
        found = None
        if frontier:
            frontier = frontier[:max_fanout]  # не раздувать фронт без конца
        for entry in frontier:
            if not (isinstance(entry, (tuple, list)) and len(entry) >= 2):
                continue
            cur, trail = entry[0], entry[1]
            for p, other, w in self.neighbors(cur):
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
        if n:
            lines = [f"«{name}» — {n.tag}"]
            if n.facts:
                lines.append("Факты: " + "; ".join(n.facts[:5]))
            # соседи по силе связи (вес) — сначала самые «проводимые»
            safe_nbrs = [r for r in self.neighbors(name)
                         if isinstance(r, (tuple, list)) and len(r) >= 3]
            ranked = sorted(safe_nbrs, key=lambda r: -r[2])
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
        # граф изменился — сбрасываем кэш дорогих вычислений
        self._cache = {}
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
            # ранжируем по весу, отдаём самое связанное (без корпусных фраз-шума)
            junk_neighbors = {"откуда", "нашел", "нашла", "найти", "хочешь", "давай",
                              "спросить", "скажи", "посмотрю", "сделаю", "можно", "тебя"}
            filtered = {}
            for o, (p, w) in candidates.items():
                oclean = o.split()[0] if " " in o else o
                if len(o) <= 24 and " " not in o.strip() and oclean not in junk_neighbors:
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
                for (s, p, t), w in list(self.edges.items()):
                    if s == d:
                        self.edges[(canon, p, t)] = w if (canon, p, t) not in self.edges else max(w, self.edges[(canon, p, t)])
                        del self.edges[(s, p, t)]
                    elif t == d:
                        self.edges[(s, p, canon)] = w if (s, p, canon) not in self.edges else max(w, self.edges[(s, p, canon)])
                        del self.edges[(s, p, t)]
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
            self.edges = {k: w for k, w in self.edges.items()
                          if k[0] not in dead and k[2] not in dead}
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
        for (s, p, d) in self.edges:
            connected.add(s)
            connected.add(d)
        isolated = [n for n in self.nodes if n not in connected]
        if sample_conn and len(connected) > sample_conn:
            import random as _rnd
            connected = set(_rnd.sample(list(connected), sample_conn))
        stop = {"это", "что", "как", "для", "на", "в", "по", "с", "из", "и", "или"}
        added = 0
        # для быстрого поиска: слово -> связные узлы, содержащие его (по одному на слово)
        word_index = {}
        for c in connected:
            for w in set(_re_b.findall(r"[а-яёa-z]{4,}", c.lower())):
                if w not in stop and w not in word_index:
                    word_index[w] = c
        for node in isolated:
            if added >= max_edges:
                break
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
            if " " not in node or len(node.split()) > max_phrase_words:
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
            for p, other, w in sorted(self.neighbors(name), key=lambda r: -r[2])[:8]:
                lines.append(f"{name} {p} {other} (вес {w:.2f})")
        return lines

    def similarity(self, a, b):
        """Насколько понятия связаны: число общих соседей / общий путь,
        с мягким бонусом за прямое ребро. Пустые узлы → 0. Один return: float 0..1."""
        a, b = self._norm(a), self._norm(b)
        if not a or not b:
            return 0.0
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
                # Jaccard на окрестностях + мягкий бонус за прямое соединение
                direct = 1.0 if self.relation(a, b) else 0.0
                result = 0.85 * (len(inter) / len(union)) + 0.15 * direct
        return result

    def centrality(self, top_n=10, exclude_junk=True):
        """Центральность понятий: степень узла (число рёбер) как мера важности.
        Возвращает топ-список (понятие, степень) и среднюю степень.
        Один return: dict."""
        degree = {}
        for (s, p, d) in self.edges:
            degree[s] = degree.get(s, 0) + 1
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
        cache_key = ("conn", top_n, len(self.edges))
        hit = self._cache.get(cache_key)
        out = None
        if hit is not None:
            out = dict(hit)
            out["top_degree"] = list(hit["top_degree"])
            return out
        neigh = {}
        for (s, p, d) in self.edges:
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
        a = self._norm(name)
        out = []
        cache_key = ("close", a, top_n, min_sim, len(self.edges))
        hit = self._cache.get(cache_key)
        if hit is not None:
            return list(hit)
        if a in self.nodes:
            na = {row[1] for row in self._adj.get(a, [])}
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
        if not a or not b:
            return 0.0
        a, b = self._norm(a), self._norm(b)
        best = 0.0
        for p, other, w in self._adj.get(a, []):
            if other == b and w > best:
                best = w
        return best

    def reward(self, a, b, amount=0.3):
        """Положительный отклик: усилить связь между a и b (Хебб).
        amount<=0 игнорируется. Один return: int — сколько связей усилено."""
        if amount <= 0:
            return 0
        return self.hebbian_learn(a, b, amount)

    def reward_sign(self, a, b, feedback_sign=1.0, amount=0.05):
        """Хебб-обновление связи по знаку отклика через reward/punish.
        Малый знак (≈0) или amount<=0 — нейтрально. Один return: int."""
        if abs(feedback_sign) < 1e-9 or amount <= 0:
            return 0
        changed = 0
        if feedback_sign >= 0:
            changed = self.hebbian_learn(a, b, amount)
        else:
            changed = self.punish(a, b, amount)
        return changed

    def punish(self, a, b, amount=0.3, floor=0.15):
        """Отрицательный отклик: ослабить связь (анти-Хебб).
        amount <= 0 игнорируется. Один return: int."""
        if amount <= 0:
            return 0
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
        note = "" if self.edges else " (граф пуст)"
        return f"граф: {len(self.nodes)} узлов, {len(self.edges)} связей{note}"

    def topic_clusters(self, max_clusters=6, max_nodes=60):
        """Выделяет кластеры тем в графе (простая агломеративная кластеризация):
        стартуем с центральных узлов и «притягиваем» их соседей, группируя по
        общности связей. Возвращает список (тема-центр, [узлы]). Плюс мосты —
        узлы, которые соединяют несколько кластеров между собой.

        Один return: dict {'clusters': [...], 'bridges': [...], 'edges': ...}."""
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
        for (s, p, d) in self.edges:
            degree[s] = degree.get(s, 0) + 1
            degree[d] = degree.get(d, 0) + 1
        # структурный фильтр: исключаем узлы, чьи связи почти все через мусорный
        # предикат «связано_с» — это корпусные хабы-связки, а не «темы знаний»
        good_pred_share = {}
        edge_totals = {}
        noisy_preds = {"связано_с", "связано"}
        for (s, p, d) in self.edges:
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
        ranked.sort(key=lambda x: -x[0])
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
    try:
        from algos.module_knowledge import try_definition, try_function_knowledge
        definition = try_definition("что такое " + start) or try_function_knowledge("что такое " + start)
        if definition:
            parts.append(definition.strip())
    except Exception:
        parts = parts
    # 2) ключевые связи из графа: ДЕКЛАРАТИВНАЯ речь, а не сырые цепочки.
    # Каждая связь превращается в осмысленную фразу: «X — это то, что p к Y,
    # потому что (через Y) связано с Z» — как люди объясняют через ассоциации.
    if start in kg.nodes:
        try:
            ranked = sorted(kg._adj.get(start, []), key=lambda r: -r[2])
            links = []
            # предикаты, которые звучат как определение («есть», «является»)
            definitional = {"есть", "является", "представляет", "это", "это такое"}
            for p, other, w in ranked[:4]:
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
                    # «X связан с Y» + добавим ещё один ход — почему/к чему
                    deeper = ""
                    nxt = sorted(kg._adj.get(otherc, []), key=lambda r: -r[2])[:2]
                    for p2, other2, w2 in nxt:
                        o2 = other2.split()[0] if " " in other2 else other2
                        if o2 not in (start, otherc):
                            deeper = f", а это влияет на {o2}"
                            break
                    links.append(f"{start} связан с {otherc}{deeper}")
            if links:
                # склеиваем фразами, не «|» и не через точку-запятую: как речь
                spoken = "; ".join(dict.fromkeys(links[:4]))
                parts.append(spoken[0].upper() + spoken[1:] + ".")
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
    if not (_re.search(r"[a-z]_\w+", q) or _we_is_algo_ask(q)) and _wants_links(q):
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