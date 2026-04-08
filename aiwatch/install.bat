@echo off
setlocal

echo.
echo ==========================================
echo  aiwatch  ^|  AI CLI approval notifier
echo ==========================================
echo.

REM Check Python is available
where python >nul 2>&1
if errorlevel 1 (
    echo [ERROR] Python not found in PATH.
    echo         Please install Python 3.8+ from https://python.org
    pause
    exit /b 1
)

echo [1/3] Installing aiwatch and Windows dependencies...
pip install -e ".[toml]"
if errorlevel 1 (
    echo [ERROR] pip install failed.
    pause
    exit /b 1
)

echo.
echo [2/3] Generating default bell sound...
python -c "from pathlib import Path; from aiwatch.bell_gen import generate_bell_wav; p=Path.home()/'.aiwatch'/'bell.wav'; generate_bell_wav(p); print(f'Bell saved to: {p}')"

echo.
echo [3/3] Verifying install...
aiwatch --version

echo.
echo ==========================================
echo  Done!  Quick-start:
echo.
echo    aiwatch run aider .
echo    aiwatch run claude .
echo    aiwatch run interpreter
echo ==========================================
echo.
pause
