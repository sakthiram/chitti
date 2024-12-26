"""Integration tests for bash agent"""

import os
import pytest
from fastapi.testclient import TestClient
from chitti_bash_agent.agent import BashAgent
from chitti_bash_agent.server import app

@pytest.fixture
def client():
    """Create a test client"""
    return TestClient(app)

@pytest.fixture
def agent():
    """Create a bash agent instance"""
    return BashAgent()

def test_agent_info(agent):
    """Test agent information"""
    info = agent.get_agent_info()
    
    assert info["name"] == "bash"
    assert "description" in info
    assert "version" in info
    assert "capabilities" in info
    assert info["capabilities"]["command_execution"] is True

def test_agent_commands(agent):
    """Test CLI commands"""
    commands = agent.get_commands()
    
    # Check command group name
    assert commands.name == "bash"
    
    # Check available commands
    command_names = [cmd.name for cmd in commands.commands.values()]
    assert "run" in command_names
    assert "serve" in command_names

def test_run_command_success(client):
    """Test successful command execution"""
    response = client.post(
        "/bash/run/",
        json={
            "command": "echo 'test'",
            "workdir": None
        }
    )
    
    assert response.status_code == 200
    assert response.json()["output"].strip() == "test"

def test_run_command_error(client):
    """Test command execution error"""
    response = client.post(
        "/bash/run/",
        json={
            "command": "invalid_command",
            "workdir": None
        }
    )
    
    assert response.status_code == 400
    assert "command not found" in response.json()["detail"].lower()

def test_run_command_with_workdir(client, tmp_path):
    """Test command execution with working directory"""
    # Create a test file
    test_file = tmp_path / "test.txt"
    test_file.write_text("test content")
    
    response = client.post(
        "/bash/run/",
        json={
            "command": "cat test.txt",
            "workdir": str(tmp_path)
        }
    )
    
    assert response.status_code == 200
    assert response.json()["output"].strip() == "test content"

def test_run_command_with_invalid_workdir(client):
    """Test command execution with invalid working directory"""
    response = client.post(
        "/bash/run/",
        json={
            "command": "pwd",
            "workdir": "/nonexistent/directory"
        }
    )
    
    assert response.status_code == 500
    assert "no such file or directory" in response.json()["detail"].lower()

def test_router_configuration(agent):
    """Test router configuration"""
    router = agent.get_router()
    
    assert router.prefix == "/bash"
    assert "bash" in router.tags
    
    # Check route operations
    routes = router.routes
    assert len(routes) > 0
    
    # Debug route paths
    route_paths = [route.path for route in routes]
    print(f"\nAvailable routes: {route_paths}")
    
    # Find the run command route (FastAPI normalizes paths)
    run_routes = [route for route in routes if "/run" in route.path]
    assert len(run_routes) > 0, f"No run route found in paths: {route_paths}"
    assert "POST" in run_routes[0].methods 