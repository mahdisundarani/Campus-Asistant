@echo off
set "VENV_PYTHON=%~dp0..\..\backend\.venv\Scripts\python.exe"
"%VENV_PYTHON%" "%~dp0server.py" %*
