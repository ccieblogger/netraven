"""
Unit tests for utility functions.
"""
import pytest
import uuid
import re
from tests.utils.test_helpers import generate_unique_name


def test_generate_unique_name():
    """Test the generate_unique_name helper function."""
    # Test with default prefix
    name1 = generate_unique_name()
    assert name1.startswith("test-")
    assert len(name1) > 10  # Should be "test-" plus a UUID part
    
    # Test with custom prefix
    name2 = generate_unique_name("device")
    assert name2.startswith("device-")
    
    # Test that names are unique
    name3 = generate_unique_name()
    assert name1 != name3
    
    # Test format
    uuid_pattern = r'^[a-z]+-[0-9a-f]{8}$'
    assert re.match(uuid_pattern, name1)
    assert re.match(uuid_pattern, name2)
    assert re.match(uuid_pattern, name3)


def test_uuid_generation():
    """Test UUID generation for test helpers."""
    # Generate two UUIDs and check they're different
    id1 = uuid.uuid4().hex[:8]
    id2 = uuid.uuid4().hex[:8]
    assert id1 != id2
    
    # Check format
    assert len(id1) == 8
    assert len(id2) == 8
    
    # Check they're valid hex strings
    int(id1, 16)  # Will raise ValueError if not valid hex
    int(id2, 16)  # Will raise ValueError if not valid hex 