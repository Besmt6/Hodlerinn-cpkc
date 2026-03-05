import requests
import sys
import json
from datetime import datetime, timedelta
import base64

class HodlerInnAPITester:
    def __init__(self, base_url="https://hodler-staging.preview.emergentagent.com/api"):
        self.base_url = base_url
        self.tests_run = 0
        self.tests_passed = 0
        self.test_data = {
            "employee_number": f"EMP{datetime.now().strftime('%H%M%S')}",
            "employee_name": "Test Employee",
            "room_number": f"ROOM{datetime.now().strftime('%M%S')}",
            "signature": "data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mP8/5+hHgAHggJ/PchI7wAAAABJRU5ErkJggg=="
        }

    def run_test(self, name, method, endpoint, expected_status, data=None):
        """Run a single API test"""
        url = f"{self.base_url}/{endpoint}"
        headers = {'Content-Type': 'application/json'}

        self.tests_run += 1
        print(f"\n🔍 Testing {name}...")
        print(f"   URL: {url}")
        if data:
            print(f"   Data: {json.dumps(data, indent=2)}")
        
        try:
            if method == 'GET':
                response = requests.get(url, headers=headers, timeout=10)
            elif method == 'POST':
                response = requests.post(url, json=data, headers=headers, timeout=10)

            print(f"   Response Status: {response.status_code}")
            success = response.status_code == expected_status
            
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                try:
                    response_data = response.json()
                    print(f"   Response: {json.dumps(response_data, indent=2)}")
                    return success, response_data
                except:
                    return success, {}
            else:
                print(f"❌ Failed - Expected {expected_status}, got {response.status_code}")
                try:
                    error_data = response.json()
                    print(f"   Error Response: {json.dumps(error_data, indent=2)}")
                except:
                    print(f"   Error Response: {response.text}")
                return False, {}

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False, {}

    def test_root_endpoint(self):
        """Test the root API endpoint"""
        success, response = self.run_test(
            "Root API Endpoint",
            "GET",
            "",
            200
        )
        return success

    def test_guest_registration(self):
        """Test guest registration"""
        success, response = self.run_test(
            "Guest Registration",
            "POST",
            "guests/register",
            200,
            data={
                "employee_number": self.test_data["employee_number"],
                "name": self.test_data["employee_name"],
                "signature": self.test_data["signature"]
            }
        )
        return success

    def test_duplicate_guest_registration(self):
        """Test duplicate guest registration (should fail)"""
        success, response = self.run_test(
            "Duplicate Guest Registration (should fail)",
            "POST",
            "guests/register",
            400,  # Should fail with 400
            data={
                "employee_number": self.test_data["employee_number"],
                "name": self.test_data["employee_name"],
                "signature": self.test_data["signature"]
            }
        )
        return success

    def test_get_guest(self):
        """Test getting guest by employee number"""
        success, response = self.run_test(
            "Get Guest by Employee Number",
            "GET",
            f"guests/{self.test_data['employee_number']}",
            200
        )
        return success

    def test_get_nonexistent_guest(self):
        """Test getting non-existent guest (should fail)"""
        success, response = self.run_test(
            "Get Non-existent Guest (should fail)",
            "GET",
            "guests/NONEXISTENT123",
            404  # Should fail with 404
        )
        return success

    def test_checkin(self):
        """Test guest check-in"""
        check_in_date = datetime.now().strftime("%Y-%m-%d")
        check_in_time = datetime.now().strftime("%H:%M")
        
        success, response = self.run_test(
            "Guest Check-In",
            "POST",
            "checkin",
            200,
            data={
                "employee_number": self.test_data["employee_number"],
                "room_number": self.test_data["room_number"],
                "check_in_date": check_in_date,
                "check_in_time": check_in_time
            }
        )
        return success

    def test_checkin_unregistered_guest(self):
        """Test check-in with unregistered guest (should fail)"""
        check_in_date = datetime.now().strftime("%Y-%m-%d")
        check_in_time = datetime.now().strftime("%H:%M")
        
        success, response = self.run_test(
            "Check-In Unregistered Guest (should fail)",
            "POST",
            "checkin",
            404,  # Should fail with 404
            data={
                "employee_number": "UNREGISTERED123",
                "room_number": "TESTROOM999",
                "check_in_date": check_in_date,
                "check_in_time": check_in_time
            }
        )
        return success

    def test_checkin_occupied_room(self):
        """Test check-in to occupied room (should fail)"""
        check_in_date = datetime.now().strftime("%Y-%m-%d")
        check_in_time = datetime.now().strftime("%H:%M")
        
        success, response = self.run_test(
            "Check-In to Occupied Room (should fail)",
            "POST",
            "checkin",
            400,  # Should fail with 400
            data={
                "employee_number": self.test_data["employee_number"],
                "room_number": self.test_data["room_number"],  # Same room as before
                "check_in_date": check_in_date,
                "check_in_time": check_in_time
            }
        )
        return success

    def test_checkout(self):
        """Test guest check-out"""
        check_out_date = (datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
        check_out_time = datetime.now().strftime("%H:%M")
        
        success, response = self.run_test(
            "Guest Check-Out",
            "POST",
            "checkout",
            200,
            data={
                "room_number": self.test_data["room_number"],
                "check_out_date": check_out_date,
                "check_out_time": check_out_time
            }
        )
        return success

    def test_checkout_nonexistent_room(self):
        """Test check-out from non-existent room (should fail)"""
        check_out_date = datetime.now().strftime("%Y-%m-%d")
        check_out_time = datetime.now().strftime("%H:%M")
        
        success, response = self.run_test(
            "Check-Out Non-existent Room (should fail)",
            "POST",
            "checkout",
            404,  # Should fail with 404
            data={
                "room_number": "NONEXISTENT999",
                "check_out_date": check_out_date,
                "check_out_time": check_out_time
            }
        )
        return success

    def test_admin_login_valid(self):
        """Test admin login with valid password"""
        success, response = self.run_test(
            "Admin Login (Valid Password)",
            "POST",
            "admin/login",
            200,
            data={"password": "hodlerinn2024"}
        )
        return success

    def test_admin_login_invalid(self):
        """Test admin login with invalid password (should fail)"""
        success, response = self.run_test(
            "Admin Login (Invalid Password - should fail)",
            "POST",
            "admin/login",
            401,  # Should fail with 401
            data={"password": "wrongpassword"}
        )
        return success

    def test_admin_stats(self):
        """Test admin stats endpoint"""
        success, response = self.run_test(
            "Admin Stats",
            "GET",
            "admin/stats",
            200
        )
        return success

    def test_admin_records(self):
        """Test admin records endpoint"""
        success, response = self.run_test(
            "Admin Records",
            "GET",
            "admin/records",
            200
        )
        return success

    def test_admin_export(self):
        """Test admin Excel export endpoint"""
        url = f"{self.base_url}/admin/export"
        headers = {'Accept': 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'}

        self.tests_run += 1
        print(f"\n🔍 Testing Admin Excel Export...")
        print(f"   URL: {url}")
        
        try:
            response = requests.get(url, headers=headers, timeout=30)
            print(f"   Response Status: {response.status_code}")
            
            success = response.status_code == 200
            if success:
                self.tests_passed += 1
                print(f"✅ Passed - Status: {response.status_code}")
                print(f"   Content-Type: {response.headers.get('Content-Type', 'N/A')}")
                print(f"   Content-Length: {len(response.content)} bytes")
                return True
            else:
                print(f"❌ Failed - Expected 200, got {response.status_code}")
                return False

        except Exception as e:
            print(f"❌ Failed - Error: {str(e)}")
            return False

def main():
    print("🏨 Starting Hodler Inn API Testing...")
    print("=" * 60)
    
    tester = HodlerInnAPITester()

    # Test sequence
    tests = [
        ("Root Endpoint", tester.test_root_endpoint),
        ("Guest Registration", tester.test_guest_registration),
        ("Duplicate Registration", tester.test_duplicate_guest_registration),
        ("Get Guest", tester.test_get_guest),
        ("Get Non-existent Guest", tester.test_get_nonexistent_guest),
        ("Check-In", tester.test_checkin),
        ("Check-In Unregistered", tester.test_checkin_unregistered_guest),
        ("Check-In Occupied Room", tester.test_checkin_occupied_room),
        ("Check-Out", tester.test_checkout),
        ("Check-Out Non-existent Room", tester.test_checkout_nonexistent_room),
        ("Admin Login Valid", tester.test_admin_login_valid),
        ("Admin Login Invalid", tester.test_admin_login_invalid),
        ("Admin Stats", tester.test_admin_stats),
        ("Admin Records", tester.test_admin_records),
        ("Admin Excel Export", tester.test_admin_export),
    ]

    print(f"\n📊 Running {len(tests)} test scenarios...")
    
    for test_name, test_func in tests:
        try:
            test_func()
        except Exception as e:
            print(f"❌ Test '{test_name}' crashed: {str(e)}")

    # Print final results
    print("\n" + "=" * 60)
    print(f"📊 Final Results: {tester.tests_passed}/{tester.tests_run} tests passed")
    print(f"🎯 Success Rate: {(tester.tests_passed/tester.tests_run*100):.1f}%")
    
    if tester.tests_passed == tester.tests_run:
        print("🎉 All tests passed! Backend is working correctly.")
        return 0
    else:
        failed_tests = tester.tests_run - tester.tests_passed
        print(f"⚠️  {failed_tests} test(s) failed. Check issues above.")
        return 1

if __name__ == "__main__":
    sys.exit(main())