@echo off
setlocal
set "COSMIC_STATE=canvas"
if not "%~1"=="" set "COSMIC_STATE=%~1"
if not exist "%~dp0.venv\Scripts\python.exe" (
    echo DreamWave virtual environment was not found.
    pause
    exit /b 1
)
echo Cosmic with live system audio. Play music through your default output.
echo Close the visualizer window to finish. No test song is played automatically.
"%~dp0.venv\Scripts\python.exe" "%~dp0app\visuals\live_visual_test.py" --state "%COSMIC_STATE%"
set "COSMIC_EXIT=%ERRORLEVEL%"
if not "%COSMIC_EXIT%"=="0" pause
endlocal & exit /b %COSMIC_EXIT%
