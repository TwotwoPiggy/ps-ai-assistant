import pytest
import subprocess
import os

def test_uninstaller_exists():
    """Verify that the uninstaller script exists."""
    assert os.path.exists("uninstall.bat")

def test_uninstaller_syntax():
    """Verify that uninstall.bat has valid syntax."""
    # Running a dry syntax check for batch files isn't straightforward without execution.
    # We can at least check if it contains expected keywords.
    with open("uninstall.bat", "r") as f:
        content = f.read()
    assert "TEMP_CLEANUP" in content
    assert "taskkill" in content
    assert "rd /s /q" in content
