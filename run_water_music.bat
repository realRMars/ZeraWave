@echo off
setlocal
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo ZeraWave virtual environment was not found.
    pause
    exit /b 1
)
echo ZeraWave Water with live system audio.
echo Play music through your default output. Close the visualizer to finish.
"%~dp0.venv\Scripts\python.exe" "%~dp0app\visuals\live_visual_test.py" --state water
set "WATER_EXIT=%ERRORLEVEL%"
if not "%WATER_EXIT%"=="0" pause
endlocal & exit /b %WATER_EXIT%
