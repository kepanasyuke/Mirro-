# -*- coding: utf-8 -*-
"""Проверки планов: шаги, ссылки на посчитанное, шаблон, ошибки.

Запуск:  python tests/test_plan.py
"""
import unittest

from algos import plan


def fake_ops():
    """Подменные операции: детерминированные, без тяжёлых импортов."""
    return {
        "find": lambda arguments, values: "music" if "music" in str(arguments[0]) else None,
        "neighbours": lambda arguments, values: ["art", "melody"],
        "fail": lambda arguments, values: (_ for _ in ()).throw(RuntimeError("сломалось")),
    }


class TestRun(unittest.TestCase):
    """Исполнение шагов и переменные."""

    def test_steps_fill_values(self):
        steps = [("topic", "find", ["what is music?"]),
                 ("links", "neighbours", ["=topic"])]
        result = plan.run(steps, ops=fake_ops())
        self.assertEqual(result["values"]["topic"], "music")
        self.assertEqual(result["values"]["links"], ["art", "melody"])

    def test_trace_follows_steps(self):
        steps = [("a", "find", ["x"]), ("b", "neighbours", ["=a"])]
        result = plan.run(steps, ops=fake_ops())
        self.assertEqual([item["operation"] for item in result["trace"]], ["find", "neighbours"])

    def test_unknown_operation_is_error_not_crash(self):
        result = plan.run([("a", "dance", [])], ops=fake_ops())
        self.assertEqual(len(result["errors"]), 1)
        self.assertEqual(result["errors"][0]["operation"], "dance")

    def test_failing_operation_is_caught(self):
        result = plan.run([("a", "fail", [])], ops=fake_ops())
        self.assertEqual(len(result["errors"]), 1)
        self.assertIn("сломалось", result["errors"][0]["error"])

    def test_next_step_runs_after_error(self):
        steps = [("a", "fail", []), ("b", "find", ["music"])]
        result = plan.run(steps, ops=fake_ops())
        self.assertEqual(result["values"]["b"], "music")


class TestRender(unittest.TestCase):
    """Шаблон подставляет посчитанные значения."""

    def test_values_substituted(self):
        template = "Тема {topic}; связано: {links}"
        values = {"topic": "music", "links": ["art", "melody"]}
        self.assertEqual(plan.render(template, values),
                         "Тема music; связано: ['art', 'melody']")

    def test_missing_value_becomes_empty(self):
        self.assertEqual(plan.render("Тема {nothing}!", {}), "Тема !")

    def test_empty_template(self):
        self.assertEqual(plan.render("", {"a": 1}), "")


class TestAnswer(unittest.TestCase):
    """Полный путь план -> ответ."""

    def test_answer_rendered(self):
        steps = [("topic", "find", ["what is music?"]),
                 ("links", "neighbours", ["=topic"])]
        result = plan.answer("{topic}: связано с {links}", steps, ops=fake_ops())
        self.assertTrue(result["answer"].startswith("music: связано с"))
        self.assertEqual(result["errors"], [])

    def test_answer_with_error_keeps_plan(self):
        steps = [("broken", "fail", []), ("topic", "find", ["music"])]
        result = plan.answer("{topic}", steps, ops=fake_ops())
        self.assertEqual(result["answer"], "music")
        self.assertEqual(len(result["errors"]), 1)


class TestExplain(unittest.TestCase):
    """План читается человеком."""

    def test_explain_lines(self):
        steps = [("topic", "find", ["q"]), ("links", "neighbours", ["=topic", 2])]
        lines = plan.explain(steps)
        self.assertEqual(lines, ["topic = find(q)", "links = neighbours(=topic, 2)"])

    def test_explain_empty(self):
        self.assertEqual(plan.explain([]), [])


class TestRealOperations(unittest.TestCase):
    """Операции по умолчанию работают на настоящих базах проекта."""

    def test_find_real_topic(self):
        self.assertEqual(plan.run([("t", "find", ["what is music?"])])["values"]["t"], "music")

    def test_unknown_query_gives_none(self):
        self.assertIsNone(plan.run([("t", "find", ["zzz qqq"])])["values"]["t"])

    def test_entropy_real(self):
        result = plan.run([("h", "entropy", [{"a": 1, "b": 1}])])
        self.assertAlmostEqual(result["values"]["h"], 1.0, places=6)


if __name__ == "__main__":
    unittest.main()
