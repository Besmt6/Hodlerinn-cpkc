"""
Test Email Alert Settings API - Per-recipient customization feature
Tests the new per-recipient email alert preferences feature
"""
import pytest
import requests
import os
import uuid

BASE_URL = os.environ.get('REACT_APP_BACKEND_URL', '').rstrip('/')

class TestEmailAlertSettings:
    """Test email alert settings and per-recipient customization"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data and cleanup after each test"""
        self.test_email = f"test_{uuid.uuid4().hex[:8]}@example.com"
        yield
        # Cleanup: Remove test email if it was added
        try:
            requests.delete(f"{BASE_URL}/api/admin/email-alerts/recipients?email={self.test_email}")
        except:
            pass
    
    def test_get_email_alert_settings(self):
        """GET /api/admin/email-alerts/settings - Returns recipients with per-recipient alert preferences"""
        response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        data = response.json()
        
        # Verify response structure - recipients is the key field
        assert "recipients" in data, "Response should contain 'recipients' field"
        
        # Verify recipients format (should be list)
        assert isinstance(data["recipients"], list), "Recipients should be a list"
        
        # If recipients exist, verify structure
        if data["recipients"]:
            for recipient in data["recipients"]:
                if isinstance(recipient, dict):
                    # New format: {email, alerts}
                    assert "email" in recipient, "Recipient dict should contain 'email'"
                    assert "alerts" in recipient, "Recipient dict should contain 'alerts'"
                    assert isinstance(recipient["alerts"], list), "Alerts should be a list"
                # Old format (string) is also acceptable for backwards compatibility
        
        # Note: Master toggles (sold_out_enabled, etc.) may not be present if not yet updated
        # The get_email_alert_settings() helper function returns defaults if these fields missing
        print(f"✓ GET settings returns {len(data['recipients'])} recipients with proper structure")
    
    def test_add_recipient_with_default_alerts(self):
        """POST /api/admin/email-alerts/recipients/add - Adds recipient with all alerts enabled by default"""
        response = requests.post(
            f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_email}"
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        
        assert "message" in data, "Response should contain success message"
        assert self.test_email in data["message"], "Message should mention the added email"
        
        # Verify the recipient was added with correct format
        settings_response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        settings = settings_response.json()
        
        found_recipient = None
        for recipient in settings["recipients"]:
            if isinstance(recipient, dict) and recipient.get("email") == self.test_email:
                found_recipient = recipient
                break
            elif isinstance(recipient, str) and recipient == self.test_email:
                found_recipient = {"email": recipient, "alerts": []}
                break
        
        assert found_recipient is not None, f"Added recipient {self.test_email} not found in settings"
        
        # New recipients should have all alerts enabled by default
        if isinstance(found_recipient, dict) and "alerts" in found_recipient:
            expected_alerts = ["sold_out", "rooms_available", "heads_up", "daily_status"]
            for alert in expected_alerts:
                assert alert in found_recipient["alerts"], f"New recipient should have {alert} enabled by default"
        
        print(f"✓ Added recipient {self.test_email} with all alerts enabled by default")
    
    def test_add_duplicate_recipient_fails(self):
        """POST /api/admin/email-alerts/recipients/add - Fails for duplicate email"""
        # First add
        requests.post(f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_email}")
        
        # Try to add duplicate
        response = requests.post(f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_email}")
        
        assert response.status_code == 400, f"Expected 400 for duplicate, got {response.status_code}"
        data = response.json()
        assert "detail" in data, "Error response should have detail"
        assert "already" in data["detail"].lower(), "Error should mention email already exists"
        
        print(f"✓ Correctly rejected duplicate recipient")
    
    def test_update_recipient_alerts(self):
        """PUT /api/admin/email-alerts/recipients/alerts - Updates specific recipient alerts"""
        # First add the recipient
        requests.post(f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_email}")
        
        # Update to only receive 'sold_out' and 'daily_status'
        new_alerts = ["sold_out", "daily_status"]
        response = requests.put(
            f"{BASE_URL}/api/admin/email-alerts/recipients/alerts?email={self.test_email}",
            json=new_alerts
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should have success message"
        
        # Verify the change was persisted
        settings_response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        settings = settings_response.json()
        
        found_recipient = None
        for recipient in settings["recipients"]:
            if isinstance(recipient, dict) and recipient.get("email") == self.test_email:
                found_recipient = recipient
                break
        
        assert found_recipient is not None, "Updated recipient should exist"
        assert set(found_recipient["alerts"]) == set(new_alerts), f"Alerts should be {new_alerts}, got {found_recipient['alerts']}"
        
        print(f"✓ Updated recipient alerts to {new_alerts}")
    
    def test_update_alerts_invalid_type(self):
        """PUT /api/admin/email-alerts/recipients/alerts - Rejects invalid alert types"""
        # First add the recipient
        requests.post(f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_email}")
        
        # Try invalid alert type
        invalid_alerts = ["sold_out", "invalid_alert_type"]
        response = requests.put(
            f"{BASE_URL}/api/admin/email-alerts/recipients/alerts?email={self.test_email}",
            json=invalid_alerts
        )
        
        assert response.status_code == 400, f"Expected 400 for invalid alert type, got {response.status_code}"
        
        print(f"✓ Correctly rejected invalid alert type")
    
    def test_update_alerts_nonexistent_email(self):
        """PUT /api/admin/email-alerts/recipients/alerts - Returns 404 for non-existent email"""
        fake_email = "nonexistent_email_12345@example.com"
        response = requests.put(
            f"{BASE_URL}/api/admin/email-alerts/recipients/alerts?email={fake_email}",
            json=["sold_out"]
        )
        
        assert response.status_code == 404, f"Expected 404 for non-existent email, got {response.status_code}"
        
        print(f"✓ Correctly returned 404 for non-existent recipient")
    
    def test_remove_recipient(self):
        """DELETE /api/admin/email-alerts/recipients - Removes recipient successfully"""
        # First add the recipient
        requests.post(f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_email}")
        
        # Remove it
        response = requests.delete(f"{BASE_URL}/api/admin/email-alerts/recipients?email={self.test_email}")
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}: {response.text}"
        data = response.json()
        assert "message" in data, "Response should have success message"
        
        # Verify it's gone
        settings_response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        settings = settings_response.json()
        
        for recipient in settings["recipients"]:
            email = recipient if isinstance(recipient, str) else recipient.get("email")
            assert email != self.test_email, f"Deleted recipient {self.test_email} should not exist"
        
        print(f"✓ Successfully removed recipient {self.test_email}")
    
    def test_remove_nonexistent_recipient(self):
        """DELETE /api/admin/email-alerts/recipients - Returns 404 for non-existent email"""
        fake_email = "nonexistent_email_99999@example.com"
        response = requests.delete(f"{BASE_URL}/api/admin/email-alerts/recipients?email={fake_email}")
        
        assert response.status_code == 404, f"Expected 404 for non-existent email, got {response.status_code}"
        
        print(f"✓ Correctly returned 404 for non-existent recipient deletion")
    
    def test_update_master_toggles(self):
        """POST /api/admin/email-alerts/settings - Updates master alert toggles"""
        # Get current settings
        current_response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        current = current_response.json()
        
        # Toggle sold_out_enabled
        new_value = not current.get("sold_out_enabled", True)
        
        response = requests.post(
            f"{BASE_URL}/api/admin/email-alerts/settings",
            json={"sold_out_enabled": new_value}
        )
        
        assert response.status_code == 200, f"Expected 200, got {response.status_code}"
        
        # Verify change persisted
        verify_response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        verify_data = verify_response.json()
        assert verify_data["sold_out_enabled"] == new_value, "Master toggle should be updated"
        
        # Restore original value
        requests.post(
            f"{BASE_URL}/api/admin/email-alerts/settings",
            json={"sold_out_enabled": current.get("sold_out_enabled", True)}
        )
        
        print(f"✓ Master toggle update works correctly")


class TestEmailAlertIntegration:
    """Test email alert integration scenarios"""
    
    @pytest.fixture(autouse=True)
    def setup(self):
        """Setup test data"""
        self.test_emails = [
            f"integration_test_1_{uuid.uuid4().hex[:6]}@example.com",
            f"integration_test_2_{uuid.uuid4().hex[:6]}@example.com"
        ]
        yield
        # Cleanup
        for email in self.test_emails:
            try:
                requests.delete(f"{BASE_URL}/api/admin/email-alerts/recipients?email={email}")
            except:
                pass
    
    def test_multiple_recipients_with_different_alerts(self):
        """Test adding multiple recipients with different alert preferences"""
        # Add first recipient with all alerts
        response1 = requests.post(
            f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_emails[0]}"
        )
        assert response1.status_code == 200
        
        # Add second recipient with all alerts
        response2 = requests.post(
            f"{BASE_URL}/api/admin/email-alerts/recipients/add?email={self.test_emails[1]}"
        )
        assert response2.status_code == 200
        
        # Update first to only have sold_out
        requests.put(
            f"{BASE_URL}/api/admin/email-alerts/recipients/alerts?email={self.test_emails[0]}",
            json=["sold_out"]
        )
        
        # Update second to have daily_status and heads_up
        requests.put(
            f"{BASE_URL}/api/admin/email-alerts/recipients/alerts?email={self.test_emails[1]}",
            json=["daily_status", "heads_up"]
        )
        
        # Verify each has their own settings
        settings_response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        settings = settings_response.json()
        
        recipient_alerts = {}
        for recipient in settings["recipients"]:
            if isinstance(recipient, dict):
                recipient_alerts[recipient["email"]] = set(recipient.get("alerts", []))
        
        assert self.test_emails[0] in recipient_alerts, "First test email should exist"
        assert self.test_emails[1] in recipient_alerts, "Second test email should exist"
        
        assert recipient_alerts[self.test_emails[0]] == {"sold_out"}, f"First recipient should only have sold_out"
        assert recipient_alerts[self.test_emails[1]] == {"daily_status", "heads_up"}, f"Second recipient should have daily_status and heads_up"
        
        print(f"✓ Multiple recipients with different preferences work correctly")
    
    def test_backward_compatibility_with_string_format(self):
        """Test that API handles old string format recipients gracefully"""
        # Get settings first
        response = requests.get(f"{BASE_URL}/api/admin/email-alerts/settings")
        data = response.json()
        
        # The API should return properly structured data regardless of internal format
        assert response.status_code == 200
        assert "recipients" in data
        
        # All recipients should be accessible
        for recipient in data["recipients"]:
            if isinstance(recipient, str):
                # Old format - still valid
                assert "@" in recipient, "String recipient should be an email"
            elif isinstance(recipient, dict):
                # New format
                assert "email" in recipient
                assert "alerts" in recipient
        
        print(f"✓ Backward compatibility with string format maintained")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
