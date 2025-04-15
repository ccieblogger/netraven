"""Redaction utilities for sensitive information in device outputs.

This module provides functionality to identify and redact sensitive information
from network device command outputs, such as passwords, secrets, and other
confidential data. It uses pattern matching to detect sensitive content and
replaces entire lines containing such content with a redaction marker.

The redaction system helps prevent inadvertent exposure of sensitive information
in logs, configurations, and other outputs from network devices.
"""

import re
from typing import List, Optional, Dict, Any

# Default keywords to redact (case-insensitive)
DEFAULT_REDACTION_KEYWORDS = ["password", "secret"]
REDACTED_LINE_MARKER = "[REDACTED LINE]"

def redact(output: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Redact sensitive information from device command output.

    This function scans the provided output text line by line, looking for
    sensitive information patterns that match the configured keywords.
    When a match is found, the entire line is replaced with a redaction marker.
    
    The function can use either default redaction patterns or custom patterns
    specified in the application configuration.

    Args:
        output: The multi-line string output from a device command
        config: Optional configuration dictionary with the following structure:
               {
                 "worker": {
                   "redaction": {
                     "patterns": List[str]  # List of keywords to redact
                   }
                 }
               }
               If not provided or if the structure is incorrect, default patterns are used

    Returns:
        A string with sensitive lines redacted, preserving the original line count and structure

    Notes:
        - The redaction is case-insensitive
        - Entire lines are redacted, not just the sensitive portions
        - Default redaction keywords are "password" and "secret"
    """
    if not output:
        return ""

    keywords = DEFAULT_REDACTION_KEYWORDS
    if config and isinstance(config.get("worker", {}).get("redaction", {}).get("patterns"), list):
        loaded_keywords = config["worker"]["redaction"]["patterns"]
        if loaded_keywords: # Ensure it's not an empty list from config
            keywords = loaded_keywords
            print(f"Using redaction keywords from config: {keywords}")
        else:
             print("Config provided empty redaction keywords list, using defaults.")
    else:
        print(f"Using default redaction keywords: {keywords}")


    lines = []
    # Simple case-insensitive check
    if keywords: # Only redact if there are keywords
        for line in output.splitlines():
            if any(keyword.lower() in line.lower() for keyword in keywords):
                lines.append(REDACTED_LINE_MARKER)
            else:
                lines.append(line)
    else: # If no keywords defined, return original output split/joined
        lines = output.splitlines()

    return "\n".join(lines)
