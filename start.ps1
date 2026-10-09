# =============================================================================
# Sentinel-X - lance tout le projet pour la demo
#   1. les conteneurs Docker (MQTT, backend, frontend, IA vision, IA anomalies...)
#   2. le service camera directement sur le PC (seule facon d'utiliser la webcam USB)
#
# Utilisation (dans le dossier sentinel-x) :
#   powershell -ExecutionPolicy Bypass -File .\start.ps1            (webcam USB = 1)
#   powershell -ExecutionPolicy Bypass -File .\start.ps1 -Camera 0  (webcam du PC)
# =============================================================================
param([int]$Camera = 1)

Set-Location $PSScriptRoot

Write-Host "[1/2] Demarrage des conteneurs Docker..." -ForegroundColor Cyan
docker compose up -d
if ($LASTEXITCODE -ne 0) {
    Write-Host "Docker n'a pas demarre : Docker Desktop est-il lance ?" -ForegroundColor Red
    exit 1
}

Write-Host "[2/2] Demarrage de la camera (webcam $Camera)..." -ForegroundColor Cyan
Set-Location "$PSScriptRoot\camera"

if (Test-Path ".venv\Scripts\python.exe") {
    $py = ".venv\Scripts\python.exe"
} else {
    $py = "python"
}

& $py -m pip install -q -r requirements.txt

$env:CAMERA_INDEX = "$Camera"
$env:MQTT_HOST = "127.0.0.1"
$env:AI_URL = "http://127.0.0.1:8001/detect"

Write-Host ""
Write-Host "Tout est lance. Dashboard : http://localhost:5173" -ForegroundColor Green
Write-Host "Ctrl+C pour arreter la camera (les conteneurs restent actifs : docker compose down pour tout arreter)" -ForegroundColor Green
Write-Host ""

& $py -m uvicorn camera:app --host 0.0.0.0 --port 9000
