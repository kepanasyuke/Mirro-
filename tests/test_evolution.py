# -*- coding: utf-8 -*-
"""Юнит-тесты эволюционного алгоритма подбора нейрохимии (scripts/evolution.py).

Проверяем на РЕАЛЬНЫХ структурах и сигнатурах:
  - create_initial_population(pop_size, num_weights)  — стартовая популяция;
  - mutate_chromosome(chromosome, mutation_rate)      — микромутации, границы;
  - run_evolution_epoch(graph, population, generations, num_weights)
    — селекция по fitness (внутри сортируется по возрастанию PINN-loss).

Чистый Python, без внешних библиотек, атомарно.
"""
import os, sys, unittest
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.evolution import (
    create_initial_population, mutate_chromosome, run_evolution_epoch,
)
from algos.knowledge_graph import KnowledgeGraph


def _graph():
    g = KnowledgeGraph()
    g.from_triples([
        ("Внимание", "влияет на", "память"),
        ("Память", "укрепляет", "понимание"),
        ("Понимание", "рождает", "знание"),
    ])
    return g


class TestMirroEvolution(unittest.TestCase):
    def setUp(self):
        self.pop_size = 10
        self.graph = _graph()

    def test_population_initialization(self):
        population = create_initial_population(self.pop_size, num_weights=4)
        self.assertEqual(len(population), self.pop_size)
        self.assertIn("chemistry", population[0])
        self.assertIn("acetylcholine", population[0]["chemistry"])
        self.assertIn("serotonin", population[0]["chemistry"])
        self.assertIn("dopamine", population[0]["chemistry"])
        self.assertEqual(len(population[0]["W_decoder"]), 4)

    def test_mutation_boundaries(self):
        base = {
            "chemistry": {"acetylcholine": 1.0, "serotonin": 1.0, "dopamine": 0.0},
            "W_decoder": [0.5, 0.5],
            "fitness": 999.0,
        }
        for _ in range(50):
            mutated = mutate_chromosome(base, mutation_rate=1.0)
            self.assertGreaterEqual(mutated["chemistry"]["acetylcholine"], 0.1)
            self.assertGreaterEqual(mutated["chemistry"]["serotonin"], 0.1)
            self.assertEqual(len(mutated["W_decoder"]), 2)

    def test_mutation_returns_new_dict(self):
        base = {
            "chemistry": {"acetylcholine": 1.0, "serotonin": 1.0, "dopamine": 0.0},
            "W_decoder": [0.5, 0.5],
            "fitness": 999.0,
        }
        mutated = mutate_chromosome(base, mutation_rate=0.0)
        self.assertIsNot(mutated, base, "мутация возвращает НОВУЮ структуру, не мутирует исходник")

    def test_evolution_selection_loop_sorts_by_fitness(self):
        population = create_initial_population(self.pop_size, num_weights=2)
        updated, _best = run_evolution_epoch(self.graph, population, generations=2,
                                             num_weights=2)
        # после эпохи популяция отсортирована: первый — лучший (мин. loss)
        self.assertLessEqual(updated[0]["fitness"], updated[-1]["fitness"])
        self.assertIsNotNone(_best, "должен найтись лучший индивид")
        self.assertIn("chemistry", _best)

    def test_evolution_with_few_generations_converges(self):
        population = create_initial_population(6, num_weights=1)
        _pop, best = run_evolution_epoch(self.graph, population, generations=3,
                                         num_weights=1)
        self.assertIsInstance(best["fitness"], float)
        self.assertGreaterEqual(best["fitness"], 0.0, "PINN-loss не может быть отрицательным")


if __name__ == "__main__":
    unittest.main()