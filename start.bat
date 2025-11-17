@echo off
REM Script de démarrage pour lancer FastAPI et React ensemble
REM Usage: start.bat

echo.
echo ========================================
echo   Démarrage de l'application AO Analyzer
echo ========================================
echo.

REM Vérifier que l'environnement virtuel existe
if not exist "..\.venv" (
    echo [ERREUR] L'environnement virtuel n'existe pas!
    echo Créez-le avec: python -m venv ..\.venv
    pause
    exit /b 1
)

REM Activer l'environnement virtuel et lancer FastAPI dans une nouvelle fenêtre
echo [1/2] Démarrage de l'API FastAPI sur http://localhost:8000...
start "FastAPI Server" cmd /k "cd /d %~dp0 && ..\.venv\Scripts\activate && python -m uvicorn api:app --host 0.0.0.0 --port 8000 --reload"

REM Attendre un peu pour que FastAPI démarre
timeout /t 3 /nobreak >nul

REM Lancer React/Vite dans une nouvelle fenêtre
echo [2/2] Démarrage de React/Vite sur http://localhost:3002...
cd frontend
start "React Dev Server" cmd /k "npm run dev -- --host --port 3002"
cd ..

echo.
echo ========================================
echo   ✅ Les serveurs sont en cours de démarrage!
echo ========================================
echo.
echo   📍 API FastAPI:  http://localhost:8000
echo   📍 Frontend React: http://localhost:3002
echo.
echo   💡 Deux fenêtres se sont ouvertes, une pour chaque serveur.
echo   💡 Fermez ces fenêtres pour arrêter les serveurs.
echo.
pause

