"""
NetRaven Jobs Module.

This module contains functionality related to job execution,
including device backup jobs, configuration deployment jobs,
and job scheduling.
"""

from netraven.jobs.device_connector import JobDeviceConnector, backup_device_config
from netraven.jobs.gateway_connector import (
    check_device_connectivity_via_gateway,
    connect_device_via_gateway,
    execute_command_via_gateway,
    backup_device_config_via_gateway
)
from netraven.jobs.device_logging import (
    start_job_session,
    end_job_session,
    register_device,
    log_device_connect,
    log_device_connect_success,
    log_device_connect_failure,
    log_device_command,
    log_device_response,
    log_device_disconnect,
    log_backup_success,
    log_backup_failure
)
from netraven.jobs.scheduler import BackupScheduler, get_scheduler

__all__ = [
    'JobDeviceConnector',
    'backup_device_config',
    'check_device_connectivity_via_gateway',
    'connect_device_via_gateway',
    'execute_command_via_gateway',
    'backup_device_config_via_gateway',
    'start_job_session',
    'end_job_session',
    'register_device',
    'log_device_connect',
    'log_device_connect_success',
    'log_device_connect_failure',
    'log_device_command',
    'log_device_response',
    'log_device_disconnect',
    'log_backup_success',
    'log_backup_failure',
    'BackupScheduler',
    'get_scheduler'
] 