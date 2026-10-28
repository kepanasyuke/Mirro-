@echo off
REM Mirro dashboard auto-refresh wrapper (Windows).
REM Читает токен из env-переменной MIRRO_TOKEN (если задана глобально),
REM либо оставляет его пустым — тогда берутся данные без health (или локально).
setlocal
set PYTHONIOENCODING=utf-8
cd /d "%~dp0.."
python "scripts\refresh_dashboard.py"
exit /b %errorlevel%