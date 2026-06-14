@echo off
setlocal

:: Request admin privileges if not already elevated
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunInstall
) else (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:RunInstall
echo Starting PS AI Assistant Installer...

:: Ensure scripts directory exists
if not exist "%~dp0scripts\install.ps1" (
    echo Error: scripts\install.ps1 not found!
    pause
    exit /b
)

:: Run the PowerShell install script
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0scripts\install.ps1"

echo.
echo Installation complete. Press any key to exit.
pause >nul
