# -*- coding: utf-8 -*-
"""Утренняя сводка по Mirro: прогоняет оценку и тесты и дописывает статус
в NIGHT-RUN-REPORT.md. Запускается Планировщиком Windows, руками — тоже можно.

Один проход: собрать статус, дописать блок в конец файла отчёта.
"""
import datetime
import io
import os
import subprocess
import sys

ROOT = r"D:\Mirro"
REPORT = os.path.join(ROOT, "NIGHT-RUN-REPORT.md")
PY = sys.executable or "python"


def run(args, timeout=1800):
    """Выполнить команду в корне проекта, вернуть (код, вывод). Один return: tuple."""
    try:
        done = subprocess.run(args, cwd=ROOT, capture_output=True, timeout=timeout)
        text = (done.stdout or b"").decode("utf-8", "replace")
        text += (done.stderr or b"").decode("utf-8", "replace")
        return done.returncode, text
    except Exception as exc:
        return -1, "ошибка запуска: %s" % exc


def tail(text, lines=8, width=120):
    """Последние строки вывода, обрезанные по ширине. Один return: str."""
    rows = [row[:width] for row in text.strip().splitlines() if row.strip()]
    return "\n".join(rows[-lines:]) or "(пусто)"


stamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M")

code_eval, out_eval = run([PY, "tools/ru_eval.py"])
code_tests, out_tests = run([PY, "-m", "pytest",
                             "tests/test_ru_bridge.py",
                             "tests/test_ru_eval.py",
                             "tests/test_core_helpers.py",
                             "-q", "-p", "no:cacheprovider", "--tb=line"])
code_head, out_head = run(["git", "rev-parse", "--short", "HEAD"])
code_origin, out_origin = run(["git", "rev-parse", "--short", "origin/main"])
code_log, out_log = run(["git", "log", "--oneline", "-8"])
code_cov, out_cov = run([PY, "tools/ru_coverage.py"])

block = [
    "",
    "## Проверка %s" % stamp,
    "",
    "**Оценка набора** (код %s):" % code_eval,
    "```",
    tail(out_eval, 6),
    "```",
    "",
    "**Тесты** (код %s):" % code_tests,
    "```",
    tail(out_tests, 4),
    "```",
    "",
    "**Покрытие:**",
    "```",
    tail(out_cov, 6),
    "```",
    "",
    "**Git:** локально `%s`, на сервере `%s`%s"
    % (out_head.strip(), out_origin.strip(),
       "" if out_head.strip() == out_origin.strip() else " — РАСХОЖДЕНИЕ"),
    "",
    "**Последние коммиты:**",
    "```",
    out_log.strip() or "(нет)",
    "```",
    "",
]

with io.open(REPORT, "a", encoding="utf-8") as handle:
    handle.write("\n".join(block))

print("дописано в %s" % REPORT)
