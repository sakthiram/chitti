"""Unit tests for CLI"""

import pytest
from click.testing import CliRunner
from unittest.mock import patch, MagicMock
from chitti.cli import cli, service
from chitti.hookspecs import PromptResponse
from chitti.services import ChittiService

service = ChittiService()

@pytest.fixture
def runner():
    return CliRunner()

@pytest.fixture
def mock_response():
    return PromptResponse(
        response="Test response",
        metadata={"model": "test-model", "provider": "test-provider"}
    )

class AsyncMock(MagicMock):
    async def __call__(self, *args, **kwargs):
        return super(AsyncMock, self).__call__(*args, **kwargs)

def test_prompt_command(runner, mock_response):
    """Test non-streaming prompt command"""
    mock = AsyncMock()
    mock.return_value = mock_response
    
    with patch('chitti.services.ChittiService.process_prompt', mock):
        result = runner.invoke(cli, ['prompt', '--no-stream', 'test prompt'])
        assert result.exit_code == 0
        assert "Test response" in result.output

def test_prompt_command_with_model(runner, mock_response):
    """Test prompt command with model"""
    mock = AsyncMock()
    mock.return_value = mock_response
    
    with patch('chitti.services.ChittiService.process_prompt', mock):
        result = runner.invoke(cli, ['prompt', '--no-stream', '--model', 'test-model', 'test prompt'])
        assert result.exit_code == 0
        assert "Test response" in result.output

def test_prompt_command_with_provider(runner, mock_response):
    """Test prompt command with provider"""
    mock = AsyncMock()
    mock.return_value = mock_response
    
    with patch('chitti.services.ChittiService.process_prompt', mock):
        result = runner.invoke(cli, ['prompt', '--no-stream', '--provider', 'test-provider', 'test prompt'])
        assert result.exit_code == 0
        assert "Test response" in result.output

class AsyncIteratorMock:
    def __init__(self, items):
        self.items = items

    def __aiter__(self):
        return self

    async def __anext__(self):
        try:
            return self.items.pop(0)
        except IndexError:
            raise StopAsyncIteration

def test_prompt_command_streaming(runner):
    """Test streaming prompt command"""
    mock = AsyncMock()
    mock.return_value = AsyncIteratorMock(["Hello", " ", "World"])
    
    with patch('chitti.services.ChittiService.process_prompt', mock):
        result = runner.invoke(cli, ['prompt', 'test prompt'])
        assert result.exit_code == 0
        assert "Hello World" in result.output

def test_list_providers_command(runner):
    """Test list-providers command"""
    with patch.object(service, 'list_providers') as mock_list:
        mock_list.return_value = ['provider1', 'provider2']
        result = runner.invoke(cli, ['list-providers'])
        assert result.exit_code == 0
        assert 'provider1' in result.output
        assert 'provider2' in result.output

def test_list_providers_command_error(runner):
    """Test list-providers command error handling"""
    with patch.object(service, 'list_providers') as mock_list:
        mock_list.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['list-providers'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_list_agents_command(runner):
    """Test list-agents command"""
    with patch.object(service, 'list_agents') as mock_list:
        mock_list.return_value = ['agent1', 'agent2']
        result = runner.invoke(cli, ['list-agents'])
        assert result.exit_code == 0
        assert 'agent1' in result.output
        assert 'agent2' in result.output

def test_list_agents_command_error(runner):
    """Test list-agents command error handling"""
    with patch.object(service, 'list_agents') as mock_list:
        mock_list.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['list-agents'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_provider_info_command(runner):
    """Test provider-info command"""
    with patch.object(service, 'get_provider_info') as mock_info:
        mock_info.return_value = {
            'name': 'test-provider',
            'description': 'Test description',
            'models': ['model1', 'model2']
        }
        result = runner.invoke(cli, ['provider-info', 'test-provider'])
        assert result.exit_code == 0
        assert 'test-provider' in result.output
        assert 'Test description' in result.output
        assert 'model1' in result.output
        assert 'model2' in result.output

def test_provider_info_command_error(runner):
    """Test provider-info command error handling"""
    with patch.object(service, 'get_provider_info') as mock_info:
        mock_info.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['provider-info', 'test-provider'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_agent_info_command(runner):
    """Test agent-info command"""
    with patch.object(service, 'get_agent_info') as mock_info:
        mock_info.return_value = {
            'name': 'test-agent',
            'description': 'Test description',
            'version': '1.0.0'
        }
        result = runner.invoke(cli, ['agent-info', 'test-agent'])
        assert result.exit_code == 0
        assert 'test-agent' in result.output
        assert 'Test description' in result.output
        assert '1.0.0' in result.output

def test_agent_info_command_error(runner):
    """Test agent-info command error handling"""
    with patch.object(service, 'get_agent_info') as mock_info:
        mock_info.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['agent-info', 'test-agent'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_set_default_provider_command(runner):
    """Test set-default-provider command"""
    with patch.object(service, 'set_default_provider') as mock_set:
        result = runner.invoke(cli, ['set-default-provider', 'test-provider'])
        assert result.exit_code == 0
        mock_set.assert_called_once_with('test-provider')
        assert "successfully" in result.output

def test_set_default_provider_command_error(runner):
    """Test set-default-provider command error handling"""
    with patch.object(service, 'set_default_provider') as mock_set:
        mock_set.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['set-default-provider', 'test-provider'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_set_default_model_command(runner):
    """Test set-default-model command"""
    with patch.object(service, 'set_default_model') as mock_set:
        result = runner.invoke(cli, ['set-default-model', 'test-provider', 'test-model'])
        assert result.exit_code == 0
        mock_set.assert_called_once_with('test-provider', 'test-model')
        assert "successfully" in result.output

def test_set_default_model_command_error(runner):
    """Test set-default-model command error handling"""
    with patch.object(service, 'set_default_model') as mock_set:
        mock_set.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['set-default-model', 'test-provider', 'test-model'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_get_default_settings_command(runner):
    """Test get-default-settings command"""
    with patch.object(service, 'get_default_settings') as mock_get:
        mock_get.return_value = {
            'provider': 'test-provider',
            'model': 'test-model'
        }
        result = runner.invoke(cli, ['get-default-settings'])
        assert result.exit_code == 0
        assert 'test-provider' in result.output
        assert 'test-model' in result.output

def test_get_default_settings_command_error(runner):
    """Test get-default-settings command error handling"""
    with patch.object(service, 'get_default_settings') as mock_get:
        mock_get.side_effect = Exception("Test error")
        result = runner.invoke(cli, ['get-default-settings'])
        assert result.exit_code != 0
        assert "Test error" in result.output

def test_serve_command(runner):
    """Test serve command"""
    with patch('uvicorn.run') as mock_run:
        result = runner.invoke(cli, ['serve'])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            "chitti.server:app",
            host="127.0.0.1",
            port=8000,
            reload=True
        )

def test_serve_command_with_options(runner):
    """Test serve command with custom host and port"""
    with patch('uvicorn.run') as mock_run:
        result = runner.invoke(cli, ['serve', '--host', 'localhost', '--port', '8001'])
        assert result.exit_code == 0
        mock_run.assert_called_once_with(
            "chitti.server:app",
            host="localhost",
            port=8001,
            reload=True
        )

def test_serve_command_invalid_port(runner):
    """Test serve command with invalid port"""
    result = runner.invoke(cli, ['serve', '--port', '-1'])
    assert result.exit_code != 0
    assert "Invalid port number" in result.output

    result = runner.invoke(cli, ['serve', '--port', '65536'])
    assert result.exit_code != 0
    assert "Invalid port number" in result.output

def test_serve_command_error(runner):
    """Test serve command error handling"""
    with patch('uvicorn.run') as mock_run:
        mock_run.side_effect = Exception("Server error")
        result = runner.invoke(cli, ['serve'])
        assert result.exit_code != 0
        assert "Failed to start server" in result.output
        assert "Server error" in result.output

def test_install_command(runner):
    """Test install command"""
    result = runner.invoke(cli, ['install', 'test-agent'])
    assert result.exit_code == 0
    assert "Installing agent: test-agent" in result.output
    assert "Agent installed successfully" in result.output

def test_install_command_invalid_agent(runner):
    """Test install command with invalid agent"""
    result = runner.invoke(cli, ['install', 'invalid_agent'])
    assert result.exit_code != 0
    assert "Invalid agent name" in result.output

def test_install_command_empty_agent(runner):
    """Test install command with empty agent name"""
    result = runner.invoke(cli, ['install', ''])
    assert result.exit_code != 0
    assert "Invalid agent name" in result.output

def test_help(runner):
    """Test help command"""
    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert "Chitti - AI agent ecosystem" in result.output 