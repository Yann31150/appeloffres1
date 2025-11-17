@echo off
echo Activation de l'environnement virtuel...
call venv\Scripts\activate.bat
echo.
echo Lancement de l'application Streamlit...
streamlit run app.py
pause

