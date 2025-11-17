# Script de démarrage pour lancer FastAPI et React ensemble
# Usage: .\start.ps1

Write-Host "🚀 Démarrage de l'application AO Analyzer..." -ForegroundColor Green
Write-Host ""

# Vérifier que l'environnement virtuel existe
$venvPath = "..\.venv"
if (-not (Test-Path $venvPath)) {
    Write-Host "❌ Erreur: L'environnement virtuel n'existe pas à $venvPath" -ForegroundColor Red
    Write-Host "   Créez-le avec: python -m venv ..\.venv" -ForegroundColor Yellow
    exit 1
}

# Activer l'environnement virtuel
$activateScript = "$venvPath\Scripts\Activate.ps1"
if (-not (Test-Path $activateScript)) {
    Write-Host "❌ Erreur: Script d'activation introuvable à $activateScript" -ForegroundColor Red
    exit 1
}

# Vérifier que les dépendances sont installées
Write-Host "📦 Vérification des dépendances..." -ForegroundColor Cyan
& "$venvPath\Scripts\python.exe" -m pip show fastapi uvicorn > $null 2>&1
if ($LASTEXITCODE -ne 0) {
    Write-Host "   Installation des dépendances Python..." -ForegroundColor Yellow
    & "$venvPath\Scripts\python.exe" -m pip install -r requirements.txt
}

# Vérifier que node_modules existe
if (-not (Test-Path "frontend\node_modules")) {
    Write-Host "   Installation des dépendances Node.js..." -ForegroundColor Yellow
    Set-Location frontend
    npm install
    Set-Location ..
}

Write-Host ""
Write-Host "✅ Démarrage des serveurs..." -ForegroundColor Green
Write-Host ""

# Lancer FastAPI en arrière-plan
Write-Host "🔧 Démarrage de l'API FastAPI sur http://localhost:8000..." -ForegroundColor Cyan
$fastapiJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD
    & "$using:venvPath\Scripts\python.exe" -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload
}

# Attendre un peu pour que FastAPI démarre
Start-Sleep -Seconds 2

# Vérifier que FastAPI répond
$maxRetries = 10
$retryCount = 0
$apiReady = $false

while ($retryCount -lt $maxRetries -and -not $apiReady) {
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2 -ErrorAction Stop
        if ($response.StatusCode -eq 200) {
            $apiReady = $true
            Write-Host "✅ API FastAPI prête!" -ForegroundColor Green
        }
    } catch {
        $retryCount++
        Start-Sleep -Seconds 1
    }
}

if (-not $apiReady) {
    Write-Host "⚠️  L'API FastAPI n'a pas répondu dans les délais, mais le processus continue..." -ForegroundColor Yellow
}

# Lancer React/Vite
Write-Host "⚛️  Démarrage de React/Vite sur http://localhost:3002..." -ForegroundColor Cyan
Set-Location frontend
$reactJob = Start-Job -ScriptBlock {
    Set-Location $using:PWD\frontend
    npm run dev -- --host --port 3002
}
Set-Location ..

Write-Host ""
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host "✅ Les deux serveurs sont en cours de démarrage!" -ForegroundColor Green
Write-Host ""
Write-Host "📍 API FastAPI:  http://localhost:8000" -ForegroundColor White
Write-Host "📍 Frontend React: http://localhost:3002" -ForegroundColor White
Write-Host ""
Write-Host "💡 Pour arrêter les serveurs, fermez cette fenêtre ou appuyez sur Ctrl+C" -ForegroundColor Yellow
Write-Host "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━" -ForegroundColor Green
Write-Host ""

# Attendre que l'utilisateur appuie sur une touche ou Ctrl+C
try {
    Write-Host "Appuyez sur Ctrl+C pour arrêter les serveurs..." -ForegroundColor Gray
    while ($true) {
        Start-Sleep -Seconds 1
        
        # Vérifier si les jobs sont toujours actifs
        $fastapiState = Get-Job -Id $fastapiJob.Id -ErrorAction SilentlyContinue
        $reactState = Get-Job -Id $reactJob.Id -ErrorAction SilentlyContinue
        
        if ($fastapiState -and $fastapiState.State -eq "Failed") {
            Write-Host "❌ L'API FastAPI s'est arrêtée avec une erreur" -ForegroundColor Red
        }
        if ($reactState -and $reactState.State -eq "Failed") {
            Write-Host "❌ React/Vite s'est arrêté avec une erreur" -ForegroundColor Red
        }
    }
} catch {
    Write-Host ""
    Write-Host "🛑 Arrêt des serveurs..." -ForegroundColor Yellow
    
    # Arrêter les jobs
    Stop-Job -Job $fastapiJob, $reactJob -ErrorAction SilentlyContinue
    Remove-Job -Job $fastapiJob, $reactJob -ErrorAction SilentlyContinue
    
    # Arrêter les processus Node et Python liés
    Get-Process | Where-Object { 
        $_.ProcessName -eq "node" -or $_.ProcessName -eq "python" 
    } | Where-Object {
        $_.Path -like "*Test_Cursor*"
    } | Stop-Process -Force -ErrorAction SilentlyContinue
    
    Write-Host "✅ Serveurs arrêtés" -ForegroundColor Green
    exit 0
}

