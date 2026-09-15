@echo off
chcp 65001 >nul
title Mirro — Эволюционная нейросеть

echo ╔═══════════════════════════════════════════╗
echo ║        MIRRO — Эволюционная нейросеть      ║
echo ╚═══════════════════════════════════════════╝
echo.

:: Проверка Python
python --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [✗] Python не найден! Установи Python 3.10+
    pause
    exit /b 1
)
for /f "tokens=2" %%i in ('python --version 2^>^&1') do echo [✓] Python %%i

:: Проверка зависимостей
python -c "import zstandard" >nul 2>&1
if %errorlevel% neq 0 (
    echo [!] Установка zstandard...
    pip install zstandard
) else (
    echo [✓] zstandard
)

:: Проверка порта 3443
netstat -ano | findstr ":3443" >nul
if %errorlevel% equ 0 (
    echo [!] Порт 3443 занят — освобождаю...
    for /f "tokens=5" %%a in ('netstat -ano ^| findstr ":3443"') do (
        taskkill /f /pid %%a >nul 2>&1
    )
    timeout /t 2 /nobreak >nul
)
echo [✓] Порт 3443 свободен

:: Проверка каталогов
if not exist D:\Mirro\data\processed\ru.jsonl (
    echo [!] Первичные данные не найдены. Загрузка...
    python D:\Mirro\scripts\download_and_ingest.py
    python D:\Mirro\scripts\decompress_ingest.py
    python D:\Mirro\scripts\self_learn.py skills
)

echo.
echo [✓] Запуск Mirro...
echo     http://127.0.0.1:3443
echo     Press Ctrl+C to stop
echo.
python -u D:\Mirro\core\mirro_core.py

pause