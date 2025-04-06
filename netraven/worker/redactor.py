import re
from typing import List, Optional, Dict, Any

# Default keywords to redact (case-insensitive)
DEFAULT_REDACTION_KEYWORDS = ["password", "secret"]
REDACTED_LINE_MARKER = "[REDACTED LINE]"

def redact(output: str, config: Optional[Dict[str, Any]] = None) -> str:
    """Redacts sensitive information from the given output string.

    Iterates through each line of the output. If a line contains
    any of the keywords (case-insensitive) defined in the configuration
    (under worker.redaction.patterns) or the defaults, the entire line is
    replaced with REDACTED_LINE_MARKER.

    Args:
        output: The multi-line string output from a device command.
        config: The loaded application configuration dictionary (optional).

    Returns:
        A string with sensitive lines redacted.
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
