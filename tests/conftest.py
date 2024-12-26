"""Pytest configuration and shared fixtures"""

import os
import pytest
import tempfile
from pathlib import Path
import asyncio
from chitti.services import ChittiService
from httpx import AsyncClient
from chitti.server import app
from utils import MockProvider

@pytest.fixture(scope="session")
def test_dir():
    """Create a temporary directory for test files"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)

@pytest.fixture(scope="session")
def test_env():
    """Set up test environment variables"""
    # Save current environment
    old_env = dict(os.environ)
    
    # Set test environment variables
    os.environ.update({
        "CHITTI_TEST": "true",
        "AWS_ACCESS_KEY_ID": "test_key",
        "AWS_SECRET_ACCESS_KEY": "test_secret",
        "AWS_DEFAULT_REGION": "us-east-1"
    })
    
    yield
    
    # Restore original environment
    os.environ.clear()
    os.environ.update(old_env)

@pytest.fixture(autouse=True)
def setup_test_env(test_env):
    """Automatically use test environment for all tests"""
    pass 

@pytest.fixture
async def async_client():
    """Async client fixture"""
    async with AsyncClient(app=app, base_url="http://test") as client:
        yield client

@pytest.fixture
def client():
    """Synchronous client fixture"""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def service():
    """Service fixture"""
    return ChittiService()

@pytest.fixture
def mock_provider():
    """Mock provider fixture"""
    return MockProvider() 