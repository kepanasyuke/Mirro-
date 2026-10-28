# -*- coding: utf-8 -*-
"""
Register Windows Task Scheduler job to auto-refresh the Mirro dashboard.
=======================================================================
Создаёт задачу «MirroDashboardRefresh», которая запускает
scripts/refresh_dashboard.bat каждый час. Тогда дашборд обновляется
автоматически (health + learn-report + repo), а не вручную.

Запуск (от администратора):
  powershell -ExecutionPolicy Bypass -File scripts\schedule_dashboard.ps1 -Register
  powershell -ExecutionPolicy Bypass -File scripts\schedule_dashboard.ps1 -Unregister
"""
param([Parameter(Mandatory=$false)][string]$Mode = "Register")

$task = "MirroDashboardRefresh"
$bat  = Join-Path $PSScriptRoot "refresh_dashboard.bat"

if ($Mode -in @("Unregister","Remove","Delete")) {
    Unregister-ScheduledTask -TaskName $task -Confirm:$false -ErrorAction SilentlyContinue
    Write-Host "[ok] Задача '$task' удалена."
    exit 0
}

if (-not (Test-Path $bat)) {
    Write-Host "[err] Не найден запускатель: $bat"
    exit 1
}

$action  = New-ScheduledTaskAction -Execute $bat -WorkingDirectory (Split-Path $bat)
$trigger = New-ScheduledTaskTrigger -Once -At (Get-Date).AddMinutes(1) -RepetitionInterval (New-TimeSpan -Hours 1) -RepetitionDuration ([TimeSpan]::MaxValue)
$principal = New-ScheduledTaskPrincipal -UserId $env:USERNAME -RunLevel Limited -LogonType Interactive

Register-ScheduledTask -TaskName $task -Action $action -Trigger $trigger -Principal $principal -Force | Out-Null
Write-Host "[ok] Задача '$task' зарегистрирована: каждый час, первый запуск через 1 мин."
Write-Host "     Запускатель: $bat"
Write-Host "     Если сервер с токеном, задай системную env-переменную MIRRO_TOKEN."