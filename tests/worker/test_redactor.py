import pytest
from netraven.worker.redactor import redact, REDACTED_LINE_MARKER, DEFAULT_REDACTION_KEYWORDS

# Test cases: input string and expected output string
TEST_CASES = [
    # Basic redaction
    ("enable password mysecret\nline 2\nuser secret others\nline 4",
     f"[REDACTED LINE]\nline 2\n[REDACTED LINE]\nline 4"),
    # Case insensitivity
    ("Enable Password mysecret\nUser Secret others",
     f"[REDACTED LINE]\n[REDACTED LINE]"),
    # No keywords
    ("line one\nline two\nline three",
     "line one\nline two\nline three"),
    # Empty input
    ("", ""),
    # Only keywords
    ("password\nsecret",
     f"[REDACTED LINE]\n[REDACTED LINE]"),
    # Keyword as substring
    ("this line has password hidden\nsome secrets here\nthis line is fine",
     f"[REDACTED LINE]\n[REDACTED LINE]\nthis line is fine"),
    # Mixed content
    ("interface GigabitEthernet0/0\n description Link to Core\n ip address 10.1.1.1 255.255.255.0\n crypto pki token default removal timeout 0\n snmp-server user admin network-admin auth sha passwordIsNotHere priv aes 128\n snmp-server community READONLY ro",
     "interface GigabitEthernet0/0\n description Link to Core\n ip address 10.1.1.1 255.255.255.0\n crypto pki token default removal timeout 0\n[REDACTED LINE]\n snmp-server community READONLY ro"),
]

@pytest.mark.parametrize("input_str, expected_output", TEST_CASES)
def test_redact(input_str, expected_output):
    """Tests the redact function with various inputs (using default keywords)."""
    # Pass no config, so it uses defaults
    assert redact(input_str) == expected_output

def test_redaction_keywords_present():
    """Ensures the default keywords are present in the default list."""
    assert "password" in DEFAULT_REDACTION_KEYWORDS # Check against imported default list
    assert "secret" in DEFAULT_REDACTION_KEYWORDS

def test_redacted_line_marker():
    """Ensures the marker is the expected string."""
    assert REDACTED_LINE_MARKER == "[REDACTED LINE]"
