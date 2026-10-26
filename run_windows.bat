@echo off
setlocal
cd /d "%~dp0"
title EvidenceLab Pro - Local Academic Prototype
echo =====================================================
echo  EvidenceLab Pro - Digital Evidence Workbench
echo  Academic prototype - not official FSL software
echo =====================================================

REM Reuse the existing virtual environment when available.
if exist ".venv\Scripts\python.exe" goto use_venv

REM Prefer the Windows Python launcher if installed.
where py >nul 2>nul
if not errorlevel 1 (
  echo [1/3] Creating virtual environment with py...
  py -3 -m venv .venv
  if not errorlevel 1 goto use_venv
)

REM Fall back to common python command.
where python >nul 2>nul
if not errorlevel 1 (
  echo [1/3] Creating virtual environment with python...
  python -m venv .venv
  if not errorlevel 1 goto use_venv
)

REM Fallback for this machine's observed Python installation path.
if exist "D:\Python\python.exe" (
  echo [1/3] Creating virtual environment with D:\Python\python.exe...
  "D:\Python\python.exe" -m venv .venv
  if not errorlevel 1 goto use_venv
)

echo ERROR: Could not locate a working Python installation.
echo Install Python from https://www.python.org/downloads/windows/
echo Ensure the installation includes pip, then run this file again.
pause
exit /b 1

:use_venv
echo [2/3] Installing required packages. First run needs internet...
".venv\Scripts\python.exe" -m pip install --upgrade pip
if errorlevel 1 goto failed
".venv\Scripts\python.exe" -m pip install -r requirements.txt
if errorlevel 1 goto failed

echo [3/3] Starting EvidenceLab Pro...
echo Keep this window open while using the application.
".venv\Scripts\python.exe" -m streamlit run app.py
if errorlevel 1 goto failed
goto end

:failed
echo.
echo The launcher stopped because of an error shown above.
echo Share a screenshot of the complete error if you need help.
pause
:end
endlocal
