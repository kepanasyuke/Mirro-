# -*- coding: utf-8 -*-
"""Тихий сторож: ждёт до 08:00 и дописывает утреннюю сводку в отчёт.
Нужен, потому что Планировщик Windows на этой машине не запускает задачи
(0xC0000142 даже для cmd echo). Сторож живёт отдельным процессом.
"""
import datetime
import io
import os
import subprocess
import sys
import time

ROOT = r"D:\Mirro"
PY = sys.executable or "python"
MARK = os.path.join(ROOT, "NIGHT-RUN-REPORT.log")
TARGET_HOUR = 8


def log(text):
    """Дописать строку в журнал сторожа. Один return: None."""
    with io.open(MARK, "a", encoding="utf-8") as handle:
        stamp = datetime.datetime.now().strftime("%d.%m.%Y %H:%M:%S")
        handle.write("%s %s\n" % (stamp, text))


log("сторож запущен, ждёт %02d:00" % TARGET_HOUR)

while True:
    now = datetime.datetime.now()
    target = now.replace(hour=TARGET_HOUR, minute=0, second=0, microsecond=0)
    if target <= now:
        target += datetime.timedelta(days=1)
    wait = (target - now).total_seconds()
    log("следующая сводка %s, ждать %.0f с" % (target.strftime("%d.%m %H:%M"), wait))
    time.sleep(min(wait, 3600))
    if datetime.datetime.now() >= target:
        break

try:
    done = subprocess.run([PY, os.path.join(ROOT, "tools", "night_status.py")],
                          cwd=ROOT, capture_output=True, timeout=3600)
    text = (done.stdout or b"").decode("utf-8", "replace")
    log("сводка выполнена, код %s: %s" % (done.returncode, text.strip()[:200]))
except Exception as exc:
    log("сводка не выполнилась: %s" % exc)
