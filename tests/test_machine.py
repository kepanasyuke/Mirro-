# -*- coding: utf-8 -*-
"""Проверки малой машины в духе Z3: арифметика, переходы, остановка.

Запуск:  python tests/test_machine.py
"""
import unittest

from algos.machine import Machine


def sum_program(start, count, target):
    """Программа: сложить count чисел, начиная с адреса start, в адрес target."""
    return [
        ("load", target),        # 0
        ("add", start),          # 1
        ("store", target),       # 2
        ("load", start),         # 3
        ("add", 15),             # 4  адрес 15 держит единицу
        ("store", start),        # 5
        ("load", 14),            # 6  адрес 14 держит счётчик
        ("sub", 15),             # 7
        ("store", 14),           # 8
        ("load", 14),            # 9
        ("jz", 12),              # 10
        ("jmp", 0),              # 11
        ("halt",),               # 12
    ]


class TestArithmetic(unittest.TestCase):
    """Арифметика и память."""

    def test_addition(self):
        machine = Machine(4, {0: 2, 1: 3})
        result = machine.run([("load", 0), ("add", 1), ("store", 2), ("halt",)])
        self.assertEqual(result["memory"][2], 5)

    def test_multiplication(self):
        machine = Machine(4, {0: 6, 1: 7})
        result = machine.run([("load", 0), ("mul", 1), ("store", 2), ("halt",)])
        self.assertEqual(result["memory"][2], 42)

    def test_subtraction(self):
        machine = Machine(4, {0: 10, 1: 4})
        result = machine.run([("load", 0), ("sub", 1), ("store", 2), ("halt",)])
        self.assertEqual(result["memory"][2], 6)

    def test_load_unknown_address_is_zero(self):
        machine = Machine(2)
        result = machine.run([("load", 9), ("halt",)])
        self.assertEqual(result["acc"], 0)


class TestControl(unittest.TestCase):
    """Переходы и остановка."""

    def test_jump_skips_command(self):
        machine = Machine(2, {0: 7})
        result = machine.run([("jmp", 2), ("store", 0), ("load", 0), ("halt",)])
        self.assertEqual(result["acc"], 7)

    def test_jz_taken_when_zero(self):
        machine = Machine(2)
        result = machine.run([("jz", 2), ("load", 1), ("halt",)])
        self.assertEqual(result["halted"], True)
        self.assertEqual(result["pc"], 2)

    def test_loop_sums_range(self):
        machine = Machine(16, {0: 1, 14: 5, 15: 1})
        result = machine.run(sum_program(0, 5, 13))
        self.assertEqual(result["memory"][13], 15)

    def test_step_limit_stops_endless_loop(self):
        machine = Machine(2)
        result = machine.run([("jmp", 0)], limit=50)
        self.assertEqual(result["halted"], False)
        self.assertEqual(result["steps"], 50)

    def test_unknown_command_halts(self):
        machine = Machine(2)
        result = machine.run([("dance", 1)])
        self.assertEqual(result["halted"], True)


class TestState(unittest.TestCase):
    """Снимок состояния не портит машину."""

    def test_snapshot_is_copy(self):
        machine = Machine(3, {0: 1})
        snapshot = machine.run([("load", 0), ("halt",)])
        snapshot["memory"][0] = 99
        self.assertEqual(machine.memory[0], 1)

    def test_steps_counted(self):
        machine = Machine(2)
        result = machine.run([("load", 0), ("halt",)])
        self.assertEqual(result["steps"], 2)

    def test_initial_memory_kept(self):
        machine = Machine(8, {5: 12})
        self.assertEqual(machine.memory[5], 12)


if __name__ == "__main__":
    unittest.main()
