#!/usr/bin/env python3
"""Mirro — главный запускатор. Запускает ядро, роутер и обучение."""
import sys, subprocess, time, os
from pathlib import Path

MIRRO = Path(r"D:\Mirro")

def run_script(name, script):
    print(f"\n[{name}] Запуск {script}...")
    result = subprocess.run([sys.executable, str(MIRRO / script)], capture_output=True, text=True)
    print(result.stdout[-2000:] if len(result.stdout) > 2000 else result.stdout)
    if result.stderr:
        print(f"STDERR: {result.stderr[-1000:]}")
    return result.returncode == 0

def main():
    print("""
╔══════════════════════════════════════════╗
║          MIRRO — v0.1                    ║
║    Эволюционная нейросеть знаний         ║
╚══════════════════════════════════════════╝
""")

    phase = sys.argv[1] if len(sys.argv) > 1 else "status"

    if phase == "ingest":
        print("📥 Фаза: инжест данных")
        run_script("INJECT", "scripts/ingest_data.py")

    elif phase == "serve":
        print("🚀 Фаза: запуск сервера")
        print("   Press Ctrl+C to stop")
        os.chdir(str(MIRRO))
        os.system(f'{sys.executable} core/mirro_core.py')

    elif phase == "status":
        # Show current state
        core_stats = Path(MIRRO / "core" / "stats.json")
        if core_stats.exists():
            import json
            stats = json.loads(core_stats.read_text("utf-8"))
            print(f"  Вызовов: {stats.get('calls', 0)}")
            print(f"  Примеров: {stats.get('total_examples', 0)}")
            print(f"  Источников: {stats.get('sources_count', 0)}")
        else:
            print("  (нет статистики — ещё не запускался)")

        proc_dir = MIRRO / "data" / "processed"
        if proc_dir.exists():
            print(f"\n  Кластеры знаний:")
            for f in sorted(proc_dir.glob("*.jsonl")):
                lines = sum(1 for _ in f.open(encoding="utf-8") if _.strip())
                print(f"    {f.stem:12} {lines:>8} примеров")

    elif phase == "all":
        print("🔄 Полный цикл: инжест → запуск")
        run_script("INGEST", "scripts/ingest_data.py")
        print("\n🚀 Запуск сервера...")
        os.chdir(str(MIRRO))
        os.system(f'{sys.executable} core/mirro_core.py')

    else:
        print(f"Неизвестная фаза: {phase}")
        print("Использование: python mirro.py [ingest|serve|status|all]")

if __name__ == "__main__":
    main()