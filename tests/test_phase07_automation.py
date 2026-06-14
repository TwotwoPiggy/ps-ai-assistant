import pytest
import os
from unittest.mock import patch, MagicMock, mock_open

from backend.tools.ps_tools import play_action, execute_local_jsx, export_for_web, PhotoshopContext

@patch('backend.tools.ps_tools.execute_jsx')
def test_play_action(mock_execute_jsx):
    ctx = PhotoshopContext()
    mock_execute_jsx.return_value = {"success": True, "result": "success"}
    
    result = play_action(ctx, "Test Action", "Test Set")
    
    assert result["success"]
    assert "成功执行" in result["message"]

@patch('backend.tools.ps_tools.execute_jsx')
def test_execute_local_jsx_whitelist(mock_execute_jsx):
    ctx = PhotoshopContext()
    mock_execute_jsx.return_value = {"success": True, "result": "success"}
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data="var a=1;")):
            # Fake a safe path
            safe_path = os.path.join(os.path.dirname(__file__), "..", "backend", "resources", "scripts", "test.jsx")
            
            result = execute_local_jsx(ctx, safe_path)
            assert result["success"]

@patch('backend.tools.ps_tools.execute_jsx')
def test_execute_local_jsx_outside_whitelist(mock_execute_jsx):
    ctx = PhotoshopContext()
    mock_execute_jsx.return_value = {"success": True, "result": "success"}
    
    with patch('os.path.exists', return_value=True):
        with patch('builtins.open', mock_open(read_data="var a=1;")):
            
            result = execute_local_jsx(ctx, "C:\\Windows\\System32\\malicious.jsx")
            assert not result["success"]
            assert "风险" in result["error"]
            assert not mock_execute_jsx.called
            
            result_confirmed = execute_local_jsx(ctx, "C:\\Windows\\System32\\malicious.jsx", user_confirmed=True)
            assert result_confirmed["success"]
            assert mock_execute_jsx.called

@patch('backend.tools.ps_tools.execute_jsx')
def test_export_for_web(mock_execute_jsx):
    ctx = PhotoshopContext()
    # Mock get_doc
    ctx.get_doc = MagicMock()
    ctx.get_doc().Width = 1000
    ctx.get_doc().Height = 1000
    
    mock_execute_jsx.return_value = {"success": True, "result": "success"}
    
    with patch('os.path.expanduser', return_value="C:\\Users\\MockUser\\Desktop"):
        result = export_for_web(ctx)
        assert result["success"]
        assert mock_execute_jsx.called

