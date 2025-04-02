@echo off

:: Store the original path of the script
set "script_path=%~dp0"

:: Check for admin privileges
net session >nul 2>&1
if %errorlevel% neq 0 (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: Add your admin tasks below
cd /d %script_path%
python main.py