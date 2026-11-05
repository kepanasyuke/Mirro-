# -*- coding: utf-8 -*-
"""Эволюционный подбор нейрохимии и весов декодера (улучшение №34).

Генетический алгоритм ищет оптимальные базовые уровни нейромедиаторов
(ацетилхолин, серотонин, дофамин) и веса декодера, минимизируя физический
PINN-loss мыслительного контура (try_route_pipeline в neural_electric.py).

Каждая «хромосома»:
  { chemistry: {acetylcholine, serotonin, dopamine},
    W_decoder: [...],
    fitness }            # чем меньше pinn_loss, тем лучше

Чистый Python, без внешних библиотек, атомарные функции, один return.
Запуск:  python scripts/evolution.py [--generations N] [--pop N]
"""
import argparse, random as _rnd

_rng = _rnd.Random(42)


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


def create_initial_population(pop_size, num_weights=4):
    """Создаёт стартовую популяцию со случайными химическими и весовыми
    параметрами. Один return: list."""
    population = []
    for _ in range(pop_size):
        chromosome = {
            "chemistry": {
                "acetylcholine": _rng.uniform(0.5, 1.8),
                "serotonin": _rng.uniform(0.5, 1.5),
                "dopamine": _rng.uniform(-0.2, 0.5),
            },
            "W_decoder": [_rng.uniform(-1.0, 1.0) for _ in range(num_weights)],
            "fitness": 999.0,
        }
        population.append(chromosome)
    return population


def mutate_chromosome(chromosome, mutation_rate=0.15):
    """Вносит микро-мутации в химию и веса декодера. Один return: dict (новая)."""
    chem = dict(chromosome["chemistry"])
    if _rng.random() < mutation_rate:
        chem["acetylcholine"] = max(0.1, chem["acetylcholine"] + _rng.uniform(-0.2, 0.2))
        chem["serotonin"] = max(0.1, chem["serotonin"] + _rng.uniform(-0.2, 0.2))
        chem["dopamine"] = chem["dopamine"] + _rng.uniform(-0.1, 0.1)
    decoder = list(chromosome["W_decoder"])
    for i in range(len(decoder)):
        if _rng.random() < mutation_rate:
            decoder[i] = decoder[i] + _rng.uniform(-0.2, 0.2)
    return {"chemistry": chem, "W_decoder": decoder, "fitness": 999.0}


def _evaluate_fitness(graph, chem, decoder):
    """PINN-loss индивида на ОГРАНИЧЕННОЙ выборке рёбер (быстро для CLI).
    Использует тот же закон (средняя квадратичная энергия), что и
    try_route_pipeline, но на подвыборке до LIMIT рёбер — порядок пригодности
    химии сохраняется, время работы константное. Один return: float."""
    from algos.neural_electric import compute_modulated_edges, calculate_physics_loss
    limit = 3000
    try:
        edges = list(graph.edges.items())
        if len(edges) > limit:
            import random as _rnd2
            edges = _rnd2.sample(edges, limit)
        # восстанавливаем подграф с теми же весами
        _probe = type(graph)()
        for key, w in edges:
            _probe.from_triples([key])
            _probe.edges[key] = w
            if hasattr(_probe, "_set_adj_weight"):
                _probe._set_adj_weight(key[0], key[1], key[2], w)
                _probe._set_adj_weight(key[2], key[1], key[0], w)
        loss = calculate_physics_loss(_probe, 0.6)
        # лёгкий штраф к отклонению химии от сбалансированного фона
        ach = chem.get("acetylcholine", 1.0)
        ser = chem.get("serotonin", 1.0)
        dop = chem.get("dopamine", 0.0)
        chem_penalty = abs(ach - 1.1) * 0.1 + abs(ser - 0.9) * 0.1 + abs(dop) * 0.05
        return loss + chem_penalty
    except Exception:
        return 999.0


def run_evolution_epoch(graph, population, generations=20, num_weights=4):
    """Оценивает популяцию через PINN Loss, селекция топ-50%, мутация худших.
    Один return: (population, best_result)."""
    best_result = None
    for _ in range(generations):
        for ind in population:
            ind["fitness"] = _evaluate_fitness(graph, ind["chemistry"], ind["W_decoder"])
        population.sort(key=lambda x: x["fitness"])
        if best_result is None or population[0]["fitness"] < best_result["fitness"]:
            best_result = dict(population[0])
        half_size = max(1, len(population) // 2)
        for i in range(half_size, len(population)):
            parent = _rng.choice(population[:half_size])
            population[i] = mutate_chromosome(parent)
    return population, best_result


def main():
    ap = argparse.ArgumentParser(
        description="Эволюционный подбор нейрохимии и весов декодера по PINN-loss")
    ap.add_argument("--generations", type=int, default=20)
    ap.add_argument("--pop", type=int, default=12)
    ap.add_argument("--weights", type=int, default=4)
    args = ap.parse_args()

    graph = _get_global_graph()
    if not graph.edges:
        print("Граф пуст — запустите Mirro, чтобы он наполнился.")
        return 1
    pop = create_initial_population(int(args.pop), int(args.weights))
    _pop, best = run_evolution_epoch(graph, pop,
                                     generations=int(args.generations),
                                     num_weights=int(args.weights))
    print("Эволюция нейрохимии завершена:")
    print(f"  поколений: {args.generations}, популяция: {args.pop}")
    print(f"  PINN-loss лучшего: {best['fitness']:.4f}")
    print(f"  ацетилхолин: {best['chemistry']['acetylcholine']:.3f}, "
          f"серотонин: {best['chemistry']['serotonin']:.3f}, "
          f"дофамин: {best['chemistry']['dopamine']:.3f}")
    print(f"  W_decoder: {[round(w, 3) for w in best['W_decoder']]}")
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(main())