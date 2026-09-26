@echo off
setlocal
if "%~1"=="" set "STATE=blend"
if not "%~1"=="" set "STATE=%~1"
echo DreamWave state preview: %STATE%
call "%~dp0.venv\Scripts\python.exe" "%~dp0app\visuals\shader_test.py" --state "%STATE%"
endlocal
