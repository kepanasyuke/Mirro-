#!/usr/bin/env python3
"""Mirro Start — запуск всех компонентов одной командой."""
import json, os, sys, time, subprocess, webbrowser, signal
from pathlib import Path
from http.server import HTTPServer, BaseHTTPRequestHandler
from datetime import datetime

MIRRO = Path(r"D:\Mirro")
CORE_SCRIPT = MIRRO / "core" / "mirro_core.py"
CATALOG = MIRRO / "data" / "catalog_phase1.json"
WEB = MIRRO / "web" / "index.html"

PORT = 3443
# Зависимости, которые проверяем
REQUIRED_PKGS = ["zstandard"]


def check_python():
    print("[1/4] Проверка Python...")
    print(f"      Python {sys.version.split()[0]}")


def check_deps():
    print("[2/4] Проверка зависимостей...")
    missing = []
    for pkg in REQUIRED_PKGS:
        try:
            __import__(pkg)
            print(f"      ✓ {pkg}")
        except ImportError:
            missing.append(pkg)
            print(f"      ✗ {pkg} отсутствует")
    if missing:
        print("      Устанавливаю...")
        for pkg in missing:
            subprocess.run([sys.executable, "-m", "pip", "install", pkg])
    else:
        print("      Все зависимости на месте")


def check_data():
    print("[3/4] Проверка данных...")
    proc_dir = MIRRO / "data" / "processed"
    total = 0
    if proc_dir.exists():
        for f in proc_dir.glob("*.jsonl"):
            cnt = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
            total += cnt
            if cnt > 0:
                print(f"      ✓ {f.stem}: {cnt} примеров")
    if total == 0:
        print("      ⚠ Данных нет! Запусти: python scripts/download_and_ingest.py")
    else:
        print(f"      Итого: {total:,} примеров")


def start_server():
    # Освободить порт
    try:
        import socket
        s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        s.bind(("127.0.0.1", PORT))
        s.close()
    except OSError:
        print(f"      Порт {PORT} занят — освобождаю...")
        import ctypes
        result = subprocess.run(
            ["netstat", "-ano"], capture_output=True, text=True
        )
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                try:
                    subprocess.run(["taskkill", "/f", "/pid", pid],
                                   capture_output=True)
                    print(f"      Убит процесс {pid}")
                except Exception:
                    pass
        time.sleep(2)

    print(f"[4/4] Запуск Mirro на http://127.0.0.1:{PORT}")
    print()
    print("      Открываю браузер...")
    webbrowser.open(f"http://127.0.0.1:{PORT}")
    print()
    print("      (Ctrl+C — остановить)")
    print()

    os.chdir(str(MIRRO))
    os.execv(sys.executable, [sys.executable, "-u", str(CORE_SCRIPT)])


if __name__ == "__main__":
    print()
    print("╔══════════════════════════════════════════════╗")
    print("║        MIRRO — Эволюционная нейросеть        ║")
    print("╚══════════════════════════════════════════════╝")
    print()
    check_python()
    check_deps()
    check_data()
    start_server()