@echo off
setlocal

set "PROJECT_ROOT=%~dp0"
set "PYTHON_EXE=%PROJECT_ROOT%.venv\Scripts\python.exe"
set "LIVE_TEST=%PROJECT_ROOT%app\visuals\live_visual_test.py"

if not exist "%PYTHON_EXE%" (
    echo ZeraWave virtual environment was not found.
    echo Expected: "%PYTHON_EXE%"
    exit /b 1
)

if not exist "%LIVE_TEST%" (
    echo ZeraWave live visualizer was not found.
    echo Expected: "%LIVE_TEST%"
    exit /b 1
)

echo Starting ZeraWave live visualizer...
echo Play music through your system audio output, then close the visualizer window when finished.
echo.

"%PYTHON_EXE%" "%LIVE_TEST%"
set "EXIT_CODE=%ERRORLEVEL%"

if not "%EXIT_CODE%"=="0" (
    echo.
    echo ZeraWave exited with code %EXIT_CODE%.
)

endlocal & exit /b %EXIT_CODE%
