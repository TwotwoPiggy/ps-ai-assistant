import pytest
import subprocess
import os

def test_install_script_exists():
    """Verify that the installation scripts exist."""
    assert os.path.exists("install.bat")
    assert os.path.exists("scripts/install.ps1")

# Since the installer mutates system state (installing python/node, creating shortcuts),
# full unit testing would require extensive mocking or a dedicated CI environment.
# We test the dry-run/syntax of the script by checking if powershell can parse it.
def test_install_script_syntax():
    """Verify that the install.ps1 script has valid syntax."""
    result = subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", 
         "Get-Command -Syntax .\\scripts\\install.ps1"],
        capture_output=True,
        text=True
    )
    assert result.returncode == 0
