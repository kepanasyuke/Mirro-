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
    Не-строка query/None-граф → [] ; max_depth<=0 → 2. Возвращает список
    строк-выводов, либо [].
    """
    try:
        max_depth = int(max_depth)
        if max_depth <= 0:
            max_depth = 2
    except Exception:
        max_depth = 2
    q = (query or "").lower() if isinstance(query, str) else ""
    if kg is None or not hasattr(kg, "nodes"):
        return []
    # стартовые узлы: тема (если указана) + узлы графа, что встречаются в вопросе
    starts = []
    if isinstance(topic, str) and topic:
        starts.append(topic)
    for name in (kg.nodes or []):
        if isinstance(name, str) and name and len(name) > 3 and name in q:
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
        if len(results) >= 8:
            break
    # обрезать до внятных
    return results[:8]


def _recurse(kg, node, trail, max_depth, results, seen_prefix, cap=8):
    """Обход в глубину с фиксацией путей (не ходим в циклы повторно).
    Емкость results ограничена cap — защита от неограниченного роста."""
    if len(results) >= cap:
        return
    if len(trail) >= max_depth:
        trail_with = trail + [node]
        if len(trail_with) >= 2:
            results.append(trail_with)
        return
    neighbors = kg.neighbors(node) if kg is not None else []
    for nb in (neighbors or []):
        if not isinstance(nb, (tuple, list)) or len(nb) < 2:
            continue
        pred, other = nb[0], nb[1]
        if other in trail:
            continue  # не зацикливаемся на уже посещённых узлах
        key = (node, pred, other)
        if key not in seen_prefix:
            seen_prefix.add(key)
            _recurse(kg, other, trail + [node], max_depth, results, seen_prefix)
            seen_prefix.discard(key)


def format_path(path):
    """path = ['a','b','c'] — соединяет узлы стрелками. Один return: str."""
    if not path:
        return ""
    return " → ".join(str(x) for x in path)


def _chain_to_str(kg, chain):
    """Цепочка узлов -> строка вида «a —p→ b». Пустая цепочка → «».
    Один return: str."""
    if not chain:
        return ""
    parts = []
    for i in range(len(chain) - 1):
        a = str(chain[i])
        b = str(chain[i + 1])
        rels = kg.relation(a, b) if kg is not None else None
        pred = rels[0][0] if rels else "связан"
        parts.append(f"{a} —{pred}→ {b}")
    return " ; ".join(parts)


def _join_chains(kg, chains):
    """Собирает человекочитаемый ответ из первых цепочек. Один return: str."""
    lines = []
    for ch in chains[:4]:
        part = _chain_to_str(kg, ch)
        if part:
            lines.append(part)
    return "Из своих связей вывожу: " + " | ".join(lines) + "."


_INFER_WORDS = ("как", "почему", "объясни", "что такое", "выведи", "связано",
                "связи", "отношение", "вывод", "из чего следует")


def _looks_like_reasoning(q):
    """Похож ли запрос на вопрос-вывод. Не-строка → False. Один return: bool."""
    if not isinstance(q, str):
        return False
    return any(w in q for w in _INFER_WORDS)


def try_graph_infer(query):
    """Точка входа для try_*: отвечает, если граф непуст и вопрос про связи.
    Один return: str или None."""
    from knowledge_graph import kg
    answer = None
    q = (query if isinstance(query, str) else "").lower()
    if kg.edges and len(kg.nodes) >= 3 and _looks_like_reasoning(q):
        chains = infer_from_graph(kg, q, max_depth=2)
        if chains:
            answer = _join_chains(kg, chains)
    return answer


_TOPIC_STOP = {"что", "такое", "объясни", "расскажи", "про", "значит", "поясни",
               "это", "как", "почему", "если", "который", "работает", "напиши",
               "покажи", "есть", "быть", "сделать", "можно", "нужно", "ещё",
               "можно сказать", "можно попробовать", "связано с", "про понятие",
               "если говорить", "мачу-пикчу", "переустановить ide",
               "искусство возможного", "давай", "иначе", "вообще", "просто",
               "смотря", "пока что", "так сказать", "связано", "связан",
               "связь", "связан с"}

_JUNK_TOPIC_MARKERS = ("можно сказать", "попробовать", "переустановить",
                       "про понятие", "если говорить о", "связано с",
                       "мачу-пикчу", "насколько", "хочешь", "поиграть",
                       "обида", "дай тебе", "смотри намека")


def _is_junk_topic(n):
    """Мусорное ли понятие-фраза (личные обращения, «вода» из корпуса).
    Не-строка → True. Один return: bool."""
    if not isinstance(n, str):
        return True
    nlow = n.lower()
    return any(m in nlow for m in _JUNK_TOPIC_MARKERS) or nlow in _TOPIC_STOP


def _graph_topics(graph, query, limit=12):
    """Узлы графа, встреченные в запросе (также по словоформе: 4-буквенный
    префикс узла входит в текст). graph — KnowledgeGraph. Один return: list."""
    import re as _re
    graph = graph or kg
    q = (query if isinstance(query, str) else "").lower()
    found = []
    for n in graph.nodes:
        if not n or len(n) < 4 or _is_junk_topic(n):
            continue
        core = n.split()[0] if " " in n else n
        if " " in n:
            # понятие-фраза: совпадение нужно по всей фразе
            if n in q:
                found.append(n)
        elif core in _TOPIC_STOP or len(core) < 4:
            continue
        elif core in q:
            found.append(n)
    seen = set()
    uniq = []
    for n in sorted(found, key=len, reverse=True)[:limit]:
        if n not in seen:
            seen.add(n)
            uniq.append(n)
    return uniq


def _infer_paragraph(kg_obj, start, max_depth=2):
    """Строит связное рассуждение от start по самым сильным рёбрам графа:
    собрать 2-шаговые цепочки и склеить в один абзац «вывода».
    Один return: str или None."""
    if not isinstance(kg_obj, object) or kg_obj is None or start not in (kg_obj.nodes or {}):
        return None
    text = None
    try:
        nbrs = [n for n in (kg_obj.neighbors(start) or []) if isinstance(n, (tuple, list)) and len(n) >= 3]
    except Exception:
        return None
    ranked = sorted(nbrs, key=lambda r: -r[2])
    parts = []
    for p, other, w in ranked[:3]:
        try:
            nxt = [n for n in (kg_obj.neighbors(other) or []) if isinstance(n, (tuple, list)) and len(n) >= 3]
        except Exception:
            continue
        for p2, other2, w2 in sorted(nxt, key=lambda r: -r[2])[:2]:
            if other2 == start or other2 == other:
                continue
            parts.append(f"{start} {p} {other}, а это {p2} {other2}")
    if parts:
        text = ("Если говорить о «" + start + "», в моих связях выходит так: "
                + "; ".join(dict.fromkeys(parts[:4])) + ".")
    return text


def try_infer_unknown(graph, query):
    """Вывод знаний для неизвестных вопросов: когда прямого ответа нет, берём
    узлы графа из вопроса и строим цепочку рассуждений по сильным связям.
    graph — GRAPH объект (KnowledgeGraph), НЕ модуль kg.
    Пустой граф или запрос → None. Один return: str или None."""
    if graph is None or not isinstance(query, str) or not query.strip():
        return None
    tokens = _graph_topics(graph, query)
    # если узлов в вопросе нет — используем понятия, схожие по основе словам запроса
    if not tokens and len(graph.nodes) >= 3 and graph.edges:
        tokens = _graph_topics_for_unknown(graph, query)
    answer = None
    for start in tokens:
        block = _infer_paragraph(graph, start, max_depth=2)
        if block:
            answer = block
            break
    return answer


def _graph_topics_for_unknown(graph, query):
    """Когда в вопросе нет точных узлов графа, возвращает понятия, чья основа
    (стем-подобный 4-префикс) близка словам запроса. graph — KnowledgeGraph.
    Не-граф/None → []. Один return: list."""
    import re as _re
    if graph is None or not hasattr(graph, "nodes"):
        return []
    graph = graph or kg
    q = (query or "").lower()
    words = [w for w in _re.findall(r"[а-яёa-z]{4,}", q) if w not in _TOPIC_STOP]
    scores = []
    for n in (graph.nodes or []):
        if not isinstance(n, str) or len(n) < 4 or _is_junk_topic(n):
            continue
        core = n.split()[0] if " " in n else n
        for w in words[:8]:
            prefix = core[:4]
            if prefix == w[:4] and len(core) >= len(w) - 2:
                scores.append((len(core), n))
                break
    scores.sort(key=lambda kv: -kv[0])
    return [n for _, n in scores[:5]]


# ============================================================
#  Интеграция опыта и динамический вывод (на реальном KnowledgeGraph:
#  edges[(src,pred,dst)] -> weight). Опыт — список латентных паттернов
#  (векторов активных весов), накопленных успешными эпохами.
# ============================================================
def _edge_pattern(graph):
    """Латентный паттерн графа: вектор активных весов рёбер. Не-граф → [].
    Один return: list."""
    if graph is None or not isinstance(getattr(graph, "edges", None), dict):
        return []
    out = []
    for w in graph.edges.values():
        try:
            out.append(float(w))
        except Exception:
            out.append(0.0)
    return out


def try_get_memory_experience(graph, active_pattern, experience=None):
    """Ищет наиболее схожий прошлый опыт косинусным сходством. Один return: list.
    Если опыта нет — возвращает нулевой паттерн той же длины."""
    if experience is None:
        experience = getattr(graph, "experience", [])
    if not isinstance(experience, (list, tuple)):
        experience = []
    best_match = [0.0] * len(active_pattern)
    if experience:
        try:
            exp0 = list(experience[0])
        except Exception:
            exp0 = []
        best_match = exp0 or best_match
        best_score = -1.0
        for exp in experience:
            try:
                exp = list(exp)
            except Exception:
                continue
            dot = sum(a * e for a, e in zip(active_pattern, exp))
            norm_a = (sum(a * a for a in active_pattern) ** 0.5) or 1.0
            norm_e = (sum(e * e for e in exp) ** 0.5) or 1.0
            denom = norm_a * norm_e
            score = dot / denom if denom else 0.0
            if score > best_score:
                best_score = score
                best_match = exp
    return best_match


def generate_dynamic_inference(graph, W_decoder, blend=0.25):
    """Смешивает текущий паттерн активных весов с прошлым опытом (памятью)
    и пропускает через перцептрон-декодер. Один return: (signal, integrated)."""
    current = _edge_pattern(graph)
    past = try_get_memory_experience(graph, current)
    n = max(len(current), len(past))
    current = list(current) + [0.0] * (n - len(current))
    past = list(past) + [0.0] * (n - len(past))
    integrated = [(1 - blend) * c + blend * p for c, p in zip(current, past)]
    try:
        W = list(W_decoder)
    except Exception:
        W = []
    signal = sum(i * w for i, w in zip(integrated, W))
    return signal, integrated


def remember_pattern(graph, pattern, max_experience=50):
    """Записывает успешный латентный паттерн в память графа. Один return: int."""
    if graph is None:
        return 0
    try:
        max_experience = int(max_experience)
        max_experience = max(1, min(1000, max_experience))
    except Exception:
        max_experience = 50
    if not hasattr(graph, "experience") or not isinstance(graph.experience, list):
        graph.experience = []
    if len(graph.experience) >= max_experience:
        graph.experience.pop(0)
    graph.experience.append(list(pattern))
    return len(graph.experience)


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