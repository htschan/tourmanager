import os
import pytest
from fastapi.testclient import TestClient
from main import app

# Setup test environment
os.environ["JWT_SECRET_KEY"] = "test-secret-key"
os.environ["DATABASE_PATH"] = "/app/scripts/touren.db"
os.environ["PORT"] = "8000"

client = TestClient(app)

@pytest.fixture(autouse=True)
def setup_test_env():
    """Setup test environment variables before each test"""
    os.environ["JWT_SECRET_KEY"] = "test-secret-key"
    os.environ["DATABASE_PATH"] = "/app/scripts/touren.db"
    os.environ["PORT"] = "8000"
    yield
    # Cleanup after test if needed

def test_read_main():
    response = client.get("/")
    assert response.status_code == 200
