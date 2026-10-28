# -*- coding: utf-8 -*-
"""
Mirro State Mirror — сохранить отчёт обучения в git-репо как зеркало.
=====================================================================
Коммитит текущие runtime-данные (models/model_state.json, core/stats.json,
logs/session_report*.md) в репозиторий Mirro, чтобы любой, кто откроет
репозиторий (или панель «Паспорт из репо» в Мейсто), видел свежий отчёт
обучения — даже без локального сервера.

Запуск (вручную, когда нужно «сфотографировать» состояние обучения):
  python scripts/mirror_state_to_git.py            # коммит + пуш
  python scripts/mirror_state_to_git.py --no-push  # только коммит, без пуша

Внимание: коммитит ТОЛЬКО runtime-данные, которые уже трекаются git
(model_state.json, stats.json). Не трогает корпус, кэш и секреты.
"""
import argparse
import json
import subprocess
import sys
from datetime import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent


def _git(*args, check=True):
    r = subprocess.run(["git", "-C", str(ROOT), *args],
                       capture_output=True, text=True, encoding="utf-8", errors="replace")
    if check and r.returncode != 0:
        raise RuntimeError(f"git {' '.join(args)} => {r.returncode}: {r.stderr.strip() or r.stdout.strip()}")
    return r


def _summary():
    parts = []
    try:
        ms = json.loads((ROOT / "models" / "model_state.json").read_text("utf-8"))
        parts.append(f"trainer_cycles={ms.get('trainer_cycles')}")
        parts.append(f"accuracy={ms.get('trainer_accuracy')}")
        parts.append(f"auto_learned={ms.get('auto_learned')}")
    except Exception:
        pass
    return " · ".join(parts) or "state"


def main():
    ap = argparse.ArgumentParser(description="Mirro state mirror to git")
    ap.add_argument("--no-push", action="store_true", help="commit only, no push")
    args = ap.parse_args()

    files = ["models/model_state.json", "core/stats.json"]
    # Убедимся, что файлы трекаются (иначе добавленные данные не уйдут в репо)
    track = _git("ls-files").stdout.splitlines()
    staged = [f for f in files if f in track]

    if not staged:
        print("Ничего трекается для зеркала (model_state/stats не в git). Пропускаю.")
        return

    _git("add", *staged)
    msg = f"Runtime mirror: {_summary()} [{datetime.utcnow().isoformat(timespec='seconds')}]"
    _git("commit", "-m", msg)
    print("[mirror]", msg)

    if not args.no_push:
        import os
        env = {**os.environ, "GIT_TERMINAL_PROMPT": "0"}
        r = subprocess.run(["git", "-C", str(ROOT), "push", "origin", "main"],
                           capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
        print("[push]", (r.stdout or r.stderr).strip()[-300:])
    else:
        print("[push] пропущен (--no-push)")


if __name__ == "__main__":
    sys.exit(main())