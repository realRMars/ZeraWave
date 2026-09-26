@echo off
rem Development preview: 40-second gather, planetary dwell, and release.
call "%~dp0run_state_preview.bat" transition
if errorlevel 1 pause
