@echo off
echo ========================================
echo   Team Weekly Planner - Quick Start
echo ========================================
echo.

cd /d "%~dp0"

REM Check if virtual environment exists
if not exist "venv\Scripts\activate.bat" (
    echo ERROR: Virtual environment not found.
    echo Please run setup_and_run.cmd first to create it.
    echo.
    pause
    exit /b 1
)

call venv\Scripts\activate.bat
streamlit run app.py
