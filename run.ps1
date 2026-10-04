# IM-VEST Intelligence: setup + jalankan. Pakai:  .\run.ps1   (tambah -Refresh untuk tarik ulang data)
param([switch]$Refresh, [switch]$Dev)
$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
$api = Join-Path $root "apps\api"
$web = Join-Path $root "apps\web"

if (-not (Get-Command uv -ErrorAction SilentlyContinue)) { throw "Butuh uv: https://docs.astral.sh/uv/ " }
if (-not (Get-Command npm -ErrorAction SilentlyContinue)) { throw "Butuh Node.js: https://nodejs.org" }

Push-Location $api
uv sync
if ($Refresh -or -not (Test-Path "imvest.db")) { Write-Host "Menarik data (harga, fundamental, berita)... ~3 menit"; uv run python -m app.refresh }
Pop-Location

Push-Location $web
if (-not (Test-Path "node_modules")) { npm install }
if (-not $Dev -and -not (Test-Path ".next\BUILD_ID")) { npm run build }
Pop-Location

$apiProc = Start-Process -PassThru -WindowStyle Hidden -WorkingDirectory $api -FilePath uv -ArgumentList "run", "uvicorn", "app.main:app", "--port", "8000"
$cmd = if ($Dev) { "dev" } else { "start" }
$webProc = Start-Process -PassThru -WindowStyle Hidden -WorkingDirectory $web -FilePath npm.cmd -ArgumentList "run", $cmd
Start-Sleep 6
Start-Process "http://localhost:3000"
Write-Host "Berjalan di http://localhost:3000  (Ctrl+C untuk berhenti)"
Write-Host "Login: admin@imvest.local / rm@imvest.local / investor@imvest.local, password dari IMVEST_SEED_PASSWORD (default: dev-password)"
try { Wait-Process -Id $apiProc.Id, $webProc.Id -ErrorAction SilentlyContinue; while ($true) { Start-Sleep 5 } }
finally { Stop-Process -Id $apiProc.Id, $webProc.Id -Force -ErrorAction SilentlyContinue; Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match "imvest-intelligence" -and $_.Name -match "node|python|uvicorn" } | ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue } }
