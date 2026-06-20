@echo off
title Lottery Probability Model

cd /d "%~dp0"

echo Starting Lottery Probability Model...
echo.
echo Do not close this window while using the app.
echo.

if exist ".venv\Scripts\python.exe" (
    ".venv\Scripts\python.exe" -m streamlit run streamlit_app.py
) else (
    python -m streamlit run streamlit_app.py
)

pause
