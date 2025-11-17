@echo off
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.
echo Lancement de l'API FastAPI...
uvicorn api:app --reload --port 8000
pause

