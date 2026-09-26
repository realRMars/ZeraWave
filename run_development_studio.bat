@echo off
setlocal
"%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0app\visuals\studio.py"
if errorlevel 1 pause
