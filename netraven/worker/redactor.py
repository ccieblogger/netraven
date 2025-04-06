import re

# Default keywords to redact (case-insensitive)
# Future: Load these from configuration
REDACTION_KEYWORDS = ["password", "secret"]
REDACTED_LINE_MARKER = "[REDACTED LINE]"

def redact(output: str) -> str:
    """Redacts sensitive information from the given output string.

    Iterates through each line of the output. If a line contains
    any of the keywords defined in REDACTION_KEYWORDS (case-insensitive),
    the entire line is replaced with REDACTED_LINE_MARKER.

    Args:
        output: The multi-line string output from a device command.

    Returns:
        A string with sensitive lines redacted.
    """
    if not output:
        return ""

    lines = []
    # Pre-compile regex for keywords for slight efficiency if needed, but simple check is fine
    # pattern = re.compile('|'.join(REDACTION_KEYWORDS), re.IGNORECASE)

    for line in output.splitlines():
        # Simple case-insensitive check
        if any(keyword.lower() in line.lower() for keyword in REDACTION_KEYWORDS):
            lines.append(REDACTED_LINE_MARKER)
        else:
            lines.append(line)

    return "\n".join(lines)
