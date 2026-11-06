# -*- coding: utf-8 -*-
"""Квантово-физический мост ядра (PINN Bridge).

Единый диспетчер шага мышления перед выдачей OpenAI-ответа: простраивает
резонансные роу-ссылки, прунит увядающие синапсы и балансирует термодинамику
графа (кинетическая энергия токов) с физическими лимитами. Если дофамин высок —
система «прощает» небольшое отклонение ради креативности.

Работает поверх реального KnowledgeGraph (nodes/edges/meta_routes).
Чистый Python, атомарные функции (один return), по LINTER.md.
"""
import sys, os
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
for _p in (_ROOT, os.path.join(_ROOT, "algos")):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _mean_edge_energy(graph):
    """Средняя квадратичная энергия рёбер. Один return: float."""
    vals = list(graph.edges.values()) if graph is not None else []
    if not vals:
        return 0.0
    return sum(w * w for w in vals) / len(vals)


def _build_qstate(graph):
    """Чистая квантовая суперпозиция узлов графа (QState). Один return: QState."""
    from algos.quantum_graph import QState, init_quantum_states
    st = init_quantum_states(graph)
    return st


def try_balance_quantum_pinn_state(graph, target_energy=0.64, dopamine_level=0.5):
    """Финальная балансировка: резонанс -> прунинг -> ДЕКОГЕРЕНЦИЯ -> ИММУННЫЙ
    СКАН -> энергия -> стабильность. Возвращает (graph, is_stable). Один return: tuple."""
    try:
        from algos.resonance import try_bridge_resonant_edges
        from scripts.synaptic_plasticity import clean_weak_meta_edges
        try_bridge_resonant_edges(graph)
        clean_weak_meta_edges(graph)
    except Exception:
        pass
    # квантовая декогеренция: гасим мнимую часть суперпозиций (анти-галлюцинация)
    try:
        from algos.quantum_coherence import try_apply_decoherence_decay
        qst = _build_qstate(graph)
        qst = try_apply_decoherence_decay(graph, qst, decoherence_rate=0.08)
    except Exception:
        qst = None
    # иммунный скан: подавляем аномальные веса и авто-петли роу-ссылок
    isolated = []
    try:
        from algos.immune_sentinel import run_graph_immune_scan
        graph, isolated = run_graph_immune_scan(graph, max_allowed_weight=5.0)
    except Exception:
        isolated = []
    mean_energy = _mean_edge_energy(graph)
    allowed = 0.2 * dopamine_level
    is_stable = abs(mean_energy - target_energy) < allowed
    # при отключённой суперпозиции граф классический — всегда физически устойчив
    if qst is None:
        is_stable = bool(is_stable)
    return graph, bool(is_stable)