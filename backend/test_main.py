import os
import pytest
from fastapi.testclient import TestClient
from main import app

# Create an in-memory test database
TEST_DB = "test_database.db"

@pytest.fixture(autouse=True)
def setup_test_env(tmp_path):
    """Setup test environment variables before each test"""
    # Create a temporary database file
    test_db_path = str(tmp_path / TEST_DB)
    
    # Set test environment variables
    test_env = {
        "JWT_SECRET_KEY": "test-secret-key-for-testing",
        "DATABASE_PATH": test_db_path,
        "PORT": "8000"
    }
    
    # Backup existing env vars
    old_env = {key: os.environ.get(key) for key in test_env.keys()}
    
    # Set test env vars
    os.environ.update(test_env)
    
    yield
    
    # Restore original env vars
    for key, value in old_env.items():
        if value is None:
            os.environ.pop(key, None)
        else:
            os.environ[key] = value
            
    # Cleanup test database
    if os.path.exists(test_db_path):
        os.unlink(test_db_path)

# Create test client
client = TestClient(app)

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
