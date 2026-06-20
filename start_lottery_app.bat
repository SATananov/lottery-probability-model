@echo off
title Lottery Probability Model

cd /d "%~dp0"

echo Starting Lottery Probability Model...
echo.
echo Do not close this window while using the app.
echo Close this window with X when you want to stop the app.
echo.

REM If the app is already running, only open the browser once.
powershell -NoProfile -Command "$c=Get-NetTCPConnection -LocalPort 8501 -State Listen -ErrorAction SilentlyContinue; if($c){Start-Process 'http://localhost:8501'; exit 77}"
if %ERRORLEVEL%==77 exit /b

REM Open browser once after Streamlit has a few seconds to start.
start "" powershell -NoProfile -WindowStyle Hidden -Command "Start-Sleep -Seconds 3; Start-Process 'http://localhost:8501'"

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
) else (
    python -m streamlit run streamlit_app.py --server.port=8501 --server.headless=true
)

pause
