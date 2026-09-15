# -*- coding: utf-8 -*-
"""
Start-Mirro — программа запуска Mirro
=====================================
- Проверяет Python и зависимости
- Освобождает порт 3443
- Запускает Mirro (индексация ~4 мин)
- Ждёт готовности сервера
- Открывает браузер
- Показывает REST API команды
"""
import socket, subprocess, sys, os, time, webbrowser

MIRRO = r"D:\Mirro"
CORE = os.path.join(MIRRO, "core", "mirro_core.py")
PORT = 3443
URL = f"http://127.0.0.1:{PORT}"

def say(tag, msg, color=""):
    print(f"[{tag}] {msg}")

def check_python():
    try:
        v = subprocess.run([sys.executable, "--version"], capture_output=True, text=True, timeout=10)
        say("OK", v.stdout.strip() or v.stderr.strip())
    except Exception:
        say("X", "Python не найден. Установи Python 3.10+")
        sys.exit(1)

def check_deps():
    r = subprocess.run([sys.executable, "-c", "import zstandard"], capture_output=True, text=True)
    if r.returncode != 0:
        say("!", "Устанавливаю zstandard...")
        subprocess.run([sys.executable, "-m", "pip", "install", "zstandard", "--quiet"])
    else:
        say("OK", "zstandard (зависимости в порядке)")

def free_port():
    try:
        conn = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        conn.bind(("127.0.0.1", PORT))
        conn.close()
        return  # порт свободен
    except OSError:
        say("!", f"Порт {PORT} занят — освобождаю...")
        result = subprocess.run(["netstat", "-ano"], capture_output=True, text=True)
        for line in result.stdout.splitlines():
            if f":{PORT}" in line and "LISTENING" in line:
                pid = line.strip().split()[-1]
                try:
                    subprocess.run(["taskkill", "/f", "/pid", pid], capture_output=True)
                    say("OK", f"Процесс {pid} остановлен")
                except Exception:
                    pass
        time.sleep(2)

def check_data():
    ru = os.path.join(MIRRO, "data", "processed", "ru.jsonl")
    if not os.path.exists(ru):
        say("!", "Данные не найдены. Первичная загрузка...")
        subprocess.run([sys.executable, os.path.join(MIRRO, "scripts", "download_and_ingest.py")])
        subprocess.run([sys.executable, os.path.join(MIRRO, "scripts", "decompress_ingest.py")])
    else:
        size = os.path.getsize(ru) / 1e6
        say("OK", f"Данные на месте (ru.jsonl: {size:.0f} MB)")

def main():
    print()
    print("=" * 54)
    print("  MIRRO — Эволюционная нейросеть знаний")
    print("  Собственные алгоритмы · Без внешних API")
    print("=" * 54)
    print()

    check_python()
    check_deps()
    free_port()
    check_data()

    print()
    print("-" * 54)
    print("  Запуск Mirro... (первая индексация 3-5 минут)")
    print(f"  Сервер: {URL}")
    print("-" * 54)
    print()

    # Запуск в фоне
    log_out = os.path.join(MIRRO, "logs", "mirro_out.log")
    log_err = os.path.join(MIRRO, "logs", "mirro_err.log")
    os.makedirs(os.path.dirname(log_out), exist_ok=True)

    with open(log_out, "w") as fo, open(log_err, "w") as fe:
        proc = subprocess.Popen(
            [sys.executable, "-u", CORE],
            stdout=fo, stderr=fe, cwd=MIRRO
        )

    # Ожидание готовности
    say("...", "Ожидание сервера (до 6 минут)")
    ready = False
    for i in range(36):
        time.sleep(10)
        try:
            s = socket.create_connection(("127.0.0.1", PORT), timeout=2)
            s.close()
            ready = True
            print()
            say("OK", f"Сервер готов (через {(i+1)*10} сек)")
            break
        except OSError:
            pass

    if not ready:
        say("X", "Сервер не ответил за 6 минут. Логи:")
        try:
            print(open(log_err).read()[-2000:])
        except Exception:
            pass
        proc.kill()
        sys.exit(1)

    # Открыть браузер
    webbrowser.open(URL)
    print()
    print("=" * 54)
    print("  MIRRO РАБОТАЕТ")
    print(f"  Интерфейс: {URL}")
    print()
    print("  REST API (OpenAI-совместимый):")
    print(f"    POST {URL}/v1/chat/completions  — чат")
    print(f"    POST {URL}/v1/feedback         — лайк/дизлайк (обучение)")
    print(f"    POST {URL}/v1/self-learn       — самообучение")
    print(f"    GET  {URL}/health              — статус и метрики")
    print(f"    GET  {URL}/catalog.json        — каталог датасетов")
    print()
    print("  Алгоритмы включения:")
    print("    база — если ответ есть в 703k примерах")
    print("    интернет — биографии, новости, курс (Wikipedia)")
    print("    прямой — приветствия, математика")
    print("    learn — когда учишь её вручную")
    print("=" * 54)
    print()
    print("  Нажми Enter, чтобы остановить Mirro...")
    input()
    proc.kill()
    print("  Mirro остановлена.")

if __name__ == "__main__":
    main()