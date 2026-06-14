$ErrorActionPreference = "Stop"

# Get script and project directories
$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Definition
$ProjectDir = Split-Path -Parent $ScriptDir
Set-Location $ProjectDir

Write-Host "Checking for Python..."
try {
    $pythonVersion = python --version 2>&1
    Write-Host "Found Python: $pythonVersion"
} catch {
    Write-Host "Python not found. Downloading Python 3.11..."
    $pythonInstaller = "$env:TEMP\python-3.11-amd64.exe"
    Invoke-WebRequest -Uri "https://www.python.org/ftp/python/3.11.8/python-3.11.8-amd64.exe" -OutFile $pythonInstaller
    Write-Host "Installing Python silently..."
    Start-Process -FilePath $pythonInstaller -ArgumentList "/quiet InstallAllUsers=0 PrependPath=1" -Wait
    Write-Host "Python installed successfully. Please ensure it is in your PATH."
}

Write-Host "Checking for Node.js..."
try {
    $nodeVersion = node -v 2>&1
    Write-Host "Found Node.js: $nodeVersion"
} catch {
    Write-Host "Node.js not found. Downloading..."
    $nodeInstaller = "$env:TEMP\node-v20-x64.msi"
    Invoke-WebRequest -Uri "https://nodejs.org/dist/v20.11.1/node-v20.11.1-x64.msi" -OutFile $nodeInstaller
    Write-Host "Installing Node.js silently..."
    Start-Process -FilePath "msiexec.exe" -ArgumentList "/i `"$nodeInstaller`" /qn" -Wait
    Write-Host "Node.js installed successfully."
}

Write-Host "Setting up Python virtual environment..."
if (-Not (Test-Path ".venv")) {
    python -m venv .venv
}

Write-Host "Building project dependencies using launcher.py..."
# Assumes python path is updated, but use .venv directly just in case
$pythonExe = if (Test-Path ".venv\Scripts\python.exe") { ".venv\Scripts\python.exe" } else { "python" }
Start-Process -FilePath $pythonExe -ArgumentList "launcher.py --build-only" -NoNewWindow -Wait

Write-Host "Creating desktop shortcut..."
$WshShell = New-Object -comObject WScript.Shell
$DesktopPath = [Environment]::GetFolderPath("Desktop")
$Shortcut = $WshShell.CreateShortcut("$DesktopPath\PS AI Assistant.lnk")
$Shortcut.TargetPath = "$ProjectDir\start_silent.vbs"
$Shortcut.WorkingDirectory = $ProjectDir
$Shortcut.IconLocation = "$ProjectDir\backend\store\icon.ico" # Assuming an icon exists, else it uses default
$Shortcut.Save()

Write-Host "Installation completed successfully."
