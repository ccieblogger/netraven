def save_connection_log(device_id: int, job_id: int, log: str) -> None:
    """Saves the connection log for a specific device and job."""
    # Requires DB models (ConnectionLog) and session (get_db)
    pass

def save_job_log(device_id: int, job_id: int, message: str, success: bool) -> None:
    """Saves a job log message for a specific device and job."""
    # Requires DB models (JobLog) and session (get_db)
    pass
