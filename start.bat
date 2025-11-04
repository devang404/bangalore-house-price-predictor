@echo off
REM Start the Flask app using the project's virtualenv (Windows cmd)
set VENV_PY=%~dp0\.venv\Scripts\python.exe
if not exist "%VENV_PY%" (
  echo .venv not found. Create it with: python -m venv .venv
  echo Then install requirements: .\.venv\Scripts\python.exe -m pip install -r requirements.txt
  exit /b 1
)
echo Starting app with %VENV_PY%
"%VENV_PY%" .\app.py
