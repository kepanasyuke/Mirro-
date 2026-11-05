# -*- coding: utf-8 -*-
"""Mirro Algorithms — 27 · Квантовый граф (Quantum Graph of Concepts)

Инновация: узел знаниевого графа живёт не как «вкл/выкл», а как КВАНТОВАЯ
СУПЕРПОЗИЦИЯ смыслов. Каждому понятию сопоставляется комплексная амплитуда
ψ = α + iβ. Роу-ссылки мета-графа (graph.meta_routes) играют роль квантовых
операторов вращения фазы, «запутывающих» состояния соседних понятий ДО
коллапса (выбора конкретной ветки генерации) по правилу Борна P=|α|².

Это даёт вариативность вывода: сеть не всегда выбирает одну и ту же семантику,
а «размазывает» вероятность по близким смыслам и лишь затем измеряет.

Чистый Python, без внешних библиотек, атомарные функции (один return).
Работает поверх РеАЛЬНОГО KnowledgeGraph (узлы-Node, рёбра (src,p,dst)).
"""
import math


class QState:
    """Хранилище квантовых состояний узлов графа: {имя_узла: (alpha, beta)}.

    Отдельно от Node (у того __slots__ без полей для ψ) — чистая структура,
    не нарушающая реальный граф. Один return на метод."""
    def __init__(self):
        self.states = {}   # name -> (alpha, beta)

    def get(self, name):
        return self.states.get(name, (0.0, 0.0))


def norm_states(state):
    """Нормирует все амплитуды так, чтобы |α|²+|β|² = const для каждого узла.
    Один return: dict (имя -> (alpha, beta))."""
    out = {}
    for name, (a, b) in state.states.items():
        norm = math.hypot(a, b) or 1.0
        out[name] = (a / norm, b / norm)
    return out


def init_quantum_states(graph):
    """Инициализирует суперпозицию узлов: равные амплитуды (|α|=|β|=1/√2).
    Один return: QState (новое хранилище)."""
    st = QState()
    inv = 1.0 / math.sqrt(2.0)
    for name in graph.nodes:
        st.states[name] = (inv, inv)
    return st


def _valid_node(graph, name):
    """Существует ли узел (с нормализацией). Один return: str|None."""
    n = (name or "").strip().lower()
    if n in graph.nodes:
        return n
    for node in graph.nodes:
        if node == n or n in node or node.startswith(n[:4]):
            return node
    return None


def apply_quantum_entanglement(graph, st, src_edge, tgt_edge, mod=1.0):
    """Вращает фазу волновой функции узлов целевого ребра.

    src_edge, tgt_edge — ключи рёбер (орт, предикат, dst). Угол поворота
    θ = проводимость источника × mod роу-ссылки. Чистая функция: возвращает
    новый QState. Один return: QState.
    """
    edges = graph.edges
    if src_edge not in edges or tgt_edge not in edges:
        return st
    s_from, _p1, s_to = src_edge
    t_from, _p2, t_to = tgt_edge
    # активность источника = проводимость ребра-источника
    theta = edges[src_edge] * mod
    new_states = dict(st.states)
    for node_key in (t_from, t_to):
        real = _valid_node(graph, node_key)
        if real is None:
            continue
        a_real, b_imag = new_states.get(real, (0.0, 0.0))
        na = a_real * math.cos(theta) - b_imag * math.sin(theta)
        nb = a_real * math.sin(theta) + b_imag * math.cos(theta)
        norm = math.hypot(na, nb) or 1.0
        new_states[real] = (na / norm, nb / norm)
    out = QState()
    out.states = new_states
    return out


def collapse_wave_function(st, name, seed, rng):
    """Измерение (коллапс) состояния узла из суперпозиции в 0/1 по Борну.
    Один return: float (0.0 или 1.0)."""
    a, _b = st.get(name)
    prob_zero = a * a
    r = (rng.random() if rng else 0.5)
    return 1.0 if r > prob_zero else 0.0


def quantum_superposition_report(graph, st, top_n=6):
    """Отчёт о суперпозициях узлов (для /health и чата). Один return: str."""
    items = []
    for name, (a, b) in st.states.items():
        if not name or len(name) < 3:
            continue
        probe = abs(a) + abs(b)
        items.append((probe, name, a, b))
    items.sort(key=lambda x: -x[0])
    lines = [f"квантовые состояния: {len(st.states)} узлов в суперпозиции"]
    for _p, name, a, b in items[:top_n]:
        p0 = a * a
        lines.append(f"  «{name}»: P(активен)={p0:.2f}, фаза θ={math.atan2(b, a):.2f}")
    return "\n".join(lines)


def try_quantum(query):
    """Точка входа для try_*: отвечает про квантовое состояние графа.
    Один return: str или None."""
    q = (query or "").lower()
    ans = None
    if any(w in q for w in ("квант", "суперпозиц", "волновая функц", "запутан",
                            "квантовое состояни", "квантовый граф")):
        try:
            from knowledge_graph import kg
            st = init_quantum_states(kg)
            # применим одну «квантовую» модуляцию по первой роу-ссылке
            meta = getattr(kg, "meta_routes", None)
            if meta:
                (se, te), mod = next(iter(meta.items()))
                st = apply_quantum_entanglement(kg, st, se, te, mod)
            ans = quantum_superposition_report(kg, st)
        except Exception:
            ans = "Квантовый граф пока пуст — наполните знания, затем измерю суперпозиции."
    return ans


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    from neural_electric import add_meta_route
    g = KnowledgeGraph()
    g.from_triples([
        ("Внимание", "влияет на", "память"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
    ])
    add_meta_route(g, ("внимание", "влияет на", "память"),
                   ("память", "укрепляет", "понимание"), mod=0.5)
    st = init_quantum_states(g)
    st2 = apply_quantum_entanglement(g, st,
                                     ("внимание", "влияет на", "память"),
                                     ("память", "укрепляет", "понимание"),
                                     mod=0.5)
    a, b = st2.get("память")
    print("суперпозиция памяти:", round(a, 4), round(b, 4), "| нормировка=", round(a*a+b*b, 6))
    print(quantum_superposition_report(g, st2))