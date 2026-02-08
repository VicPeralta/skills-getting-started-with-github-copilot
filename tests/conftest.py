"""
Test configuration and fixtures for FastAPI app tests
"""

import pytest
from fastapi.testclient import TestClient
from src.app import app


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def sample_activity_data():
    """Sample activity data for testing"""
    return {
        "description": "Test activity description",
        "schedule": "Mondays, 3:00 PM - 4:00 PM", 
        "max_participants": 5,
        "participants": ["test1@mergington.edu", "test2@mergington.edu"]
    }


@pytest.fixture(autouse=True)
def reset_activities():
    """Reset activities data before each test"""
    # Store original activities
    from src.app import activities
    original_activities = activities.copy()
    
    yield
    
    # Restore original activities after test
    activities.clear()
    activities.update(original_activities)