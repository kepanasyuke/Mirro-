# -*- coding: utf-8 -*-
"""Проверки транслятора: план исполняется как программа машины.

Запуск:  python tests/test_plan_machine.py
"""
import unittest

from algos import plan_machine


def arithmetic(operation, arguments):
    """Операции для проверки: сложение, умножение, вычитание, тождество."""
    if operation == "add":
        return arguments[0] + arguments[1]
    if operation == "mul":
        return arguments[0] * arguments[1]
    if operation == "sub":
        return arguments[0] - arguments[1]
    if operation == "same":
        return arguments[0]
    raise ValueError("нет операции " + str(operation))


class TestCompile(unittest.TestCase):
    """Компиляция плана в программу."""

    def test_step_becomes_call(self):
        program, addresses = plan_machine.compile_plan([("a", "add", [1, 2])])
        self.assertEqual(program[0][0], "call")
        self.assertEqual(program[0][2], ("add", (1, 2)))
        self.assertEqual(program[-1][0], "halt")

    def test_addresses_are_unique(self):
        _, addresses = plan_machine.compile_plan([("a", "same", [1]), ("b", "same", [2])])
        self.assertEqual(len(set(addresses.values())), 2)

    def test_reference_becomes_slot(self):
        program, addresses = plan_machine.compile_plan([("a", "same", [1]), ("b", "same", ["=a"])])
        self.assertEqual(program[1][2][1][0], ("slot", addresses["a"]))


class TestRun(unittest.TestCase):
    """План идёт по памяти машины и даёт те же значения."""

    def test_two_steps_with_reference(self):
        steps = [("a", "add", [2, 3]), ("b", "mul", ["=a", 4])]
        result = plan_machine.run_plan(steps, arithmetic)
        self.assertEqual(result["values"]["a"], 5)
        self.assertEqual(result["values"]["b"], 20)

    def test_steps_counted_by_machine(self):
        steps = [("a", "add", [1, 1]), ("b", "sub", ["=a", 1])]
        result = plan_machine.run_plan(steps, arithmetic)
        self.assertEqual(result["steps"], 3)

    def test_unknown_operation_stops_machine(self):
        result = plan_machine.run_plan([("a", "dance", [])], arithmetic)
        self.assertTrue(result["error"].startswith("нет операции"))

    def test_step_limit_respected(self):
        steps = [("v%d" % index, "same", [index]) for index in range(10)]
        result = plan_machine.run_plan(steps, arithmetic, limit=3)
        self.assertEqual(result["steps"], 3)
        self.assertEqual(result["values"], {"v0": 0, "v1": 1, "v2": 2})

    def test_empty_plan(self):
        result = plan_machine.run_plan([], arithmetic)
        self.assertEqual(result["values"], {})
        self.assertEqual(result["error"], "")


class TestRealOperations(unittest.TestCase):
    """План на настоящих понятиях проекта исполняется той же машиной."""

    def test_find_through_machine(self):
        steps = [("topic", "find", ["what is music?"]),
                 ("links", "neighbours", ["=topic"])]

        def operations(operation, arguments):
            from algos import concepts, concept_graph
            if operation == "find":
                found = concepts.find(arguments[0])
                return found["concept"]["name"] if found else None
            if operation == "neighbours":
                return list(concept_graph.neighbours(arguments[0], depth=1)[:2])
            return None

        result = plan_machine.run_plan(steps, operations)
        self.assertEqual(result["values"]["topic"], "music")
        self.assertEqual(result["error"], "")
        self.assertEqual(result["steps"], 3)


if __name__ == "__main__":
    unittest.main()
