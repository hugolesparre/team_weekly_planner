@echo off
echo ========================================
echo   Team Weekly Planner - Setup and Run
echo ========================================
echo.

cd /d "%~dp0"

echo Current directory: %cd%
echo.

REM Check if virtual environment exists
if not exist "venv" (
    echo Creating virtual environment...
    python -m venv venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment.
        echo Make sure Python is installed and in your PATH.
        pause
        exit /b 1
    )
    echo Virtual environment created successfully.
    echo.
)

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    pause
    exit /b 1
)

REM Install/upgrade dependencies
echo.
echo Installing dependencies...
pip install --upgrade pip
pip install streamlit==1.52.0 pandas fpdf2

echo.
echo ========================================
echo   Starting Team Weekly Planner...
echo ========================================
echo.
echo Press Ctrl+C to stop the server.
echo.

streamlit run app.py

pause
