@echo off
setlocal
echo ZeraWave geometric isolate preview
echo This launcher is hardcoded to geometric rooms. No extra argument needed.
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo ZeraWave virtual environment was not found.
    pause
    exit /b 1
)
"%~dp0.venv\Scripts\python.exe" "%~dp0app\visuals\shader_test.py" --state geometric
set "GEO_EXIT=%ERRORLEVEL%"
if not "%GEO_EXIT%"=="0" pause
endlocal & exit /b %GEO_EXIT%
