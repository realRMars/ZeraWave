@echo off
setlocal
"%~dp0.venv\Scripts\python.exe" -X utf8 "%~dp0app\player.py"
if errorlevel 1 pause
