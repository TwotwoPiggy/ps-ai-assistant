@echo off
setlocal

echo --- PS AI Assistant Uninstaller ---
echo This will completely remove PS AI Assistant and its data.
echo Press any key to confirm, or close this window to cancel.
pause >nul

:: Request admin privileges if not already elevated
net session >nul 2>&1
if %errorLevel% == 0 (
    goto :RunUninstall
) else (
    echo Requesting administrative privileges...
    powershell -Command "Start-Process '%~dpnx0' -Verb RunAs"
    exit /b
)

:RunUninstall
set "APP_DIR=%~dp0"
:: Remove trailing backslash if present
if "%APP_DIR:~-1%"=="\" set "APP_DIR=%APP_DIR:~0,-1%"

:: Create a temporary cleanup script to delete the app folder, since we can't delete the folder we're running from
set "TEMP_CLEANUP=%TEMP%\ps_ai_cleanup.bat"

echo @echo off > "%TEMP_CLEANUP%"
echo setlocal >> "%TEMP_CLEANUP%"
echo echo Stopping processes... >> "%TEMP_CLEANUP%"

:: Kill processes based on PID if lock file exists
echo if exist "%APP_DIR%\.pid" ( >> "%TEMP_CLEANUP%"
echo     for /F "tokens=*" %%%%A in (%APP_DIR%\.pid) do ( >> "%TEMP_CLEANUP%"
echo         taskkill /F /PID %%%%A ^>nul 2^>^&1 >> "%TEMP_CLEANUP%"
echo     ) >> "%TEMP_CLEANUP%"
echo ) >> "%TEMP_CLEANUP%"

:: Wait a moment for processes to exit
echo timeout /t 2 /nobreak ^>nul >> "%TEMP_CLEANUP%"

echo echo Removing Desktop Shortcut... >> "%TEMP_CLEANUP%"
echo set "SHORTCUT=%%USERPROFILE%%\Desktop\PS AI Assistant.lnk" >> "%TEMP_CLEANUP%"
echo if exist "%%SHORTCUT%%" del /q "%%SHORTCUT%%" >> "%TEMP_CLEANUP%"

echo echo Removing application files from %APP_DIR%... >> "%TEMP_CLEANUP%"
echo rd /s /q "%APP_DIR%" >> "%TEMP_CLEANUP%"

echo echo Uninstallation Complete. >> "%TEMP_CLEANUP%"
echo timeout /t 3 /nobreak ^>nul >> "%TEMP_CLEANUP%"
:: Self delete temp script
echo del "%%~f0" >> "%TEMP_CLEANUP%"

:: Execute the temp script and exit this one
start "" "%TEMP_CLEANUP%"
exit
