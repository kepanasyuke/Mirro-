# -*- coding: utf-8 -*-
"""Планы вычислений: ответ собирается шагами, а не поиском готовой строки.

Идея от Цузе: машина исполняет план, а не «угадывает» ответ. План — список шагов
`(куда, операция, аргументы)`; каждая операция берёт аргументы (литералы или ссылки
`=имя` на уже посчитанное) и кладёт результат в переменную. В конце план рендерится
в текст шаблоном.

Операции по умолчанию — над понятиями и графом проекта:
`find` (понятие по запросу), `neighbours` (соседи темы), `entropy` (энтропия счётчиков).
Реестр операций подменяемый, поэтому план проверяется тестами без тяжёлых импортов.
"""
import re

_PLACEHOLDER = re.compile(r"\{([A-Za-zА-Яа-я0-9_]+)\}")


def _find(arguments, values):
    """Понятие по запросу: имя понятия или None."""
    from algos import concepts
    query = _resolve(arguments[0] if arguments else "", values)
    found = concepts.find(query) if isinstance(query, str) else None
    return found["concept"]["name"] if found else None


def _neighbours(arguments, values):
    """Соседи темы из графа определений: список имён."""
    from algos.concept_graph import neighbours
    topic = _resolve(arguments[0] if arguments else "", values)
    depth = int(_resolve(arguments[1], values)) if len(arguments) > 1 else 1
    return list(neighbours(topic, depth=depth)) if isinstance(topic, str) else []


def _entropy(arguments, values):
    """Энтропия по счётчикам, переданным словарём."""
    from algos.information import entropy
    counts = _resolve(arguments[0] if arguments else {}, values)
    return entropy(counts) if isinstance(counts, dict) else 0.0


def default_ops():
    """Реестр операций плана: имя -> функция(аргументы, значения)."""
    return {"find": _find, "neighbours": _neighbours, "entropy": _entropy}


def _resolve(argument, values):
    """Аргумент шага: ссылка вида «=имя» берётся из посчитанного."""
    result = argument
    if isinstance(argument, str) and argument.startswith("="):
        result = values.get(argument[1:])
    return result


def render(template, values):
    """Подставляет значения в шаблон вида «Тема {topic}, связано: {links}»."""
    def replace(match):
        value = values.get(match.group(1))
        return "" if value is None else str(value)
    return _PLACEHOLDER.sub(replace, template or "")


def explain(steps):
    """Человекочитаемый план: по строке на шаг."""
    result = []
    for target, operation, arguments in steps or ():
        shown = ", ".join(str(argument) for argument in arguments or ())
        result.append("%s = %s(%s)" % (target, operation, shown))
    return result


def run(steps, ops=None, values=None):
    """Исполняет план: значения, след и ошибки шагов.

    Ошибка одного шага не роняет план: она попадает в `errors`, шаг пропускается.
    """
    registry = default_ops()
    registry.update(ops or {})
    state = dict(values or {})
    trace = []
    errors = []
    for index, step in enumerate(steps or ()):
        target = step[0] if len(step) > 0 else "step%d" % index
        operation = step[1] if len(step) > 1 else ""
        arguments = step[2] if len(step) > 2 else ()
        function = registry.get(operation)
        if function is None:
            errors.append({"step": index, "operation": operation, "error": "нет операции"})
        else:
            try:
                state[target] = function(arguments, state)
            except Exception as error:
                errors.append({"step": index, "operation": operation, "error": str(error)})
        trace.append({"step": index, "target": target, "operation": operation})
    return {"values": state, "trace": trace, "errors": errors}


def answer(template, steps, ops=None, values=None):
    """Короткий путь: исполнить план и сразу отрендерить ответ."""
    executed = run(steps, ops=ops, values=values)
    return {"answer": render(template, executed["values"]),
            "errors": executed["errors"], "values": executed["values"]}
