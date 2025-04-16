"""Unit tests for the device credential resolver module."""

import pytest
from unittest.mock import MagicMock, patch
from sqlalchemy.orm import Session

from netraven.services.device_credential_resolver import (
    DeviceWithCredentials,
    resolve_device_credential,
    resolve_device_credentials_batch,
    track_credential_selection
)
from netraven.db import models

class TestDeviceWithCredentials:
    def test_initialization(self):
        """Test that attributes are properly copied from original device."""
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.ip_address = "192.168.1.1"
        
        device_with_creds = DeviceWithCredentials(
            device=mock_device,
            username="test-user",
            password="test-pass"
        )
        
        # Check that properties are set correctly
        assert device_with_creds.username == "test-user"
        assert device_with_creds.password == "test-pass"
        
        # Check that device attributes are copied
        assert device_with_creds.id == mock_device.id
        assert device_with_creds.hostname == mock_device.hostname
        assert device_with_creds.ip_address == mock_device.ip_address
        
    def test_overriding_existing_credentials(self):
        """Test that existing username/password are overridden."""
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.username = "old-user"
        mock_device.password = "old-pass"
        
        device_with_creds = DeviceWithCredentials(
            device=mock_device,
            username="new-user",
            password="new-pass"
        )
        
        # Check that properties are set correctly from constructor, not original device
        assert device_with_creds.username == "new-user"
        assert device_with_creds.password == "new-pass"


class TestResolveDeviceCredential:
    def test_no_matching_credentials(self, monkeypatch):
        """Test handling when no credentials match."""
        # Setup mocks
        mock_get_creds = MagicMock(return_value=[])
        mock_track = MagicMock()
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.get_matching_credentials_for_device", 
            mock_get_creds
        )
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.track_credential_selection", 
            mock_track
        )
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_db = MagicMock(spec=Session)
        
        # Should raise ValueError
        with pytest.raises(ValueError):
            resolve_device_credential(mock_device, mock_db)
        
        # Should not track any credential selection
        mock_track.assert_not_called()
    
    def test_with_matching_credentials(self, monkeypatch):
        """Test with one matching credential."""
        # Create credential mock
        mock_cred = MagicMock(spec=models.Credential)
        mock_cred.id = 5
        mock_cred.username = "test-user"
        mock_cred.password = "test-pass"
        mock_cred.priority = 10
        
        # Setup mocks
        mock_get_creds = MagicMock(return_value=[mock_cred])
        mock_track = MagicMock()
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.get_matching_credentials_for_device", 
            mock_get_creds
        )
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.track_credential_selection", 
            mock_track
        )
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db)
        
        # Check that result is a DeviceWithCredentials
        assert isinstance(result, DeviceWithCredentials)
        assert result.username == "test-user"
        assert result.password == "test-pass"
        
        # Should track credential selection
        mock_track.assert_called_once_with(mock_db, 1, 5, None)
    
    def test_multiple_credentials_priority_order(self, monkeypatch):
        """Test that credential with lowest priority number is selected."""
        # Create credential mocks
        mock_cred1 = MagicMock(spec=models.Credential)
        mock_cred1.id = 5
        mock_cred1.username = "high-priority"
        mock_cred1.password = "high-pass"
        mock_cred1.priority = 10
        
        mock_cred2 = MagicMock(spec=models.Credential)
        mock_cred2.id = 6
        mock_cred2.username = "low-priority"
        mock_cred2.password = "low-pass"
        mock_cred2.priority = 100
        
        # Setup mocks
        mock_get_creds = MagicMock(return_value=[mock_cred1, mock_cred2])
        mock_track = MagicMock()
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.get_matching_credentials_for_device", 
            mock_get_creds
        )
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.track_credential_selection", 
            mock_track
        )
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db)
        
        # Should select the first credential (highest priority)
        assert result.username == "high-priority"
        assert result.password == "high-pass"
        
        # Should track credential selection for the selected credential
        mock_track.assert_called_once_with(mock_db, 1, 5, None)
    
    def test_device_with_existing_credentials(self):
        """Test that existing credentials are preserved if skip_if_has_credentials=True."""
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.username = "existing-user"
        mock_device.password = "existing-pass"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db)
        
        # Should return original device without changes
        assert result is mock_device
        assert result.username == "existing-user"
        assert result.password == "existing-pass"
        
    def test_force_credential_resolution(self, monkeypatch):
        """Test force credential resolution by setting skip_if_has_credentials=False."""
        # Create credential mock
        mock_cred = MagicMock(spec=models.Credential)
        mock_cred.id = 5
        mock_cred.username = "test-user"
        mock_cred.password = "test-pass"
        mock_cred.priority = 10
        
        # Setup mocks
        mock_get_creds = MagicMock(return_value=[mock_cred])
        mock_track = MagicMock()
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.get_matching_credentials_for_device", 
            mock_get_creds
        )
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.track_credential_selection", 
            mock_track
        )
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.username = "existing-user"
        mock_device.password = "existing-pass"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db, skip_if_has_credentials=False)
        
        # Should return DeviceWithCredentials with new credentials
        assert isinstance(result, DeviceWithCredentials)
        assert result.username == "test-user"
        assert result.password == "test-pass"
        
        # Should call get_matching_credentials_for_device and track selection
        mock_get_creds.assert_called_once_with(mock_db, 1)
        mock_track.assert_called_once_with(mock_db, 1, 5, None)
        
    def test_no_credentials_but_device_has_credentials(self, monkeypatch):
        """Test that if no credentials match but device has credentials, it returns the device as is."""
        # Setup mocks
        mock_get_creds = MagicMock(return_value=[])
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.get_matching_credentials_for_device", 
            mock_get_creds
        )
        
        mock_device = MagicMock()
        mock_device.id = 1
        mock_device.hostname = "test-device"
        mock_device.username = "existing-user"
        mock_device.password = "existing-pass"
        mock_db = MagicMock(spec=Session)
        
        result = resolve_device_credential(mock_device, mock_db, skip_if_has_credentials=False)
        
        # Should return original device without changes
        assert result is mock_device
        assert result.username == "existing-user"
        assert result.password == "existing-pass"


class TestResolveDeviceCredentialsBatch:
    def test_batch_resolution(self, monkeypatch):
        """Test that batch function processes all devices."""
        mock_device1 = MagicMock()
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        
        mock_device2 = MagicMock()
        mock_device2.id = 2
        mock_device2.hostname = "device2"
        
        # Setup mock with side effect
        mock_resolve = MagicMock(side_effect=lambda d, *args, **kwargs: d)
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.resolve_device_credential", 
            mock_resolve
        )
        
        mock_db = MagicMock(spec=Session)
        
        results = resolve_device_credentials_batch([mock_device1, mock_device2], mock_db)
        
        # Should return both devices
        assert len(results) == 2
        assert mock_device1 in results
        assert mock_device2 in results
        
        # Should have called resolve_device_credential for each device
        assert mock_resolve.call_count == 2
    
    def test_batch_with_errors(self, monkeypatch):
        """Test that batch function handles errors for individual devices."""
        mock_device1 = MagicMock()
        mock_device1.id = 1
        mock_device1.hostname = "device1"
        
        mock_device2 = MagicMock()
        mock_device2.id = 2
        mock_device2.hostname = "device2"
        
        # Setup mock with side effect
        def side_effect(device, *args, **kwargs):
            if device.id == 1:
                return device
            else:
                raise ValueError("Test error")
                
        mock_resolve = MagicMock(side_effect=side_effect)
        
        # Apply monkeypatching
        monkeypatch.setattr(
            "netraven.services.device_credential_resolver.resolve_device_credential", 
            mock_resolve
        )
        
        mock_db = MagicMock(spec=Session)
        
        results = resolve_device_credentials_batch([mock_device1, mock_device2], mock_db)
        
        # Should return only the successful device
        assert len(results) == 1
        assert mock_device1 in results
        assert mock_device2 not in results


class TestTrackCredentialSelection:
    def test_tracking_updates_last_used(self, monkeypatch):
        """Test that tracking updates the last_used timestamp."""
        mock_db = MagicMock(spec=Session)
        mock_credential = MagicMock()
        
        # Setup query chain for retrieving the credential
        mock_credential_model_query = MagicMock()
        mock_credential_model_query.filter.return_value = MagicMock()
        mock_credential_model_query.filter().first.return_value = mock_credential
        mock_db.query.return_value = mock_credential_model_query
        
        # Call the function
        track_credential_selection(mock_db, 1, 5, 10)
        
        # Verify that last_used was updated and db.commit was called
        assert mock_credential.last_used is not None
        mock_db.commit.assert_called_once()
        
    def test_tracking_handles_missing_credential(self):
        """Test that tracking gracefully handles missing credentials."""
        mock_db = MagicMock(spec=Session)
        
        # Setup query chain for retrieving the credential (not found)
        mock_credential_model_query = MagicMock()
        mock_credential_model_query.filter.return_value = MagicMock()
        mock_credential_model_query.filter().first.return_value = None
        mock_db.query.return_value = mock_credential_model_query
        
        # Call the function - should not raise exceptions
        track_credential_selection(mock_db, 1, 5, 10)
        
        # Verify that db.commit was not called
        mock_db.commit.assert_not_called()
        
    def test_tracking_handles_exceptions(self):
        """Test that tracking gracefully handles exceptions."""
        mock_db = MagicMock(spec=Session)
        
        # Setup query to raise an exception
        mock_db.query.side_effect = Exception("Test exception")
        
        # Call the function - should not propagate exceptions
        track_credential_selection(mock_db, 1, 5, 10)
        
        # Verify that db.commit was not called
        mock_db.commit.assert_not_called() 