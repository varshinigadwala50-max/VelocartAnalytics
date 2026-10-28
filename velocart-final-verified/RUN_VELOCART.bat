@echo off
cd /d "%~dp0"
echo Installing/checking VeloCart dependencies...
py -m pip install -r requirements.txt
if errorlevel 1 (
  echo Could not install dependencies. Check your Python installation and internet connection.
  pause
  exit /b 1
)
echo Starting VeloCart shared database server...
py server.py
pause
