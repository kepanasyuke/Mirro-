# -*- coding: utf-8 -*-
"""Транслятор плана в программу машины: шаги становятся командами.

План из `algos/plan.py` — список шагов `(куда, операция, аргументы)`. Здесь он
переводится в программу для `algos/machine.py`: каждая переменная получает адрес
в памяти, каждый шаг — команду `call`, которая вызывает операцию и кладёт результат
по адресу переменной. Ссылки `=имя` компилируются в ссылку на адрес, поэтому план
выполняется по памяти машины, а не по словарю Python.

Машина при этом не «делает вид»: она считает шаги, соблюдает предел и
останавливается, а ошибка внешней операции останавливает её и попадает в `error`.
"""
ADDRESS_BASE = 16


def slots(steps):
    """Адреса переменных плана: имя -> адрес в памяти машины."""
    result = {}
    for index, step in enumerate(steps or ()):
        name = step[0] if len(step) > 0 else "step%d" % index
        result[name] = ADDRESS_BASE + index
    return result


def argument_spec(argument, addresses):
    """Аргумент плана -> описание для машины: литерал или ссылка на адрес."""
    result = argument
    if isinstance(argument, str) and argument.startswith("="):
        result = ("slot", addresses.get(argument[1:], 0))
    return result


def compile_plan(steps):
    """Программа машины и таблица адресов: (program, addresses)."""
    addresses = slots(steps)
    program = []
    for index, step in enumerate(steps or ()):
        name = step[0] if len(step) > 0 else "step%d" % index
        operation = step[1] if len(step) > 1 else ""
        source = step[2] if len(step) > 2 else ()
        arguments = tuple(argument_spec(argument, addresses) for argument in source)
        program.append(("call", "plan", (operation, arguments), addresses[name]))
    program.append(("halt",))
    return program, addresses


def resolve(arguments, memory):
    """Подставляет значения из памяти вместо ссылок на адреса."""
    result = []
    for item in arguments or ():
        result.append(memory.get(item[1]) if isinstance(item, tuple) else item)
    return result


def plan_handler(operations):
    """Обработчик команды `plan`: имя операции, аргументы из памяти, результат."""
    def handle(spec, memory):
        operation, arguments = spec if isinstance(spec, tuple) and len(spec) == 2 else ("", ())
        return operations(operation, resolve(arguments, memory))
    return handle


def run_plan(steps, operations, size=128, limit=1000):
    """Исполняет план на машине: значения, ошибка, программа и число шагов."""
    from algos.machine import Machine
    program, addresses = compile_plan(steps)
    names = {address: name for name, address in addresses.items()}
    machine = Machine(size=size, externals={"plan": plan_handler(operations)})
    machine.run(program, limit=limit)
    executed = [command for command in program[:machine.steps] if command[0] == "call"]
    values = {names.get(command[3], command[3]): machine.memory.get(command[3])
              for command in executed}
    return {"values": values, "error": machine.error, "errors": [] if not machine.error else [machine.error],
            "program": program, "addresses": addresses, "steps": machine.steps}
