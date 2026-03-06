"""
Test suite for Simplified Check-In Flow
Tests employee verification, registration, and access request endpoints
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hodler-preview.preview.emergentagent.com').rstrip('/')


class TestHealthAndRooms:
    """Health check and basic endpoints"""
    
    def test_health_endpoint(self):
        """API health check"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        print("PASS: Health endpoint returns healthy status")
    
    def test_get_rooms(self):
        """GET /api/rooms returns room list"""
        response = requests.get(f"{BASE_URL}/api/rooms")
        assert response.status_code == 200
        rooms = response.json()
        assert isinstance(rooms, list)
        assert len(rooms) > 0
        # Verify room structure
        room = rooms[0]
        assert "room_number" in room
        assert "room_type" in room
        print(f"PASS: Rooms endpoint returns {len(rooms)} rooms")


class TestEmployeeVerification:
    """Employee verification endpoints for check-in auto-fill"""
    
    def test_verify_valid_employee(self):
        """GET /api/employees/verify/{id} - valid employee returns name"""
        # Test with Aaron Frasco (2202373) - known valid employee
        response = requests.get(f"{BASE_URL}/api/employees/verify/2202373")
        assert response.status_code == 200
        data = response.json()
        assert data["valid"] == True
        assert data["name"] == "Aaron Frasco"
        assert data["employee_number"] == "2202373"
        print(f"PASS: Valid employee verification returns name: {data['name']}")
    
    def test_verify_invalid_employee(self):
        """GET /api/employees/verify/{id} - invalid employee returns 404"""
        response = requests.get(f"{BASE_URL}/api/employees/verify/9999999")
        assert response.status_code == 404
        data = response.json()
        assert "not found" in data["detail"].lower()
        print("PASS: Invalid employee returns 404 with appropriate message")


class TestGuestLookup:
    """Guest lookup endpoints"""
    
    def test_get_registered_guest(self):
        """GET /api/guests/{id} - registered guest returns info"""
        # Test with Aaron Frasco (2202373) - known registered guest
        response = requests.get(f"{BASE_URL}/api/guests/2202373")
        assert response.status_code == 200
        data = response.json()
        assert data["employee_number"] == "2202373"
        assert data["name"] == "Aaron Frasco"
        print(f"PASS: Registered guest lookup returns: {data['name']}")
    
    def test_get_unregistered_guest(self):
        """GET /api/guests/{id} - unregistered employee returns 404"""
        # Test with an employee who is in the list but not registered as guest
        response = requests.get(f"{BASE_URL}/api/guests/9999999")
        assert response.status_code == 404
        print("PASS: Unregistered guest returns 404")


class TestRequestEmployeeAccess:
    """Request employee access endpoint - Telegram notification"""
    
    def test_request_access_valid(self):
        """POST /api/request-employee-access - sends notification for unknown ID"""
        response = requests.post(
            f"{BASE_URL}/api/request-employee-access",
            json={"employee_number": "8888888"}  # Unknown ID
        )
        assert response.status_code == 200
        data = response.json()
        assert "Access request sent to admin" in data["message"]
        assert data["employee_number"] == "8888888"
        print("PASS: Request access endpoint works and confirms notification sent")
    
    def test_request_access_existing_employee(self):
        """POST /api/request-employee-access - returns 400 for existing employee"""
        response = requests.post(
            f"{BASE_URL}/api/request-employee-access",
            json={"employee_number": "2202373"}  # Already in system
        )
        assert response.status_code == 400
        data = response.json()
        assert "already exists" in data["detail"].lower()
        print("PASS: Request access for existing employee returns 400")


class TestCheckInEndpoint:
    """Check-in endpoint tests"""
    
    def test_checkin_unregistered_employee(self):
        """POST /api/checkin - unregistered employee returns 404"""
        response = requests.post(
            f"{BASE_URL}/api/checkin",
            json={
                "employee_number": "9999999",
                "room_number": "101",
                "check_in_date": "2026-03-02",
                "check_in_time": "15:00",
                "signature": "data:image/png;base64,test"
            }
        )
        assert response.status_code == 404
        data = response.json()
        assert "not registered" in data["detail"].lower()
        print("PASS: Check-in with unregistered employee returns 404")


class TestAutoVerifyFlow:
    """Tests for the auto-verify flow behavior"""
    
    def test_full_employee_lookup_flow(self):
        """Test the full lookup flow: employee list -> guest check"""
        # Step 1: Check if employee is in the approved list
        emp_response = requests.get(f"{BASE_URL}/api/employees/verify/2202373")
        assert emp_response.status_code == 200
        emp_data = emp_response.json()
        assert emp_data["valid"] == True
        print(f"Step 1 PASS: Employee {emp_data['name']} is in approved list")
        
        # Step 2: Check if guest is already registered
        guest_response = requests.get(f"{BASE_URL}/api/guests/2202373")
        if guest_response.status_code == 200:
            print("Step 2 PASS: Guest is already registered - show full form")
        else:
            print("Step 2 INFO: Guest not registered - show Register button")
    
    def test_new_guest_flow(self):
        """Test flow for employee in list but not registered as guest"""
        # Find an employee who is in list but not registered
        emp_response = requests.get(f"{BASE_URL}/api/employees/verify/1177593")
        
        if emp_response.status_code == 200:
            emp_data = emp_response.json()
            # Now check if they're a registered guest
            guest_response = requests.get(f"{BASE_URL}/api/guests/1177593")
            if guest_response.status_code == 404:
                print(f"PASS: Employee {emp_data['name']} is in list but not registered - shows 'Register as' button")
            else:
                print(f"INFO: Employee {emp_data['name']} is already registered as guest")
        else:
            print("INFO: Employee 1177593 not in list - checking different employee")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
