@echo off
setlocal
cd /d "%~dp0"
echo === AEROKEYS - INSTALACION ===
python --version >nul 2>&1
if errorlevel 1 (
  echo ERROR: Windows no encuentra Python.
  echo Instala Python 3.11 y activa Add Python to PATH.
  echo Despues reinicia VS Code y vuelve a ejecutar este archivo.
  pause
  exit /b 1
)
python --version
python -m venv .venv
if errorlevel 1 goto error
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto error
echo.
echo === INSTALACION TERMINADA ===
echo Puedes abrir DEMO_JINGLE.bat o JUGAR_JINGLE.bat
pause
exit /b 0
:error
echo Error de instalacion. Copia el mensaje para revisarlo.
pause
exit /b 1
