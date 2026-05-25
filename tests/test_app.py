"""
Tests for the FastAPI Activity Management Application
"""

import copy
import pytest
from fastapi.testclient import TestClient
from src.app import app, activities


@pytest.fixture
def client():
    """Create a test client for the FastAPI app"""
    return TestClient(app)


@pytest.fixture
def reset_activities():
    """Reset activities to initial state before each test"""
    initial_state = copy.deepcopy(activities)
    yield
    activities.clear()
    activities.update(initial_state)


class TestSignupEndpoint:
    """Tests for POST /activities/{activity_name}/signup"""

    def test_successful_signup(self, client, reset_activities):
        """Test successful signup for an activity"""
        response = client.post(
            "/activities/Chess Club/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        assert "Signed up" in response.json()["message"]
        assert "alex@mergington.edu" in activities["Chess Club"]["participants"]

    def test_signup_activity_not_found(self, client, reset_activities):
        """Test signup for non-existent activity"""
        response = client.post(
            "/activities/Nonexistent Activity/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_signup_already_registered(self, client, reset_activities):
        """Test signup when student is already registered"""
        response = client.post(
            "/activities/Chess Club/signup?email=michael@mergington.edu"
        )
        assert response.status_code == 400
        assert "already signed up" in response.json()["detail"]

    def test_signup_increases_participant_count(self, client, reset_activities):
        """Test that signup increases the participant count"""
        initial_count = len(activities["Programming Class"]["participants"])
        response = client.post(
            "/activities/Programming Class/signup?email=alex@mergington.edu"
        )
        assert response.status_code == 200
        assert len(activities["Programming Class"]["participants"]) == initial_count + 1

    def test_signup_updates_activities_endpoint(self, client, reset_activities):
        """Test that signup changes are reflected in GET /activities"""
        client.post("/activities/Chess Club/signup?email=alex@mergington.edu")
        response = client.get("/activities")
        assert response.status_code == 200
        assert "alex@mergington.edu" in response.json()["Chess Club"]["participants"]


class TestRemoveParticipantEndpoint:
    """Tests for DELETE /activities/{activity_name}/participants/{email}"""

    def test_successful_removal(self, client, reset_activities):
        """Test successful removal of a participant"""
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        assert "Removed" in response.json()["message"]
        assert "michael@mergington.edu" not in activities["Chess Club"]["participants"]

    def test_remove_activity_not_found(self, client, reset_activities):
        """Test removal from non-existent activity"""
        response = client.delete(
            "/activities/Nonexistent Activity/participants/alex@mergington.edu"
        )
        assert response.status_code == 404
        assert "Activity not found" in response.json()["detail"]

    def test_remove_participant_not_found(self, client, reset_activities):
        """Test removal of non-existent participant"""
        response = client.delete(
            "/activities/Chess Club/participants/nonexistent@mergington.edu"
        )
        assert response.status_code == 404
        assert "Participant not found" in response.json()["detail"]

    def test_removal_decreases_participant_count(self, client, reset_activities):
        """Test that removal decreases the participant count"""
        initial_count = len(activities["Chess Club"]["participants"])
        response = client.delete(
            "/activities/Chess Club/participants/michael@mergington.edu"
        )
        assert response.status_code == 200
        assert len(activities["Chess Club"]["participants"]) == initial_count - 1

    def test_removal_updates_activities_endpoint(self, client, reset_activities):
        """Test that removal changes are reflected in GET /activities"""
        client.delete("/activities/Chess Club/participants/michael@mergington.edu")
        response = client.get("/activities")
        assert response.status_code == 200
        assert "michael@mergington.edu" not in response.json()["Chess Club"]["participants"]


class TestSignupAndRemovalIntegration:
    """Integration tests for signup and removal together"""

    def test_signup_then_remove(self, client, reset_activities):
        """Test signing up then removing a participant"""
        # Signup
        signup_response = client.post(
            "/activities/Art Club/signup?email=alex@mergington.edu"
        )
        assert signup_response.status_code == 200
        assert "alex@mergington.edu" in activities["Art Club"]["participants"]

        # Remove
        remove_response = client.delete(
            "/activities/Art Club/participants/alex@mergington.edu"
        )
        assert remove_response.status_code == 200
        assert "alex@mergington.edu" not in activities["Art Club"]["participants"]

    def test_multiple_signups_and_removals(self, client, reset_activities):
        """Test multiple signup and removal operations"""
        emails = ["student1@mergington.edu", "student2@mergington.edu", "student3@mergington.edu"]
        activity = "Drama Club"

        # Sign up multiple students
        for email in emails:
            response = client.post(f"/activities/{activity}/signup?email={email}")
            assert response.status_code == 200

        assert len(activities[activity]["participants"]) == 5  # 2 existing + 3 new

        # Remove first two students
        for email in emails[:2]:
            response = client.delete(f"/activities/{activity}/participants/{email}")
            assert response.status_code == 200

        assert len(activities[activity]["participants"]) == 3  # 2 original + 1 remaining
