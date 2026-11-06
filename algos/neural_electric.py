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
import sys, os, math
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from knowledge_graph import KnowledgeGraph
from refractory import init_refractory_counters, update_refractory_states, apply_fatigue_to_weights


# по-босовски: ток идёт по «проводу-связи», если «напряжение» выше порога
def _threshold_for(e, base=0.5, dip=0.15, ser=0.15, nor=0.2):
    """Порог активации узла от медиаторов. Один return: float (0..1).

    дофамин и серотонин повышают порог (спокойно), норадреналин понижает
    (легче возбудиться, тревога/бодрость).
    """
    return max(0.05, min(0.95, base - nor + (dip + ser) * 0.2))


def fire(graph, start, neuromod=None, voltage=1.0, max_hops=4, decay=0.5, learn=False):
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
        if v >= threshold:
            activated.append((node, hop, round(v, 3)))
            for pred, other, w in graph.neighbors(node):
                # вес связи (из ТТЛ) усиливает остаточное напряжение по-босовски:
                # ЕСЛИ есть связь ТО передать, вес = проводимость
                if other not in seen:
                    seen.add(other)
                    nv = v * decay * (0.5 + w) if w else v * decay * 0.6
                    if nv >= threshold:
                        frontier.append((other, hop + 1, nv))
                        # Хебб: импульс, прошедший по связи, её укрепляет
                        if learn and hasattr(graph, "hebbian_learn"):
                            graph.hebbian_learn(node, other, amount=0.03)
    return activated


def _avg_dimension(graph, nodes):
    """Средняя размерность затронутых узлов (по zero_dimensional). Один return: float."""
    try:
        from zero_dimensional import dimension_of
    except Exception:
        return 0.0
    dims = [dimension_of(graph, n)[0] for n in nodes if n in graph.nodes]
    return round(sum(dims) / len(dims), 2) if dims else 0.0


def _edges_on_path(graph, path_nodes):
    """Рёбра графа, реально соединяющие подряд идущие узлы пути.
    Возвращает список (src, pred, dst, weight). Один return: list."""
    found = []
    for i in range(len(path_nodes) - 1):
        a, b = path_nodes[i], path_nodes[i + 1]
        a, b = a.lower(), b.lower()
        for p, other, w in graph._adj.get(a, []):
            if other == b:
                found.append((a, p, b, w))
                break
        else:
            # обратное направление
            for p, other, w in graph._adj.get(b, []):
                if other == a:
                    found.append((b, p, a, w))
                    break
    return found


def hebbian_update_path(graph, path_nodes, feedback_sign, learning_rate=0.01,
                        floor=0.15, ceil=2.0):
    """Хебб-обучение роу-ссылок (рёбер) по знаку обратной связи.

    Если связь участвовала в активированном пути И фидбек успешен (+1) — ребро
    крепнет (проводимость растёт). При дизлайке/каше (-1) — слабеет. Это «мета»-
    уровень над обычным графом: учится не понятие, а то, КАКИМИ СВЯЗЯМИ ходить.

    Все функции имеют один return (структурный стиль LINTER).
    Возвращает: dict {updated, strengthened, weakened, avg_delta}.
    """
    result = {"updated": 0, "strengthened": 0, "weakened": 0, "avg_delta": 0.0}
    if not path_nodes or len(path_nodes) < 2 or graph is None:
        return result
    edges = _edges_on_path(graph, [n.lower() for n in path_nodes])
    if not edges:
        return result
    total = 0.0
    for src, pred, dst, weight in edges:
        delta = learning_rate * weight * feedback_sign
        new_w = weight + delta
        new_w = max(floor, min(ceil, new_w))
        graph.edges[(src, pred, dst)] = new_w
        if hasattr(graph, "_set_adj_weight"):
            graph._set_adj_weight(src, pred, dst, new_w)
            graph._set_adj_weight(dst, pred, src, new_w)
        total += abs(delta)
        result["updated"] += 1
        if delta > 0:
            result["strengthened"] += 1
        elif delta < 0:
            result["weakened"] += 1
    result["avg_delta"] = round(total / len(edges), 4) if edges else 0.0
    return result


def all_weights_on_path(graph, path_nodes):
    """Текущие активные веса рёбер пути (для отчёта). Один return: list."""
    return [(src, pred, dst, round(w, 3)) for src, pred, dst, w in _edges_on_path(graph, path_nodes)]


def visualize_chain(chain):
    """ASCII-карта силы импульса по цепочке (затухание). Один return: str."""
    if not chain:
        return ""
    rows = []
    for n, hop, v in chain:
        amp = int(v * 10)
        bar = "▮" * amp + "▯" * (10 - amp)
        rows.append(f"{n:<16} {bar} {v:.2f} (шаг {hop})")
    return "\n".join(rows)


def activate_chain(graph, start, neuromod=None, report_growth=True, viz=False, learn=False):
    """Осмысленная цепочка активированных понятий. Один return: str.

    Нуль-точка: если start изолирован (нет связей) — это «точка нигде»,
    сигнал не может пойти; честно говорим об этом. Если report_growth —
    добавляет метрику «средняя размерность» активированного пути.
    """
    if start.strip().lower() not in graph.nodes:
        return f"Понятие «{start}» ещё не в графе — импульс не от чего оттолкнуться."
    if not graph.neighbors(start.strip().lower()):
        return f"«{start}» — изолированная нуль-точка: нет связей, электричество не побежало."
    chain = fire(graph, start, neuromod=neuromod, learn=learn)
    if not chain:
        return f"Импульс от «{start}» затух — порог медиаторов слишком высок."
    parts = [f"{n}@{hop}:{v}" for n, hop, v in chain]
    result = " → ".join(parts)
    if viz:
        result += "\n" + visualize_chain(chain)
    if report_growth and len(chain) > 1:
        nodes = [n for n, _h, _v in chain]
        dim = _avg_dimension(graph, nodes)
        result += f"  [рост понимания: средняя размерность пути {dim}/3]"
    return result


def try_neural_electric(query, kg=None):
    """Точка входа для try_*: «пусти электричество от X», «активируй понятие X».
    Один return: str или None."""
    q = (query or "").strip().lower()
    ans = None
    m = None
    import re as _re
    for pat in (r"пусти (?:импульс|электричество|ток) (?:от|из) (.+)",
                r"обуч(?:и|ить).{0,8}импульс.{0,8}(?:от|из) (.+)",
                r"выучи (?:понятие\s+)?(.+)",
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
        if g is None or not g.nodes:
            try:
                from knowledge_graph import kg as _globkg
                g = _globkg if _globkg.nodes else KnowledgeGraph()
            except Exception:
                g = KnowledgeGraph()
        # в реальном графе узел может быть без окончания — ищем по вхождению
        anchor = _find_node(g, m)
        if anchor is not None:
            m = anchor
        want_viz = any(w in q for w in ["покажи", "визуализ", "схема", "карта", "нарисуй"])
        learn = any(w in q for w in ["обуч", "выучи", "запомн", "укрепи"])
        # обучение через импульс: извлечь ТТЛ-факты из запроса и влить в граф
        learned = 0
        if learn:
            try:
                from ttl_extract import extract
                facts = extract(q)
                if facts:
                    learned = g.from_triples(facts)
            except Exception:
                learned = 0
        ans = activate_chain(g, m, neuromod=nm.level, viz=want_viz, learn=learn)
        if learn and learned:
            ans += f"  [обучение: импульс извлёк и добавил {learned} новых фактов из твоих слов]"
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


# ============================================================
#  Сквозной мыслительный пайплайн (Reasoning Pipeline), работающий
#  на РЕАЛЬНОМ KnowledgeGraph: edges[(src, pred, dst)] -> weight.
#  Биометрия → модулированные рёбра → роу-импульсы → физика → опыт.
# ============================================================
def compute_modulated_edges(graph, ach=1.0, serotonin=1.0, dopamine=0.0):
    """Проводимость рёбер как функция нейромедиаторов. Возвращает dict
    edge_key -> active_weight (не мутирует граф — чистая функция).
    Один return: dict {(src,pred,dst): float}."""
    out = {}
    for key, w in list(graph.edges.items()):
        active = (w * ach * serotonin) + dopamine
        out[key] = active
    return out


def _edge_overlap_targets(edge_key, edges):
    """Куда от ребра (src,pred,dst) идут роу-связи: на рёбра, исходящие из dst.
    Возвращает список рёбер-целей. Один return: list keys."""
    src, _p, dst = edge_key
    targets = []
    for (s2, p2, d2), w in edges.items():
        if s2 == dst and d2 != src:
            targets.append((s2, p2, d2))
    return targets


def add_meta_route(graph, from_edge, to_edge, mod=1.0):
    """Регистрирует роу-ссылку «ребро→ребро» с коэффициентом модуляции.
    Отрицательный mod = подавление (каша гасится), положительный = усиление.
    Один return: int — число зарегистрированных роу-ссылок."""
    if not hasattr(graph, "meta_routes"):
        graph.meta_routes = {}
    graph.meta_routes[(from_edge, to_edge)] = float(mod)
    return len(graph.meta_routes)


def _meta_route_mod(graph, from_edge, to_edge):
    """Коэффициент роу-ссылки from_edge→to_edge, или топологический.
    Один return: float (может быть отрицательным для подавления)."""
    if hasattr(graph, "meta_routes"):
        return graph.meta_routes.get((from_edge, to_edge), 0.0)
    return 0.0


def propagate_meta_impulses(graph, active_weights):
    """Роу-импульсы «ребро→ребро»: активированное ребро модулирует исходящие
    из своей цели. Роу-ссылка из graph.meta_routes запрещает/усиливает ребро
    (mod<0 гасит «кашу», mod>0 усиливает). Возвращает новую dict проводимостей.
    Один return: dict edge_key -> active_weight."""
    out = dict(active_weights)
    if not hasattr(graph, "meta_routes") or not graph.meta_routes:
        # без явных роу-ссылок — топологическое усиление (обратная совместимость)
        for key, act in list(active_weights.items()):
            if act <= 0:
                continue
            for tgt in _edge_overlap_targets(key, graph.edges):
                if tgt in out:
                    out[tgt] = out[tgt] + act * key_meta_mod(key, out)
        return out
    # с явными роу-ссылками: применяем модуляцию (усиление/подавление)
    for (fkey, tkey), mod in list(graph.meta_routes.items()):
        f_act = active_weights.get(fkey, 0.0)
        if f_act <= 0:
            continue
        if tkey in out:
            out[tkey] = out[tkey] + f_act * mod
    return out


def key_meta_mod(edge_key, active_weights):
    """Коэффициент «маршрута» от ребра: чем сильнее проводимость, тем влиятельнее.
    Один return: float (нормализованный 0..1)."""
    return 0.5  # фиксированный мета-множитель; можно обучать отдельно


def calculate_physics_loss(graph, target_energy=0.6):
    """PINN-фильтр: отклонение средней квадратичной энергии рёбер от константы.
    Один return: float (0 = физично)."""
    vals = list(graph.edges.values())
    if not vals:
        return 0.0
    mean_energy = sum(w * w for w in vals) / len(vals)
    return abs(mean_energy - target_energy)


def path_active_energies(graph, path_nodes):
    """Энергии рёбер вдоль пути (для физического контроля). Один return: list float."""
    energies = []
    for src, _p, _d, w in _edges_on_path(graph, path_nodes):
        energies.append(w)
    return energies


def try_extract_biometric_context(user_query, session_pulse=0.75):
    """Определяет стартовую «биометрию» эпохи из текста запроса (виртуальная):
    пульс растёт при длинном/восклицательном вопросе, GSR — при вопросительном.
    Один return: dict {pulse, gsr_stress, energy}."""
    q = user_query or ""
    pulse_modifier = 0.15 if ("!" in q or len(q) > 50) else 0.0
    return {
        "pulse": min(1.0, session_pulse + pulse_modifier),
        "gsr_stress": 0.65 if "?" in q else 0.40,
        "energy": 0.85,
    }


def try_route_pipeline(graph, user_query, chemistry=None, session_pulse=0.75,
                       target_energy=0.6, refractory_state=None):
    """Сквозной мыслительный контур на ЖИВОМ графе:
    биометрия → модулированные рёбра → роу-импульсы → синаптическое утомление
    → PINN-контроль → ответ. Один return: dict {signal, physics_loss, active_edges,
    physics_ok, answer}."""
    chem = chemistry or {"acetylcholine": 1.0, "serotonin": 1.0, "dopamine": 0.0}
    refr_state = refractory_state
    if refr_state is None:
        from algos.refractory import init_refractory_counters
        refr_state = init_refractory_counters(graph)
    bio = try_extract_biometric_context(user_query, session_pulse)
    modulated = compute_modulated_edges(graph,
                                        ach=chem.get("acetylcholine", 1.0),
                                        serotonin=chem.get("serotonin", 1.0),
                                        dopamine=chem.get("dopamine", 0.0))
    # роу-импульсы: активированные рёбра усиливают следующие по цепочке
    routed = propagate_meta_impulses(graph, modulated)
    # синаптическое утомление: уставшие рёбра временно теряют проводимость
    fatigued = apply_fatigue_to_weights(graph, refr_state)
    routed = {k: fatigued.get(k, v) for k, v in routed.items()}
    # обновляем счётчики утомления на следующую эпоху (по активированным рёбрам)
    activated_nodes = []
    for (s, p, d) in routed:
        if routed.get((s, p, d), 0.0) > 0.1:
            activated_nodes.extend([s, d])
    from algos.refractory import update_refractory_states
    refr_state = update_refractory_states(graph, refr_state, activated_nodes)
    # физический цензор: отклонение средней энергии от целевой, нормализованное
    # по масштабу реальных весов (иначе любой граф с весами>1 кажется «кашей»).
    loss = calculate_physics_loss(graph, target_energy)
    norm_scale = 1.0
    if graph.edges:
        mean_w = sum(w for w in graph.edges.values()) / len(graph.edges)
        mean_energy = sum(w * w for w in graph.edges.values()) / len(graph.edges)
        norm_scale = max(1.0, mean_energy, mean_w * mean_w)
    rel_loss = loss / norm_scale
    physics_ok = rel_loss <= 0.4
    # ответ = средневзвешенный сигнал проводимостей маршрута
    avg = 0.0
    if routed:
        avg = sum(w for w in routed.values()) / len(routed)
    signal = math.tanh(avg) * (0.5 + bio["pulse"] * 0.5)
    return {
        "signal": round(signal, 4),
        "physics_loss": round(loss, 4),
        "active_edges": len(routed),
        "physics_ok": physics_ok,
        "biometrics": bio,
        "answer": round(signal, 4) if physics_ok else None,
    }


if __name__ == "__main__":
    from knowledge_graph import KnowledgeGraph
    g = KnowledgeGraph()
    g.from_triples(_sample_triples() + [])  # без ТТЛ пока
    print("граф:", g.summary())
    print("порог (база):", round(_threshold_for(0, nor=0.2), 2))
    print("импульс от 'внимание':", fire(g, "внимание"))
    print("цепочка:", activate_chain(g, "внимание"))
    print("нуль-точка:", activate_chain(g, "квантовый"))