# -*- coding: utf-8 -*-
"""Регрессия маршрута «русский вопрос -> понятие -> ответ».

Прогоняет оценочный набор целиком: если правка в мосте, реестре или
описаниях ломает маршрут, тест падает с перечнем конкретных вопросов.
"""
import unittest

from tools.ru_eval import check
from tests.ru_eval_set import CASES


class TestRussianEval(unittest.TestCase):
    """Все вопросы набора должны проходить."""

    def test_all_cases_pass(self):
        failed = [item for item in (check(case) for case in CASES) if not item["ok"]]
        report = ["%s: ожидалось %s, найдено %s" % (item["query"], item["expected"], item["topic"])
                  for item in failed]
        self.assertEqual(failed, [], "провалы маршрута:\n" + "\n".join(report))

    def test_cases_are_well_formed(self):
        bad = [case for case in CASES if not isinstance(case, tuple) or len(case) != 3]
        self.assertEqual(bad, [])


if __name__ == "__main__":
    unittest.main()
