@echo off
chcp 65001 >nul 2>&1
cd /d "%~dp0"
set PYTHONIOENCODING=utf-8
set PYTHONUTF8=1
set PYTHONUNBUFFERED=1

REM 静默模式: 被 start_silent.vbs 调用时设为 1, 跳过所有 pause
if "%PSAI_SILENT%"=="" set PSAI_SILENT=0

set PYTHON=python
if exist ".venv\Scripts\python.exe" set PYTHON=.venv\Scripts\python.exe
if exist "venv\Scripts\python.exe" set PYTHON=venv\Scripts\python.exe

if "%PSAI_SILENT%"=="0" (
    echo PS AI Assistant Launcher
    echo ========================
    echo Python: %PYTHON%
    %PYTHON% --version
    echo.
    echo Starting...
    echo.
)

%PYTHON% launcher.py %*
set EXITCODE=%errorlevel%

if "%PSAI_SILENT%"=="0" (
    echo.
    echo ========================
    echo Launcher exited ^(code %errorlevel%^)
    echo ========================
    pause
)
exit /b %EXITCODE%
