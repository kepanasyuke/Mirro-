@echo off
title Mirro — Эволюционная нейросеть
chcp 65001 >nul

echo ╔══════════════════════════════════════════════════╗
echo ║        MIRRO — Эволюционная нейросеть            ║
echo ║   Собственные алгоритмы · Без внешних API        ║
echo ╚══════════════════════════════════════════════════╝
echo.

:: Проверка Python
where python >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] Python не найден. Установи Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [✓] Python %%i

:: Проверка зависимостей
python -c "import zstandard" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Установка zstandard (нужен для датасетов)...
    pip install zstandard --quiet
) else (
    echo [✓] zstandard
    echo [✓] Все зависимости на месте (stdlib-only ядро)
)

:: Освобождение порта 3443
for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3443"') do (
    taskkill /f /pid %%a >nul 2>&1
)
echo [✓] Порт 3443 свободен

:: Проверка данных
if not exist "D:\Mirro\data\processed\ru.jsonl" (
    echo [!] Первичные данные не найдены. Загрузка...
    python D:\Mirro\scripts\download_and_ingest.py
    python D:\Mirro\scripts\decompress_ingest.py
)
:: else данные есть - отлично

echo.
echo ┌─────────────────────────────────────────┐
echo │  Mirro запускается...                   │
echo │  http://127.0.0.1:3443                  │
echo │  Первый запуск: ~4 минуты (индексация)  │
echo │  Ctrl+C — остановить                    │
echo └─────────────────────────────────────────┘
echo.

:: Запуск
python -u D:\Mirro\core\mirro_core.py

pause