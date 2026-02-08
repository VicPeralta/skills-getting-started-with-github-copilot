"""
Tests for general FastAPI app functionality
"""

import pytest
from fastapi.testclient import TestClient


class TestAppConfiguration:
    """Tests for app configuration and metadata"""

    def test_app_title_and_description(self, client):
        """Test that the app has correct title and description"""
        # Check OpenAPI schema
        response = client.get("/openapi.json")
        assert response.status_code == 200
        
        openapi_schema = response.json()
        assert openapi_schema["info"]["title"] == "Mergington High School API"
        assert "extracurricular activities" in openapi_schema["info"]["description"]

    def test_docs_endpoint_accessible(self, client):
        """Test that API documentation is accessible"""
        response = client.get("/docs")
        assert response.status_code == 200

    def test_redoc_endpoint_accessible(self, client):
        """Test that ReDoc documentation is accessible"""
        response = client.get("/redoc")
        assert response.status_code == 200


class TestStaticFiles:
    """Tests for static file serving"""

    def test_static_html_served(self, client):
        """Test that static HTML files are served correctly"""
        response = client.get("/static/index.html")
        assert response.status_code == 200
        assert "text/html" in response.headers.get("content-type", "")

    def test_static_css_served(self, client):
        """Test that static CSS files are served correctly"""
        response = client.get("/static/styles.css")
        assert response.status_code == 200
        assert "text/css" in response.headers.get("content-type", "")

    def test_static_js_served(self, client):
        """Test that static JavaScript files are served correctly"""
        response = client.get("/static/app.js")
        assert response.status_code == 200
        assert "application/javascript" in response.headers.get("content-type", "") or \
               "text/javascript" in response.headers.get("content-type", "")

    def test_nonexistent_static_file(self, client):
        """Test request for non-existent static file"""
        response = client.get("/static/nonexistent.txt")
        assert response.status_code == 404


class TestDataIntegrity:
    """Tests for data integrity and state management"""

    def test_activities_data_structure_integrity(self, client):
        """Test that activities data maintains proper structure"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            # Check required fields exist
            required_fields = ["description", "schedule", "max_participants", "participants"]
            for field in required_fields:
                assert field in activity_data, f"Missing field {field} in activity {activity_name}"
            
            # Check data types
            assert isinstance(activity_data["description"], str)
            assert isinstance(activity_data["schedule"], str)
            assert isinstance(activity_data["max_participants"], int)
            assert isinstance(activity_data["participants"], list)
            
            # Check logical constraints
            assert activity_data["max_participants"] > 0
            assert len(activity_data["participants"]) <= activity_data["max_participants"]

    def test_participant_count_consistency(self, client):
        """Test that participant counts are consistent"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            participant_count = len(activity_data["participants"])
            max_participants = activity_data["max_participants"]
            
            # Participant count should never exceed maximum
            assert participant_count <= max_participants, \
                f"Activity {activity_name} has {participant_count} participants but max is {max_participants}"

    def test_email_format_in_participants(self, client):
        """Test that participant emails follow expected format"""
        response = client.get("/activities")
        activities = response.json()
        
        for activity_name, activity_data in activities.items():
            for email in activity_data["participants"]:
                assert "@" in email, f"Invalid email format: {email} in activity {activity_name}"
                assert email.endswith("@mergington.edu"), \
                    f"Email {email} doesn't match expected domain in activity {activity_name}"


class TestErrorHandling:
    """Tests for error handling and HTTP status codes"""

    def test_method_not_allowed(self, client):
        """Test that unsupported HTTP methods return 405"""
        response = client.put("/activities")
        assert response.status_code == 405

    def test_invalid_json_handling(self, client):
        """Test handling of invalid JSON in requests"""
        # This test depends on how FastAPI handles malformed requests
        # For signup endpoint, we use query parameters, so this tests general behavior
        response = client.post("/activities/Chess Club/signup")  # Missing email parameter
        # Should return 422 for validation error
        assert response.status_code == 422

    def test_url_encoding_handled_correctly(self, client):
        """Test that URL encoding is handled correctly"""
        # Test with URL-encoded activity name and email
        response = client.post(
            "/activities/Chess%20Club/signup?email=url%2Dtest@mergington.edu"
        )
        assert response.status_code == 200