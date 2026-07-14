@echo off
setlocal
cd /d "%~dp0"

set PORT=8501
set URL=http://localhost:%PORT%

set CHROME=
if exist "%ProgramFiles%\Google\Chrome\Application\chrome.exe" set CHROME=%ProgramFiles%\Google\Chrome\Application\chrome.exe
if exist "%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe" set CHROME=%ProgramFiles(x86)%\Google\Chrome\Application\chrome.exe
if exist "%LocalAppData%\Google\Chrome\Application\chrome.exe" set CHROME=%LocalAppData%\Google\Chrome\Application\chrome.exe

if "%CHROME%"=="" (
  echo Google Chrome was not found.
  echo Install Chrome or start the app with: python -m streamlit run app.py
  pause
  exit /b 1
)

echo Starting Streamlit...
start "LOTTERY_STREAMLIT_SERVER" /min python -m streamlit run streamlit_app.py --server.port %PORT% --server.headless true --browser.gatherUsageStats false

echo Waiting for app...
timeout /t 5 /nobreak >nul

set PROFILE=%TEMP%\lottery-chrome-profile-%RANDOM%%RANDOM%
mkdir "%PROFILE%" >nul 2>nul

echo Opening Chrome app window...
echo Close the Chrome app window with X to stop the server.
"%CHROME%" --user-data-dir="%PROFILE%" --app="%URL%" --new-window --no-first-run --disable-extensions --disable-background-mode

echo Chrome closed. Stopping Streamlit...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :%PORT%') do (
  taskkill /PID %%a /F >nul 2>nul
)

rmdir /s /q "%PROFILE%" >nul 2>nul

echo Done.
timeout /t 1 /nobreak >nul
exit
