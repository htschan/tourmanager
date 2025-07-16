import os
import pytest
from fastapi.testclient import TestClient
from main import app

# Create an in-memory test database
TEST_DB = "test_database.db"
TEST_DATA_DIR = "test_data"

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables and directories before each test"""
    # Create test data directory if it doesn't exist
    if not os.path.exists(TEST_DATA_DIR):
        os.makedirs(TEST_DATA_DIR)
        print(f"Created test data directory: {TEST_DATA_DIR}")

    # Set test environment variables
    test_env = {
        "ENV": "test",  # Tell the app we're in test mode
        "JWT_SECRET_KEY": "test-secret-key-for-testing",
        "DATABASE_PATH": ":memory:",  # Use in-memory database for tests
        "PORT": "8000",
        "DATA_DIR": TEST_DATA_DIR  # Set the data directory for tests
    }
    
    # Store original environment
    orig_env = {key: os.environ.get(key) for key in test_env}
    
    # Set test environment
    for key, value in test_env.items():
        os.environ[key] = value
    
    yield
    
    # Restore original environment
    for key, value in orig_env.items():
        if value is None:
            del os.environ[key]
        else:
            os.environ[key] = value

@pytest.fixture
def client():
    """Create a test client using the FastAPI app"""
    return TestClient(app)

def test_read_main(client):
    response = client.get("/")
    assert response.status_code == 200
