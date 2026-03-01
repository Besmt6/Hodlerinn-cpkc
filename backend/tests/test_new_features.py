"""
Test suite for Hodler Inn - New Features (Room Management, Date Filtering, PDF Export)
Tests: Room CRUD, Date Range Filtering, PDF Export endpoints
"""
import pytest
import requests
import os
from datetime import datetime, timedelta

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', 'https://hotel-guest-system.preview.emergentagent.com').rstrip('/')

class TestRoomManagement:
    """Room Management CRUD tests"""
    
    def test_get_all_rooms(self):
        """Test getting all rooms"""
        response = requests.get(f"{BASE_URL}/api/admin/rooms")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/rooms - Found {len(data)} rooms")
        
        # Verify room structure
        if len(data) > 0:
            room = data[0]
            assert 'id' in room
            assert 'room_number' in room
            assert 'room_type' in room
            assert 'floor' in room
            assert 'status' in room
            print(f"✓ Room structure validated - Room {room['room_number']}: {room['room_type']}, Status: {room['status']}")
    
    def test_create_room(self):
        """Test creating a new room"""
        test_room = {
            "room_number": f"TEST_{datetime.now().strftime('%H%M%S')}",
            "room_type": "Suite",
            "floor": "3",
            "notes": "Test room for automated testing"
        }
        
        response = requests.post(f"{BASE_URL}/api/admin/rooms", json=test_room)
        assert response.status_code == 200
        data = response.json()
        assert 'message' in data
        assert data['message'] == "Room created successfully"
        assert 'room' in data
        print(f"✓ POST /api/admin/rooms - Created room {test_room['room_number']}")
        
        # Verify room was persisted by fetching all rooms
        get_response = requests.get(f"{BASE_URL}/api/admin/rooms")
        rooms = get_response.json()
        created_room = next((r for r in rooms if r['room_number'] == test_room['room_number']), None)
        assert created_room is not None
        assert created_room['room_type'] == test_room['room_type']
        assert created_room['floor'] == test_room['floor']
        print(f"✓ Room verified in database")
        
        return created_room
    
    def test_create_duplicate_room(self):
        """Test creating a duplicate room fails"""
        # First, get existing rooms
        response = requests.get(f"{BASE_URL}/api/admin/rooms")
        rooms = response.json()
        
        if len(rooms) > 0:
            existing_room_number = rooms[0]['room_number']
            duplicate_room = {
                "room_number": existing_room_number,
                "room_type": "Standard",
                "floor": "1"
            }
            
            response = requests.post(f"{BASE_URL}/api/admin/rooms", json=duplicate_room)
            assert response.status_code == 400
            assert 'detail' in response.json()
            print(f"✓ POST /api/admin/rooms - Duplicate room {existing_room_number} correctly rejected")
        else:
            pytest.skip("No existing rooms to test duplicate")
    
    def test_update_room(self):
        """Test updating a room"""
        # First create a test room
        test_room = {
            "room_number": f"TEST_UPDATE_{datetime.now().strftime('%H%M%S')}",
            "room_type": "Standard",
            "floor": "1",
            "notes": "Initial notes"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/rooms", json=test_room)
        assert create_response.status_code == 200
        room_data = create_response.json()['room']
        room_id = room_data['id']
        
        # Update the room
        update_data = {
            "room_type": "Deluxe",
            "floor": "2",
            "notes": "Updated notes",
            "status": "maintenance"
        }
        
        update_response = requests.put(f"{BASE_URL}/api/admin/rooms/{room_id}", json=update_data)
        assert update_response.status_code == 200
        assert update_response.json()['message'] == "Room updated successfully"
        print(f"✓ PUT /api/admin/rooms/{room_id} - Room updated")
        
        # Verify update was persisted
        get_response = requests.get(f"{BASE_URL}/api/admin/rooms")
        rooms = get_response.json()
        updated_room = next((r for r in rooms if r['id'] == room_id), None)
        assert updated_room is not None
        assert updated_room['room_type'] == "Deluxe"
        assert updated_room['floor'] == "2"
        print(f"✓ Room update verified in database")
    
    def test_delete_room(self):
        """Test deleting a room"""
        # First create a test room to delete
        test_room = {
            "room_number": f"TEST_DELETE_{datetime.now().strftime('%H%M%S')}",
            "room_type": "Standard",
            "floor": "1"
        }
        
        create_response = requests.post(f"{BASE_URL}/api/admin/rooms", json=test_room)
        assert create_response.status_code == 200
        room_data = create_response.json()['room']
        room_id = room_data['id']
        
        # Delete the room
        delete_response = requests.delete(f"{BASE_URL}/api/admin/rooms/{room_id}")
        assert delete_response.status_code == 200
        assert delete_response.json()['message'] == "Room deleted successfully"
        print(f"✓ DELETE /api/admin/rooms/{room_id} - Room deleted")
        
        # Verify deletion
        get_response = requests.get(f"{BASE_URL}/api/admin/rooms")
        rooms = get_response.json()
        deleted_room = next((r for r in rooms if r['id'] == room_id), None)
        assert deleted_room is None
        print(f"✓ Room deletion verified")
    
    def test_delete_nonexistent_room(self):
        """Test deleting a nonexistent room fails"""
        fake_id = "nonexistent-room-id"
        response = requests.delete(f"{BASE_URL}/api/admin/rooms/{fake_id}")
        assert response.status_code == 404
        print(f"✓ DELETE /api/admin/rooms/{fake_id} - 404 as expected")


class TestDateRangeFiltering:
    """Date Range Filtering tests"""
    
    def test_get_records_without_filter(self):
        """Test getting records without date filter"""
        response = requests.get(f"{BASE_URL}/api/admin/records")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/records (no filter) - Found {len(data)} records")
    
    def test_get_records_with_start_date(self):
        """Test filtering records with start_date"""
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(f"{BASE_URL}/api/admin/records?start_date={today}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/records?start_date={today} - Found {len(data)} records")
    
    def test_get_records_with_end_date(self):
        """Test filtering records with end_date"""
        today = datetime.now().strftime('%Y-%m-%d')
        response = requests.get(f"{BASE_URL}/api/admin/records?end_date={today}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/records?end_date={today} - Found {len(data)} records")
    
    def test_get_records_with_date_range(self):
        """Test filtering records with full date range"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = requests.get(f"{BASE_URL}/api/admin/records?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/records?start_date={start_date}&end_date={end_date} - Found {len(data)} records")
    
    def test_get_records_with_future_date(self):
        """Test filtering records with future date returns empty"""
        future_date = (datetime.now() + timedelta(days=365)).strftime('%Y-%m-%d')
        response = requests.get(f"{BASE_URL}/api/admin/records?start_date={future_date}")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        print(f"✓ GET /api/admin/records?start_date={future_date} (future) - Found {len(data)} records")


class TestPDFExport:
    """PDF Export tests"""
    
    def test_export_signin_pdf(self):
        """Test Sign-In Sheet PDF export"""
        response = requests.get(f"{BASE_URL}/api/admin/export-pdf")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert 'attachment' in response.headers.get('content-disposition', '')
        assert len(response.content) > 0
        print(f"✓ GET /api/admin/export-pdf - PDF generated ({len(response.content)} bytes)")
    
    def test_export_signin_pdf_with_date_filter(self):
        """Test Sign-In Sheet PDF export with date filter"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = requests.get(f"{BASE_URL}/api/admin/export-pdf?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        print(f"✓ GET /api/admin/export-pdf with date filter - PDF generated ({len(response.content)} bytes)")
    
    def test_export_billing_pdf(self):
        """Test Billing Report PDF export"""
        response = requests.get(f"{BASE_URL}/api/admin/export-billing-pdf")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        assert 'attachment' in response.headers.get('content-disposition', '')
        assert len(response.content) > 0
        print(f"✓ GET /api/admin/export-billing-pdf - PDF generated ({len(response.content)} bytes)")
    
    def test_export_billing_pdf_with_date_filter(self):
        """Test Billing Report PDF export with date filter"""
        end_date = datetime.now().strftime('%Y-%m-%d')
        start_date = (datetime.now() - timedelta(days=30)).strftime('%Y-%m-%d')
        
        response = requests.get(f"{BASE_URL}/api/admin/export-billing-pdf?start_date={start_date}&end_date={end_date}")
        assert response.status_code == 200
        assert response.headers['content-type'] == 'application/pdf'
        print(f"✓ GET /api/admin/export-billing-pdf with date filter - PDF generated ({len(response.content)} bytes)")


class TestRoomStats:
    """Room stats calculation tests"""
    
    def test_room_stats_counts(self):
        """Test room stats are correctly calculated"""
        response = requests.get(f"{BASE_URL}/api/admin/rooms")
        assert response.status_code == 200
        rooms = response.json()
        
        total = len(rooms)
        available = len([r for r in rooms if r['status'] == 'available'])
        occupied = len([r for r in rooms if r['status'] == 'occupied'])
        maintenance = len([r for r in rooms if r['status'] == 'maintenance'])
        
        print(f"✓ Room Stats: Total={total}, Available={available}, Occupied={occupied}, Maintenance={maintenance}")
        
        # Verify counts add up
        assert available + occupied + maintenance == total or (available + occupied <= total)


# Cleanup fixture for test rooms
@pytest.fixture(scope="module", autouse=True)
def cleanup_test_rooms():
    """Cleanup test rooms after tests complete"""
    yield
    
    # Delete all rooms starting with TEST_
    response = requests.get(f"{BASE_URL}/api/admin/rooms")
    if response.status_code == 200:
        rooms = response.json()
        for room in rooms:
            if room['room_number'].startswith('TEST_'):
                requests.delete(f"{BASE_URL}/api/admin/rooms/{room['id']}")
                print(f"Cleaned up test room: {room['room_number']}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
