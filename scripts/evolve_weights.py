# -*- coding: utf-8 -*-
"""Эволюционное скрещивание весов знаниевого графа (улучшение №33).

Идея (нейроэволюция, читается с off-line графом):
  * берём живые веса KnowledgeGraph как «родителя-чемпиона»;
  * создаём ПОПУЛЯЦИЮ геномов-копий графа;
  * применяем мутацию и СКРЕЩИВАНИЕ весов рёбер;
  * оцениваем fitness = физичность (мал PINN-loss) − метаболический штраф
    (сумма квадратов энергий), с бонусом за стабильно связанный граф;
  * выживает элита; лучший паттерн записывается в память опыта графа.

Чистый Python, без numpy, атомарные функции, один return на функцию.
Запуск:  python scripts/evolve_weights.py [--generations N]
"""
import argparse, random as _rnd

# Ленивый доступ к графу, чтобы этот CLI работал и без поднятого сервера.
_rand = _rnd.Random(42)


def _get_global_graph():
    """Возвращает живой граф знаний. Один return: object."""
    import os, sys
    _home = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if _home not in sys.path:
        sys.path.insert(0, _home)
    from algos.knowledge_graph import kg
    if not kg.nodes:
        _seed = os.path.join(_home, "models", "knowledge_graph.pkl")
        if os.path.exists(_seed):
            kg.load(_seed)
    return kg


def genome_edges(graph):
    """Вектор весов рёбер графа. Один return: list."""
    return [float(w) for _, w in list(graph.edges.items())]


def set_genome_edges(graph, weights):
    """Применяет вектор весов к рёбрам графа (мутация графа на месте).
    Один return: int — число рёбер."""
    keys = list(graph.edges.keys())
    for i, w in enumerate(weights):
        if i >= len(keys):
            break
        key = keys[i]
        graph.edges[key] = float(w)
        if hasattr(graph, "_set_adj_weight"):
            graph._set_adj_weight(key[0], key[1], key[2], float(w))
            graph._set_adj_weight(key[2], key[1], key[0], float(w))
    return len(keys)


def physics_loss(graph, target_energy=0.6):
    """Отклонение средней квадратичной энергии от эталона. Один return: float."""
    vals = list(graph.edges.values())
    dev = 0.0
    if vals:
        mean_e = sum(w * w for w in vals) / len(vals)
        dev = abs(mean_e - target_energy)
    return dev


def fitness(graph, target_energy=0.6, penalty=0.05):
    """Приспособленность: малый PINN-loss + связанность − энергоплата.
    Один return: float (чем больше, тем лучше)."""
    loss = physics_loss(graph, target_energy)
    energy_penalty = penalty * sum(w * w for w in graph.edges.values())
    connectivity = min(0.5, len(graph._adj) / 1.0) if graph._adj else 0.0
    return connectivity - loss - energy_penalty


def make_population(graph, size=10):
    """Популяция как список копий весов графа. Один return: list[list]."""
    base = genome_edges(graph)
    return [list(base) for _ in range(size)]


def mutate_weights(weights, rate=0.3):
    """Мутация вектора весов. Один return: list (новый список)."""
    out = []
    for w in weights:
        nw = w
        if _rand.random() < rate:
            nw = w + _rand.uniform(-0.5, 0.5)
        if _rand.random() < 0.02:
            nw = _rand.uniform(0.05, 1.5)
        out.append(max(0.05, nw))
    return out


def crossover_weights(a, b):
    """Скрещивание двух векторов весов. Один return: list."""
    return [x if _rand.random() < 0.5 else y for x, y in zip(a, b)]


def evaluate(pop, graph, target_energy):
    """Оценка популяции: применяет каждый геном к графу, считает fitness.
    Возвращает сортирован slow список (fitness, weights). Один return: list."""
    scored = []
    for weights in pop:
        set_genome_edges(graph, weights)
        f = fitness(graph, target_energy)
        scored.append((f, list(weights)))
    scored.sort(key=lambda x: -x[0])
    return scored


def evolve_iteration(graph, pop, target_energy=0.6, elite=2):
    """Одна итерация эволюции: оценка → элита → скрещивание + мутация.
    Один return: list (новая популяция)."""
    scored = evaluate(pop, graph, target_energy)
    new_pop = [w for _f, w in scored[:elite]]
    while len(new_pop) < len(pop):
        a = scored[_rand.randint(0, len(scored) - 1)][1]
        b = scored[_rand.randint(0, len(scored) - 1)][1]
        child = crossover_weights(a, b)
        child = mutate_weights(child)
        new_pop.append(child)
    # возвращаем лучшие веса в граф
    set_genome_edges(graph, scored[0][1])
    return new_pop, scored[0][0]


def remember_best(graph, best_weights, max_experience=50):
    """Записывает лучший паттерн в память опыта графа. Один return: int."""
    if not hasattr(graph, "experience"):
        graph.experience = []
    if len(graph.experience) >= max_experience:
        graph.experience.pop(0)
    graph.experience.append(list(best_weights))
    return len(graph.experience)


def run(graph, generations=15, target_energy=0.6):
    """Полный прогон эволюции. Один return: dict-отчёт."""
    pop = make_population(graph)
    best_fit = None
    for g in range(generations):
        pop, best_fit = evolve_iteration(graph, pop, target_energy)
    n = remember_best(graph, genome_edges(graph))
    return {
        "generations": generations,
        "best_fitness": round(best_fit, 4),
        "edges": len(graph.edges),
        "nodes": len(graph.nodes),
        "experience": n,
    }


def main():
    ap = argparse.ArgumentParser(description="Эволюционное скрещивание весов графа знаний")
    ap.add_argument("--generations", type=int, default=15)
    args = ap.parse_args()
    graph = _get_global_graph()
    code = 0
    if not graph.edges:
        print("Граф пуст — нечего эволюционировать. Запустите Mirro, чтобы он наполнился.")
        code = 1
    else:
        report = run(graph, int(args.generations))
        print("Эволюция весов графа:")
        for k, v in report.items():
            print(f"  {k}: {v}")
        print("Лучший паттерн записан в память опыта круг.")
        try:
            from pathlib import Path
            _home = Path(__file__).resolve().parent.parent
            graph.save(_home / "models" / "knowledge_graph.pkl")
            print("Граф сохранён в models/knowledge_graph.pkl")
        except Exception as e:
            print(f"  (граф не сохранён: {e})")
    return code


if __name__ == "__main__":
    import sys
    sys.exit(main())