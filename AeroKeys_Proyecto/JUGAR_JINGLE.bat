@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
  echo Debes ejecutar INSTALAR_WINDOWS.bat primero.
  pause
  exit /b 1
)
".venv\Scripts\python.exe" aerokeys.py --game
if errorlevel 1 pause
