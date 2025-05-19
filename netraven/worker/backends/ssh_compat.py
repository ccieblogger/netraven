"""
Utility for enabling legacy SSH KEX and MAC algorithms for Paramiko/Netmiko.
"""

def enable_legacy_kex(kex_list=None, mac_list=None, logger=None, job_id=None, device_id=None):
    """
    Patch Paramiko's preferred KEX and MACs at runtime to allow legacy algorithms.
    Args:
        kex_list: List of KEX algorithms to add (or None for default legacy set)
        mac_list: List of MAC algorithms to add (or None for default legacy set)
        logger: Optional logger for warnings
        job_id: Optional job ID for logging
        device_id: Optional device ID for logging
    """
    try:
        import paramiko
        # Default legacy KEX and MACs if not provided
        default_kex = [
            'diffie-hellman-group14-sha1',
            'diffie-hellman-group1-sha1',
            'diffie-hellman-group-exchange-sha1'
        ]
        default_macs = [
            'hmac-sha1',
            'hmac-md5'
        ]
        kex_to_add = kex_list if kex_list else default_kex
        macs_to_add = mac_list if mac_list else default_macs
        # Patch KEX
        for kex in kex_to_add:
            if kex not in paramiko.transport.Transport._preferred_kex:
                paramiko.transport.Transport._preferred_kex = (
                    paramiko.transport.Transport._preferred_kex + (kex,)
                )
        # Patch MACs
        for mac in macs_to_add:
            if mac not in paramiko.transport.Transport._preferred_macs:
                paramiko.transport.Transport._preferred_macs = (
                    paramiko.transport.Transport._preferred_macs + (mac,)
                )
        if logger:
            logger.log(
                "Legacy SSH security algorithms have been enabled! See NetRaven docs for details.",
                level="WARNING",
                destinations=["stdout", "file", "db"],
                log_type="job",
                job_id=job_id,
                device_id=device_id
            )
    except Exception:
        if logger:
            logger.log(
                "Failed to patch Paramiko for legacy SSH algorithms.",
                level="WARNING",
                destinations=["stdout", "file", "db"],
                log_type="job",
                job_id=job_id,
                device_id=device_id
            )
        pass  # If paramiko is not available or patch fails, ignore
