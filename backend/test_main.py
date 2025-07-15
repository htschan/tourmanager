import os
import pytest
from fastapi.testclient import TestClient
from main import app

# Create an in-memory test database
TEST_DB = "test_database.db"

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables before each test"""
    # Set test environment variables
    test_env = {
        "ENV": "test",  # Tell the app we're in test mode
        "JWT_SECRET_KEY": "test-secret-key-for-testing",
        "DATABASE_PATH": ":memory:",  # Use in-memory database for tests
        "PORT": "8000"
    }
    
    # Store original environment
    original_env = {key: os.getenv(key) for key in test_env.keys()}
    
    # Set test environment
    for key, value in test_env.items():
        os.environ[key] = value
        
    yield
    
    # Restore original environment
    for key, value in original_env.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value
    
    # Backup existing env vars
    old_env = {key: os.environ.get(key) for key in test_env.keys()}
    
    # Set test env vars
    os.environ.update(test_env)
    
    yield
    
    # Environment cleanup is handled in the new fixture

# Create test client
client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
