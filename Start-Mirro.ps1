# Start-Mirro.ps1 — запуск Mirro с автооткрытием браузера
$ErrorActionPreference = "SilentlyContinue"

# Проверка Python
$pyVersion = python --version 2>&1
if (-not $pyVersion) {
    Write-Host "Python не найден. Установи Python 3.10+" -ForegroundColor Red
    exit 1
}
Write-Host "[OK] $pyVersion" -ForegroundColor Green

# Проверка zstandard
python -c "import zstandard" 2>$null
if ($LASTEXITCODE -ne 0) {
    Write-Host "[!] Устанавливаю zstandard..."
    python -m pip install zstandard --quiet
} else {
    Write-Host "[OK] zstandard" -ForegroundColor Green
}

# Освобождение порта
$processId = (netstat -ano | Select-String ":3443" | Select-String "LISTENING") -split '\s+' | Select-Object -Last 1
if ($processId -and $processId -ne 0) {
    Stop-Process -Id $processId -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}
Write-Host "[OK] Порт 3443 свободен" -ForegroundColor Green

Write-Host ""
Write-Host "┌───────────────────────────────────────────┐" -ForegroundColor Cyan
Write-Host "│  Mirro — Эволюционная нейросеть           │" -ForegroundColor Cyan
Write-Host "│  Запуск...                                │" -ForegroundColor Cyan
Write-Host "│  Первая загрузка: 3-4 минуты (индексация) │" -ForegroundColor Cyan
Write-Host "│  После запуска браузер откроется сам      │" -ForegroundColor Cyan
Write-Host "└───────────────────────────────────────────┘" -ForegroundColor Cyan
Write-Host ""

# Запуск в фоне
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = "python"
$psi.Arguments = "-u D:\Mirro\core\mirro_core.py"
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = "D:\Mirro\logs\mirro_out.log"
$psi.RedirectStandardError = "D:\Mirro\logs\mirro_err.log"
$psi.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$proc = [System.Diagnostics.Process]::Start($psi)
Write-Host "[OK] Mirro запущена (PID $($proc.Id))" -ForegroundColor Green

# Ожидание сервера
Write-Host "Ожидание сервера (до 5 минут)..." -ForegroundColor Yellow
$serverReady = $false
for ($i = 0; $i -lt 30; $i++) {
    Start-Sleep -Seconds 10
    try {
        $r = Invoke-WebRequest -Uri "http://127.0.0.1:3443/health" -TimeoutSec 3 -UseBasicParsing -ErrorAction Stop
        $serverReady = $true
        Write-Host "[OK] Сервер готов через $(($i+1)*10)с" -ForegroundColor Green
        break
    } catch {}
}

if (-not $serverReady) {
    Write-Host "[!] Сервер не ответил за 5 минут. Проверь логи:" -ForegroundColor Red
    Get-Content "D:\Mirro\logs\mirro_err.log" -Tail 5
    exit 1
}

# Открыть браузер
Write-Host "[OK] Открываю браузер..." -ForegroundColor Green
Start-Process "http://127.0.0.1:3443"

# Ожидание завершения
Write-Host ""
Write-Host "─────────────────────────────────────────────" -ForegroundColor Cyan
Write-Host "  Mirro работает! http://127.0.0.1:3443" -ForegroundColor Green
Write-Host "  Нажми любую клавишу чтобы остановить..." -ForegroundColor Cyan
Write-Host "─────────────────────────────────────────────" -ForegroundColor Cyan
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")

# Остановка
Stop-Process -Id $proc.Id -Force -ErrorAction SilentlyContinue
Write-Host "Mirro остановлена." -ForegroundColor Yellow