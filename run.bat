@echo off
REM One-click start for Windows: creates venv, installs packages, makes .env, runs the app.
cd /d "%~dp0"

if not exist venv (
    echo Creating virtual environment...
    python -m venv venv || (echo Python not found. Install Python 3.10+ first. & pause & exit /b 1)
)

call venv\Scripts\activate
echo Installing requirements...
pip install -q -r requirements.txt

if not exist .env (
    copy .env.example .env >nul
    echo.
    echo Created .env file. Open it and paste your GEMINI_API_KEY, then run run.bat again.
    notepad .env
    pause
    exit /b 0
)

streamlit run app.py
