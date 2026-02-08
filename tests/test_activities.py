"""
Tests for FastAPI activities endpoints
"""

import pytest
from fastapi.testclient import TestClient


class TestRootEndpoint:
    """Tests for the root endpoint"""

    def test_root_redirects_to_static_index(self, client):
        """Test that root endpoint redirects to static/index.html"""
        response = client.get("/", follow_redirects=False)
        assert response.status_code == 307
        assert response.headers["location"] == "/static/index.html"


class TestActivitiesEndpoint:
    """Tests for the activities endpoint"""

    def test_get_activities_returns_all_activities(self, client):
        """Test getting all activities"""
        response = client.get("/activities")
        assert response.status_code == 200
        
        activities = response.json()
        assert isinstance(activities, dict)
        
        # Check that we have some default activities
        assert len(activities) > 0
        
        # Check structure of activities
        for activity_name, activity_data in activities.items():
            assert "description" in activity_data
            assert "schedule" in activity_data
            assert "max_participants" in activity_data
            assert "participants" in activity_data
            assert isinstance(activity_data["participants"], list)

    def test_activities_contain_expected_fields(self, client):
        """Test that activities contain all required fields"""
        response = client.get("/activities")
        activities = response.json()
        
        # Check a specific activity structure
        chess_club = activities.get("Chess Club")
        assert chess_club is not None
        assert chess_club["description"] == "Learn strategies and compete in chess tournaments"
        assert chess_club["schedule"] == "Fridays, 3:30 PM - 5:00 PM"
        assert chess_club["max_participants"] == 12
        assert isinstance(chess_club["participants"], list)


class TestActivitySignup:
    """Tests for activity signup functionality"""

    def test_successful_signup(self, client):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=newstudent@mergington.edu"
        )
        assert response.status_code == 200
        
        result = response.json()
        assert result["message"] == "Signed up newstudent@mergington.edu for Chess Club"
        
        # Verify the participant was added
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "newstudent@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_nonexistent_activity(self, client):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_duplicate_signup(self, client):
        """Test duplicate signup for same activity"""
        # First signup
        client.post("/activities/Chess Club/signup?email=duplicate@mergington.edu")
        
        # Attempt duplicate signup
        response = client.post(
            "/activities/Chess Club/signup?email=duplicate@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_already_registered_participant(self, client):
        """Test signup for participant already in the activity"""
        # Try to signup someone who's already registered
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert response.json()["detail"] == "Student already signed up"

    def test_signup_multiple_different_activities(self, client):
        """Test signing up for multiple different activities"""
        email = "multisport@mergington.edu"
        
        # Sign up for Chess Club
        response1 = client.post(f"/activities/Chess Club/signup?email={email}")
        assert response1.status_code == 200
        
        # Sign up for Programming Class
        response2 = client.post(f"/activities/Programming Class/signup?email={email}")
        assert response2.status_code == 200
        
        # Verify both signups
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert email in activities["Chess Club"]["participants"]
        assert email in activities["Programming Class"]["participants"]


class TestParticipantRemoval:
    """Tests for participant removal functionality"""

    def test_successful_participant_removal(self, client):
        """Test successful removal of a participant"""
        # First add a participant
        client.post("/activities/Chess Club/signup?email=toremove@mergington.edu")
        
        # Then remove them
        response = client.delete(
            "/activities/Chess Club/participants/toremove@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Removed toremove@mergington.edu from Chess Club"
        
        # Verify the participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "toremove@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_remove_existing_participant(self, client):
        """Test removing an existing participant"""
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        assert response.json()["message"] == "Removed michael@mergington.edu from Chess Club"
        
        # Verify participant was removed
        activities_response = client.get("/activities")
        activities = activities_response.json()
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_remove_participant_from_nonexistent_activity(self, client):
        """Test removing participant from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/participants/test@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Activity not found"

    def test_remove_nonexistent_participant(self, client):
        """Test removing participant who isn't registered"""
        response = client.delete(
            "/activities/Chess Club/participants/notregistered@mergington.edu"
        )
        assert response.status_code == 404
        assert response.json()["detail"] == "Participant not found"

    def test_remove_participant_updates_availability(self, client):
        """Test that removing a participant updates spot availability"""
        # First add a participant we can reliably remove
        test_email = "availability_test@mergington.edu"
        client.post(f"/activities/Chess Club/signup?email={test_email}")
        
        # Get initial participant count
        activities_response = client.get("/activities")
        initial_activities = activities_response.json()
        initial_count = len(initial_activities["Chess Club"]["participants"])
        
        # Remove the participant we just added
        client.delete(f"/activities/Chess Club/participants/{test_email}")
        
        # Check updated count
        updated_response = client.get("/activities")
        updated_activities = updated_response.json()
        final_count = len(updated_activities["Chess Club"]["participants"])
        
        assert final_count == initial_count - 1


class TestEdgeCases:
    """Tests for edge cases and error conditions"""

    def test_signup_with_special_characters_in_email(self, client):
        """Test signup with special characters in email"""
        response = client.post(
            "/activities/Chess Club/signup?email=test%2Bspecial@mergington.edu"
        )
        assert response.status_code == 200

    def test_activity_name_with_spaces(self, client):
        """Test operations with activity names containing spaces"""
        # Test signup
        response = client.post(
            "/activities/Programming Class/signup?email=spacetester@mergington.edu"
        )
        assert response.status_code == 200
        
        # Test removal
        response = client.delete(
            "/activities/Programming Class/participants/spacetester@mergington.edu"
        )
        assert response.status_code == 200

    def test_case_sensitivity(self, client):
        """Test case sensitivity in activity names"""
        response = client.post(
            "/activities/chess club/signup?email=case@mergington.edu"
        )
        # Should fail since activity names are case-sensitive 
        assert response.status_code == 404