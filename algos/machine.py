# -*- coding: utf-8 -*-
"""Малая вычислительная машина в духе Z3: память, аккумулятор, счётчик команд.

Цузе строил машину, где есть лента памяти, регистр и переходы по условию.
Здесь то же самое, но настолько малое, чтобы всё можно было проверить в тестах:
команды `load / store / add / sub / mul / jmp / jz / halt`, память по адресам,
один аккумулятор. Этого хватает, чтобы исполнять планы вычислений без Python-кода.

Класс держит состояние, свободные функции только считают.
"""
OPERATIONS = ("load", "store", "add", "sub", "mul", "jmp", "jz", "halt")


class Machine:
    """Машина с памятью, аккумулятором и счётчиком команд."""

    __slots__ = ("memory", "acc", "pc", "halted", "steps", "externals", "error")

    def __init__(self, size=16, memory=None, externals=None):
        self.memory = {index: 0 for index in range(max(int(size), 0))}
        self.memory.update({int(key): int(value) for key, value in (memory or {}).items()})
        self.acc = 0
        self.pc = 0
        self.halted = False
        self.steps = 0
        self.externals = dict(externals or {})
        self.error = ""

    def _read(self, address):
        """Значение из памяти по адресу; неизвестный адрес считается нулём."""
        return int(self.memory.get(int(address), 0))

    def step(self, program):
        """Одна команда программы; False, если машина уже остановлена."""
        if self.halted or not isinstance(program, (list, tuple)):
            return False
        command = program[self.pc] if 0 <= self.pc < len(program) else None
        self.steps += 1
        if not isinstance(command, (list, tuple)) or not command:
            self.halted = True
            return False
        operation = str(command[0]).lower()
        argument = command[1] if len(command) > 1 else 0
        if operation == "load":
            self.acc = self._read(argument)
            self.pc += 1
        elif operation == "store":
            self.memory[int(argument)] = self.acc
            self.pc += 1
        elif operation == "add":
            self.acc += self._read(argument)
            self.pc += 1
        elif operation == "sub":
            self.acc -= self._read(argument)
            self.pc += 1
        elif operation == "mul":
            self.acc *= self._read(argument)
            self.pc += 1
        elif operation == "jmp":
            self.pc = int(argument)
        elif operation == "jz":
            self.pc = int(argument) if self.acc == 0 else self.pc + 1
        elif operation == "call":
            self._call(command)
        else:
            self.halted = True
        return not self.halted

    def _call(self, command):
        """Внешняя операция: имя, описание аргументов, адрес результата."""
        name = str(command[1]) if len(command) > 1 else ""
        handler = self.externals.get(name)
        if handler is None:
            self.error = "нет внешней операции: " + name
            self.halted = True
        else:
            try:
                target = int(command[3]) if len(command) > 3 else 0
                self.memory[target] = handler(command[2] if len(command) > 2 else (), self.memory)
                self.pc += 1
            except Exception as error:
                self.error = str(error)
                self.halted = True
        return self.error

    def run(self, program, limit=10000):
        """Выполняет программу до HALT или до предела шагов; отдаёт снимок."""
        for _ in range(max(int(limit), 0)):
            if self.halted:
                break
            self.step(program)
        return self.snapshot()

    def snapshot(self):
        """Состояние машины на текущий момент."""
        return {"acc": self.acc, "pc": self.pc, "halted": self.halted,
                "steps": self.steps, "memory": dict(self.memory)}
