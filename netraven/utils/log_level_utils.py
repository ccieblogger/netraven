def log_level_to_status(level) -> str:
    """
    Maps a log level (str or enum) to a status string ('success', 'failure', 'warning', 'unknown').
    """
    if not level:
        return "unknown"
    # Convert enum to string if needed
    if hasattr(level, 'value'):
        level = level.value
    level = str(level).lower()
    if level in ("info", "success", "debug"):
        return "success"
    elif level in ("error", "failure", "critical"):
        return "failure"
    elif level == "warning":
        return "warning"
    return "unknown" 