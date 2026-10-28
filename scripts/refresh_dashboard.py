# -*- coding: utf-8 -*-
"""
Mirro Dashboard Refresh — автоматическое обновление данных дашборда.
=====================================================================
Пересобирает data/mirro_meysto_data.json (health + learn-report с локального
сервера + метаданные репо с GitHub) и встраивает свежий JSON прямо в
web/mirro-meysto-dashboard.html, чтобы карточки (включая «уровень сознания» φ)
показывали актуальные значения без ручного редактирования.

Токен доступа к серверу берётся из env MIRRO_TOKEN (если задан, иначе сервер
считается локальным). Без ключа DeepSeek — тоже ок, это не зависит от неё.

Запуск:
  python scripts/refresh_dashboard.py
Можно ставить в планировщик (Task Scheduler на Windows / cron на Linux) —
см. раздел «Расписание» ниже.
"""
import json
import os
import re
import sys
import urllib.request
import datetime
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA_FILE = ROOT / "data" / "mirro_meysto_data.json"
DASH_FILE = ROOT / "web" / "mirro-meysto-dashboard.html"
PHI_HIST_FILE = ROOT / "data" / "phi_history.json"

BASE = os.environ.get("MIRRO_BASE", "http://127.0.0.1:3443")
REPO = "https://api.github.com/repos/kepanasyuke/Mirro-"
TOKEN = os.environ.get("MIRRO_TOKEN", "").strip()


def _get(url, auth=False):
    """GET JSON. Один return: распарсенный dict/list или {'__error__': msg}."""
    headers = {"User-Agent": "Mirro-Dashboard"}
    if auth and TOKEN:
        headers["Authorization"] = "Bearer " + TOKEN
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as r:
            body = r.read().decode("utf-8", "replace")
            ct = r.headers.get("Content-Type", "")
            if "json" in ct or body.lstrip().startswith(("{", "[")):
                return json.loads(body)
            return body
    except Exception as e:
        return {"__error__": str(e)}


def _collect():
    """Собирает снимок. Один return: dict-отчёт."""
    report = {
        "generated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        "source": "local_server + github_repo",
    }
    report["health"] = _get(BASE + "/health", auth=True)
    report["learn_report"] = _get(BASE + "/v1/learn-report", auth=True)
    repo = _get(REPO)
    if isinstance(repo, dict):
        report["repo"] = {k: repo.get(k) for k in
                          ("full_name", "description", "default_branch",
                           "pushed_at", "stars_count", "forks_count", "open_issues_count")}
    else:
        report["repo"] = {"__error__": str(repo)}
    commits = _get(REPO + "/commits?per_page=5")
    report["repo_commits"] = commits if isinstance(commits, list) else {"__error__": str(commits)}
    return report


def _embed(report):
    """Встраивает снимок в дашборд. Один return: bool (изменено/успех)."""
    data_json = json.dumps(report, ensure_ascii=False)
    if not DASH_FILE.exists():
        print(f"[err] нет дашборда: {DASH_FILE}")
        return False
    html = DASH_FILE.read_text("utf-8")
    new_html = re.sub(r"const D = \{.*?\};\n", "const D = " + data_json + ";\n",
                      html, count=1, flags=re.S)
    if new_html == html:
        print("[warn] шаблон 'const D = {...}' не найден — файл мог измениться вручную.")
        return False
    DASH_FILE.write_text(new_html, "utf-8")
    return True


def _append_phi(report, max_points=720):
    """Дописывает точку phi в историю. Один return: list точек."""
    history = []
    if PHI_HIST_FILE.exists():
        try:
            history = json.loads(PHI_HIST_FILE.read_text("utf-8"))
        except Exception:
            history = []
    if not isinstance(history, list):
        history = []
    phi_raw = report.get("health", {}).get("algorithms", {}).get("consciousness_phi", {}).get("phi")
    if phi_raw is None:
        return history
    point = {"ts": report.get("generated_at"), "phi": round(float(phi_raw), 4)}
    if history and history[-1].get("ts") == point["ts"]:
        history[-1] = point
    else:
        history.append(point)
    if len(history) > max_points:
        history = history[-max_points:]
    try:
        PHI_HIST_FILE.write_text(json.dumps(history, ensure_ascii=False, indent=2), "utf-8")
    except Exception:
        pass
    return history


def main():
    print("MIRRO DASHBOARD REFRESH")
    report = _collect()
    # Подскажем причину при заборе health, чтобы не было тихого провала
    h = report.get("health") or {}
    if isinstance(h, dict) and h.get("__error__"):
        print(f"[info] health недоступен: {h['__error__']}: пишет прочие данные")
    if isinstance(report.get("repo"), dict) and not report["repo"].get("full_name"):
        print("[info] репозиторий не собрался полностью")

    # Сохраняем JSON-снимок для удобства
    DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
    DATA_FILE.write_text(json.dumps(report, ensure_ascii=False, indent=2), "utf-8")

    # История уровня сознания φ (тренд по времени)
    history = _append_phi(report)
    report["phi_history"] = history

    if _embed(report):
        phi = report.get("health", {}).get("algorithms", {}).get("consciousness_phi", {}).get("phi")
        print("[ok] дашборд обновлён; generated_at=%s; phi=%s" % (report["generated_at"], phi))
    else:
        print("[err] не встроил данные в дашборд")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())