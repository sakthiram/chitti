"""Unit tests for bash agent"""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException
from fastapi.testclient import TestClient
from examples.bash_agent.chitti_bash_agent.agent import BashAgent, CommandRequest

@pytest.fixture
def agent():
    """Create a bash agent instance"""
    return BashAgent()

@pytest.fixture
def client(agent):
    """Create a test client"""
    from fastapi import FastAPI
    app = FastAPI()
    app.include_router(agent.router)
    return TestClient(app)

def test_get_agent_name(agent):
    """Test get_agent_name method"""
    assert agent.get_agent_name() == "bash"

def test_get_agent_info(agent):
    """Test get_agent_info method"""
    info = agent.get_agent_info()
    assert info["name"] == "bash"
    assert "description" in info
    assert "version" in info
    assert "capabilities" in info

def test_get_commands(agent):
    """Test get_commands method"""
    commands = agent.get_commands()
    assert "run" in commands.commands
    assert "serve" in commands.commands

def test_get_router(agent):
    """Test get_router method"""
    router = agent.get_router()
    assert router.prefix == "/bash"
    assert router.tags == ["bash"]

def test_run_command_success(client):
    """Test successful command execution"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="command output",
            stderr=""
        )
        
        response = client.post(
            "/bash/run/",
            json={"command": "echo test"}
        )
        assert response.status_code == 200
        assert response.json()["output"] == "command output"

def test_run_command_with_workdir(client):
    """Test command execution with working directory"""
    with patch('subprocess.run') as mock_run, \
         patch('os.chdir') as mock_chdir:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="command output",
            stderr=""
        )
        
        response = client.post(
            "/bash/run/",
            json={
                "command": "echo test",
                "workdir": "/tmp"
            }
        )
        assert response.status_code == 200
        mock_chdir.assert_called_once_with("/tmp")

def test_run_command_invalid_workdir(client):
    """Test command execution with invalid working directory"""
    with patch('os.chdir') as mock_chdir:
        mock_chdir.side_effect = FileNotFoundError("Directory not found")
        
        response = client.post(
            "/bash/run/",
            json={
                "command": "echo test",
                "workdir": "/nonexistent"
            }
        )
        assert response.status_code == 500
        assert "Invalid working directory" in response.json()["detail"]

def test_run_command_not_found(client):
    """Test execution of non-existent command"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="command not found"
        )
        
        response = client.post(
            "/bash/run/",
            json={"command": "nonexistent"}
        )
        assert response.status_code == 400
        assert "Command not found" in response.json()["detail"]

def test_run_command_error(client):
    """Test command execution error"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message"
        )
        
        response = client.post(
            "/bash/run/",
            json={"command": "failing_command"}
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "error message"

def test_run_command_exception(client):
    """Test command execution with unexpected exception"""
    with patch('subprocess.run') as mock_run:
        mock_run.side_effect = Exception("Unexpected error")
        
        response = client.post(
            "/bash/run/",
            json={"command": "echo test"}
        )
        assert response.status_code == 500
        assert "Unexpected error" in response.json()["detail"]

def test_cli_run_command(agent):
    """Test CLI run command"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="command output",
            stderr=""
        )
        
        commands = agent.get_commands()
        result = commands.commands["run"].callback("echo test")
        mock_run.assert_called_once()

def test_cli_run_command_with_workdir(agent):
    """Test CLI run command with working directory"""
    with patch('subprocess.run') as mock_run, \
         patch('os.chdir') as mock_chdir:
        mock_run.return_value = MagicMock(
            returncode=0,
            stdout="command output",
            stderr=""
        )
        
        commands = agent.get_commands()
        result = commands.commands["run"].callback("echo test", workdir="/tmp")
        mock_chdir.assert_called_once_with("/tmp")
        mock_run.assert_called_once()

def test_cli_run_command_error(agent):
    """Test CLI run command with error"""
    with patch('subprocess.run') as mock_run:
        mock_run.return_value = MagicMock(
            returncode=1,
            stdout="",
            stderr="error message"
        )
        
        commands = agent.get_commands()
        result = commands.commands["run"].callback("failing_command")
        mock_run.assert_called_once()

def test_cli_serve_command(agent):
    """Test CLI serve command"""
    with patch('uvicorn.run') as mock_run:
        commands = agent.get_commands()
        result = commands.commands["serve"].callback(host="localhost", port=8001)
        mock_run.assert_called_once_with(
            "chitti_bash_agent.server:app",
            host="localhost",
            port=8001,
            reload=True
        ) 