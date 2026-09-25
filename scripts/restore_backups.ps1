# Restore encrypted Mirro backups (decimal cipher).
# Usage:  powershell -ExecutionPolicy Bypass -File scripts\restore_backups.ps1 "path\to\key document"
param([Parameter(Mandatory=$true)][string]$KeyPath)

$ErrorActionPreference = 'Stop'
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

if (-not (Test-Path -LiteralPath $KeyPath)) {
  Write-Error "Key document not found: $KeyPath"
  exit 1
}

New-Item -ItemType Directory -Force -Path restore | Out-Null

Write-Host "Decrypting stats.json ..."
& python scripts/cipher.py decode backups/stats.json.dec $KeyPath restore/stats.json
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host "Decrypting model_state.json ..."
& python scripts/cipher.py decode backups/model_state.json.dec $KeyPath restore/model_state.json
if ($LASTEXITCODE -ne 0) { exit 1 }

Write-Host ""
Write-Host "Restored into restore/. Compare hashes with live files to confirm:"
Get-FileHash -Algorithm SHA256 core/stats.json, models/model_state.json, restore/stats.json, restore/model_state.json |
  Format-Table Path, Hash -AutoSize