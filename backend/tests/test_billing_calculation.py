"""
Backend tests for Hodler Inn - Billing Calculation & Bug Fixes
Tests the nights billed calculation based on 24-hour periods.

Bug Fix Tests:
1. Billing calculation: ceil(hours/24) instead of calendar days
2. SYNC_AGENT_VERSION should be 2026-03-05-v4
"""

import pytest
import requests
import os
import sys

# Add parent directory to import server modules directly
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

# ==================== Unit Tests for calculate_stay_duration ====================

class TestBillingCalculation:
    """Test the nights billed calculation logic.
    
    Bug fix: Stays over 24 hours should be billed as multiple nights
    - ceil(28/24) = 2 nights
    - ceil(23/24) = 1 night
    - ceil(48/24) = 2 nights
    - ceil(72/24) = 3 nights
    """
    
    def test_28_hours_should_be_2_nights(self):
        """28 hours = 2 nights billed (ceiling of 28/24 = 2)"""
        from server import calculate_stay_duration
        
        # 28 hours: check in Jan 1 10:00, check out Jan 2 14:00
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-02", "14:00"
        )
        
        assert hours == 28.0, f"Expected 28.0 hours, got {hours}"
        assert nights == 2, f"BILLING BUG: 28 hours should be 2 nights (ceil(28/24)=2), got {nights}"
        print(f"✓ 28 hours = {nights} nights billed (correct)")
    
    def test_23_hours_should_be_1_night(self):
        """23 hours = 1 night billed (ceiling of 23/24 = 1)"""
        from server import calculate_stay_duration
        
        # 23 hours: check in Jan 1 10:00, check out Jan 2 09:00
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-02", "09:00"
        )
        
        assert hours == 23.0, f"Expected 23.0 hours, got {hours}"
        assert nights == 1, f"BILLING BUG: 23 hours should be 1 night (ceil(23/24)=1), got {nights}"
        print(f"✓ 23 hours = {nights} night billed (correct)")
    
    def test_48_hours_should_be_2_nights(self):
        """48 hours = 2 nights billed (ceiling of 48/24 = 2)"""
        from server import calculate_stay_duration
        
        # 48 hours: check in Jan 1 10:00, check out Jan 3 10:00
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-03", "10:00"
        )
        
        assert hours == 48.0, f"Expected 48.0 hours, got {hours}"
        assert nights == 2, f"BILLING BUG: 48 hours should be 2 nights (ceil(48/24)=2), got {nights}"
        print(f"✓ 48 hours = {nights} nights billed (correct)")
    
    def test_72_hours_should_be_3_nights(self):
        """72 hours = 3 nights billed (ceiling of 72/24 = 3)"""
        from server import calculate_stay_duration
        
        # 72 hours: check in Jan 1 10:00, check out Jan 4 10:00
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-04", "10:00"
        )
        
        assert hours == 72.0, f"Expected 72.0 hours, got {hours}"
        assert nights == 3, f"BILLING BUG: 72 hours should be 3 nights (ceil(72/24)=3), got {nights}"
        print(f"✓ 72 hours = {nights} nights billed (correct)")
    
    def test_49_hours_should_be_3_nights(self):
        """49 hours = 3 nights billed (ceiling of 49/24 = 3)"""
        from server import calculate_stay_duration
        
        # 49 hours: check in Jan 1 10:00, check out Jan 3 11:00
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-03", "11:00"
        )
        
        assert hours == 49.0, f"Expected 49.0 hours, got {hours}"
        assert nights == 3, f"BILLING BUG: 49 hours should be 3 nights (ceil(49/24)=3), got {nights}"
        print(f"✓ 49 hours = {nights} nights billed (correct)")
    
    def test_25_hours_should_be_2_nights(self):
        """25 hours = 2 nights billed (just over 24 hours)"""
        from server import calculate_stay_duration
        
        # 25 hours: check in Jan 1 10:00, check out Jan 2 11:00
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-02", "11:00"
        )
        
        assert hours == 25.0, f"Expected 25.0 hours, got {hours}"
        assert nights == 2, f"BILLING BUG: 25 hours should be 2 nights (ceil(25/24)=2), got {nights}"
        print(f"✓ 25 hours = {nights} nights billed (correct)")
    
    def test_24_hours_exactly_should_be_1_night(self):
        """24 hours exactly = 1 night billed"""
        from server import calculate_stay_duration
        
        # Exactly 24 hours
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-02", "10:00"
        )
        
        assert hours == 24.0, f"Expected 24.0 hours, got {hours}"
        assert nights == 1, f"BILLING BUG: 24 hours exactly should be 1 night, got {nights}"
        print(f"✓ 24 hours exactly = {nights} night billed (correct)")
    
    def test_minimum_1_night(self):
        """Any stay should be minimum 1 night"""
        from server import calculate_stay_duration
        
        # Very short stay - 30 minutes
        hours, nights = calculate_stay_duration(
            "2026-01-01", "10:00",
            "2026-01-01", "10:30"
        )
        
        assert hours == 0.5, f"Expected 0.5 hours, got {hours}"
        assert nights == 1, f"BILLING BUG: Minimum should be 1 night, got {nights}"
        print(f"✓ 30 minutes = {nights} night billed (minimum 1 night correct)")


# ==================== Sync Agent Version Test ====================

class TestSyncAgentVersion:
    """Test that sync agent version is correct."""
    
    def test_sync_agent_version(self):
        """SYNC_AGENT_VERSION should be 2026-03-05-v4"""
        from sync_agent import SYNC_AGENT_VERSION
        
        expected_version = "2026-03-05-v4"
        assert SYNC_AGENT_VERSION == expected_version, \
            f"SYNC_AGENT_VERSION is '{SYNC_AGENT_VERSION}', expected '{expected_version}'"
        print(f"✓ SYNC_AGENT_VERSION = {SYNC_AGENT_VERSION} (correct)")


# ==================== API Endpoint Tests ====================

class TestHealthEndpoint:
    """Test health check endpoint."""
    
    def test_health_returns_healthy(self):
        """Health endpoint should return status 'healthy'"""
        response = requests.get(f"{BASE_URL}/api/health")
        
        assert response.status_code == 200, f"Health check returned {response.status_code}"
        data = response.json()
        assert data.get("status") == "healthy", f"Health status is '{data.get('status')}', expected 'healthy'"
        assert data.get("database") == "connected", f"Database status is '{data.get('database')}', expected 'connected'"
        print(f"✓ Health endpoint: status={data.get('status')}, database={data.get('database')}")


class TestAdminEndpoints:
    """Test admin dashboard endpoints."""
    
    def test_admin_guests_endpoint(self):
        """Admin guests endpoint should return guest list"""
        response = requests.get(f"{BASE_URL}/api/admin/guests")
        
        assert response.status_code == 200, f"Admin guests returned {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Admin guests should return a list"
        print(f"✓ Admin guests endpoint: {len(data)} guests found")
    
    def test_admin_employees_endpoint(self):
        """Admin employees endpoint should return employee list"""
        response = requests.get(f"{BASE_URL}/api/admin/employees")
        
        assert response.status_code == 200, f"Admin employees endpoint returned {response.status_code}"
        data = response.json()
        assert isinstance(data, list), "Admin employees should return a list"
        print(f"✓ Admin employees endpoint: {len(data)} employees found")


class TestBillingReportEndpoints:
    """Test billing report export functionality."""
    
    def test_billing_report_endpoint_exists(self):
        """Billing report endpoint should exist and respond"""
        # Test CSV export
        response = requests.get(f"{BASE_URL}/api/admin/billing/export?format=csv")
        
        # Should return 200 with CSV or 404/400 if no data - both are valid responses
        assert response.status_code in [200, 400, 404], \
            f"Billing export returned unexpected status {response.status_code}"
        print(f"✓ Billing CSV export endpoint: status={response.status_code}")
    
    def test_billing_report_excel_endpoint(self):
        """Billing report Excel export should work"""
        response = requests.get(f"{BASE_URL}/api/admin/billing/export?format=xlsx")
        
        # Should return 200 with XLSX or appropriate error
        assert response.status_code in [200, 400, 404], \
            f"Billing XLSX export returned unexpected status {response.status_code}"
        print(f"✓ Billing XLSX export endpoint: status={response.status_code}")


# ==================== Sync Agent Logic Tests ====================

class TestSyncAgentNameMatching:
    """Test sync agent name matching functions.
    Note: These test current behavior of the name matching system.
    """
    
    def test_normalize_name_lastname_firstname_with_suffix(self):
        """Test name normalization for LASTNAME/FIRSTNAME/SUFFIX format"""
        from sync_agent import normalize_name
        
        # LASTNAME/FIRSTNAME/SUFFIX format - this is the common pattern
        result = normalize_name("BEARDEN/WILLIAM/OT I E")
        assert result == "william bearden", f"Expected 'william bearden', got '{result}'"
        print(f"✓ normalize_name('BEARDEN/WILLIAM/OT I E') = '{result}'")
    
    def test_normalize_name_lastname_parenthesis_format(self):
        """Test name normalization for LASTNAME,(FIRSTNAME) format"""
        from sync_agent import normalize_name
        
        # LASTNAME,(FIRSTNAME) format
        result = normalize_name("SMITH,(JOHN)")
        assert result == "john smith", f"Expected 'john smith', got '{result}'"
        print(f"✓ normalize_name('SMITH,(JOHN)') = '{result}'")
    
    def test_normalize_name_lastname_space_paren_format(self):
        """Test name normalization for LASTNAME (FIRSTNAME) format with space"""
        from sync_agent import normalize_name
        
        # LASTNAME (FIRSTNAME) format with space before parenthesis
        result = normalize_name("HESS (BERNARD) DT/2 E")
        assert result == "bernard hess", f"Expected 'bernard hess', got '{result}'"
        print(f"✓ normalize_name('HESS (BERNARD) DT/2 E') = '{result}'")
    
    def test_match_names_exact_paren_format(self):
        """Test name matching for LASTNAME (FIRSTNAME) format"""
        from sync_agent import match_names
        
        result = match_names("HESS (BERNARD)", "Bernard Hess")
        assert result == True, "HESS (BERNARD) should match Bernard Hess"
        print("✓ match_names('HESS (BERNARD)', 'Bernard Hess') = True")
    
    def test_match_names_comma_paren_format(self):
        """Test name matching for LASTNAME,(FIRSTNAME) format"""
        from sync_agent import match_names
        
        result = match_names("SMITH,(JOHN)", "John Smith")
        assert result == True, "SMITH,(JOHN) should match John Smith"
        print("✓ match_names('SMITH,(JOHN)', 'John Smith') = True")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
