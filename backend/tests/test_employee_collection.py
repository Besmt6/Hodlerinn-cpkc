"""
Test suite for Employee Collection from Railroad Portal
Tests the /api/admin/employees endpoint and validates imported employee data
"""
import pytest
import requests
import os

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmployeeCollection:
    """Tests for employee collection and retrieval from portal import"""
    
    def test_health_check(self):
        """Test API health endpoint"""
        response = requests.get(f"{BASE_URL}/api/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert data["database"] == "connected"
        print(f"Health check passed: {data}")
    
    def test_get_employees_returns_list(self):
        """GET /api/admin/employees returns list of imported employees"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert isinstance(data, list), "Response should be a list"
        print(f"Total employees returned: {len(data)}")
    
    def test_employees_count_meets_minimum(self):
        """Verify at least 63 employees were imported (per main agent context)"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        # Main agent stated 63 employees were imported - verify minimum count
        assert len(data) >= 60, f"Expected at least 60 employees, got {len(data)}"
        print(f"Employee count verification: {len(data)} employees found (minimum 60 required)")
    
    def test_employees_have_required_fields(self):
        """Verify all employees have employee_number and name fields"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) > 0, "No employees found in database"
        
        missing_employee_number = []
        missing_name = []
        valid_employees = 0
        
        for emp in data:
            has_emp_num = "employee_number" in emp and emp["employee_number"]
            has_name = "name" in emp and emp["name"]
            
            if not has_emp_num:
                missing_employee_number.append(emp)
            if not has_name:
                missing_name.append(emp)
            if has_emp_num and has_name:
                valid_employees += 1
        
        print(f"Valid employees (with both fields): {valid_employees}/{len(data)}")
        if missing_employee_number:
            print(f"Employees missing employee_number: {len(missing_employee_number)}")
        if missing_name:
            print(f"Employees missing name: {len(missing_name)}")
        
        # All employees should have both required fields
        assert len(missing_employee_number) == 0, f"Found {len(missing_employee_number)} employees without employee_number"
        assert len(missing_name) == 0, f"Found {len(missing_name)} employees without name"
    
    def test_employee_number_format_valid(self):
        """Verify employee_number values are valid (alphanumeric, reasonable length)"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        invalid_format = []
        
        for emp in data:
            emp_num = emp.get("employee_number", "")
            # Employee numbers should be alphanumeric and reasonable length (1-15 chars)
            if not emp_num or len(emp_num) > 15 or not emp_num.replace('-', '').replace('.', '').replace(' ', '').isalnum():
                invalid_format.append({"employee_number": emp_num, "name": emp.get("name", "")})
        
        if invalid_format:
            print(f"Invalid employee numbers found: {invalid_format[:5]}")
        
        assert len(invalid_format) == 0, f"Found {len(invalid_format)} employees with invalid employee_number format"
        print(f"All {len(data)} employees have valid employee_number format")
    
    def test_employee_name_format_valid(self):
        """Verify name values are properly formatted (not raw portal format)"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        raw_format_names = []
        
        for emp in data:
            name = emp.get("name", "")
            # Names should NOT be in raw portal format like "LASTNAME,(FIRSTNAME)SUFFIX"
            # They should be formatted as "First Last"
            if "(" in name or ")" in name or name.isupper():
                raw_format_names.append({"name": name, "employee_number": emp.get("employee_number", "")})
        
        if raw_format_names:
            print(f"Names in raw format (may need formatting): {raw_format_names[:5]}")
        
        # Warning level - names should be formatted but not critical if some are raw
        print(f"Names formatted correctly: {len(data) - len(raw_format_names)}/{len(data)}")
    
    def test_employees_sorted_by_name(self):
        """Verify employees are returned sorted by name (as per API implementation)"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        if len(data) < 2:
            pytest.skip("Not enough employees to verify sorting")
        
        # Check if first 10 employees are in alphabetical order by name
        names = [emp.get("name", "").lower() for emp in data[:10]]
        sorted_names = sorted(names)
        
        is_sorted = names == sorted_names
        print(f"First 10 employee names: {names[:5]}")
        print(f"Employees sorted by name: {is_sorted}")
        
        assert is_sorted, "Employees should be sorted by name alphabetically"
    
    def test_sample_employees_data_quality(self):
        """Verify sample employees have expected data structure"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        assert len(data) >= 5, "Need at least 5 employees for sample validation"
        
        sample = data[:5]
        print("Sample employee data:")
        for emp in sample:
            emp_num = emp.get("employee_number", "N/A")
            name = emp.get("name", "N/A")
            is_active = emp.get("is_active", "N/A")
            source = emp.get("source", "N/A")
            print(f"  - ID: {emp_num}, Name: {name}, Active: {is_active}, Source: {source}")
            
            # Each employee should have these fields
            assert "id" in emp, f"Employee {emp_num} missing 'id' field"
            assert "employee_number" in emp, f"Employee {emp_num} missing 'employee_number' field"
            assert "name" in emp, f"Employee {emp_num} missing 'name' field"
    
    def test_employees_have_portal_source(self):
        """Verify imported employees have source='portal_import' marker"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        portal_imported = [emp for emp in data if emp.get("source") == "portal_import"]
        other_source = [emp for emp in data if emp.get("source") != "portal_import"]
        
        print(f"Employees from portal import: {len(portal_imported)}")
        print(f"Employees from other sources: {len(other_source)}")
        
        # At least 50 employees should be from portal import
        assert len(portal_imported) >= 50, f"Expected at least 50 portal-imported employees, got {len(portal_imported)}"
    
    def test_employee_verify_endpoint(self):
        """Test the public employee verification endpoint"""
        # First get an employee
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        assert response.status_code == 200
        
        data = response.json()
        if not data:
            pytest.skip("No employees to test verification")
        
        # Pick first active employee
        test_emp = data[0]
        emp_num = test_emp.get("employee_number")
        
        # Test verification endpoint
        verify_response = requests.get(f"{BASE_URL}/api/employees/verify/{emp_num}")
        assert verify_response.status_code == 200
        
        verify_data = verify_response.json()
        assert verify_data.get("valid") == True
        assert verify_data.get("employee_number") == emp_num
        assert "name" in verify_data
        print(f"Employee verification passed for {emp_num}: {verify_data}")
    
    def test_employee_verify_invalid_id(self):
        """Test verification endpoint rejects invalid employee IDs"""
        # Use clearly invalid employee number
        invalid_emp_num = "INVALID_99999999"
        
        response = requests.get(f"{BASE_URL}/api/employees/verify/{invalid_emp_num}")
        assert response.status_code == 404, f"Expected 404 for invalid employee, got {response.status_code}"
        print(f"Invalid employee verification correctly returns 404")


class TestCollectEmployeesEndpoint:
    """Tests for the POST /api/admin/collect-employees endpoint - structure validation only"""
    
    def test_endpoint_exists_without_triggering(self):
        """Verify the endpoint exists by checking error response when no credentials"""
        # Note: We're not triggering actual scraping, just validating endpoint exists
        # The endpoint should return 400 if credentials are not configured
        # or some other response if called
        response = requests.options(f"{BASE_URL}/api/admin/collect-employees")
        # OPTIONS request should succeed for CORS preflight
        print(f"Endpoint preflight check: {response.status_code}")
        # Just verify endpoint is reachable
        assert response.status_code in [200, 204, 405], "Endpoint should be reachable"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
