@echo off
setlocal EnableExtensions
cd /d "%~dp0"

set "PROJECT_DIR=%~dp0"
set "APP_FILE=%PROJECT_DIR%app.py"
set "PYTHON="

rem Prefer a project virtual environment.
if exist "%PROJECT_DIR%.venv\Scripts\python.exe" set "PYTHON=%PROJECT_DIR%.venv\Scripts\python.exe"
if not defined PYTHON if exist "%PROJECT_DIR%venv\Scripts\python.exe" set "PYTHON=%PROJECT_DIR%venv\Scripts\python.exe"

rem Fall back to Python available on PATH.
if not defined PYTHON for /f "delims=" %%P in ('where python 2^>nul') do if not defined PYTHON set "PYTHON=%%P"

if not defined PYTHON (
    echo.
    echo [StudyBuddy] Python was not found.
    echo Please install Python 3 and try again.
    echo.
    pause
    exit /b 1
)

if not exist "%APP_FILE%" (
    echo.
    echo [StudyBuddy] app.py was not found in:
    echo %PROJECT_DIR%
    echo.
    echo Put this launcher in the same folder as app.py.
    echo.
    pause
    exit /b 1
)

rem Do not start a second app when port 8501 is already listening.
powershell -NoProfile -ExecutionPolicy Bypass -Command "if (Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue) { exit 0 } else { exit 1 }" >nul 2>&1
if errorlevel 1 (
    echo [StudyBuddy] Starting Streamlit...
    "%PYTHON%" -m streamlit run "%APP_FILE%" --server.port 8501 --server.address 127.0.0.1 --server.headless true --browser.gatherUsageStats false
) else (
    echo [StudyBuddy] Streamlit is already running on port 8501.
)
endlocal
