"""
Unified, Multi-Destination Logger Utility for NetRaven

This module provides a centralized logger supporting configurable, multi-destination logging:
- File (with rotation, JSON/plain)
- Stdout (human-readable)
- Redis (real-time streaming)
- DB (wraps save_job_log/save_connection_log)

Initialization is config-driven. All modules should import and use the same logger instance.
"""

import logging
from logging.handlers import TimedRotatingFileHandler
from typing import Optional, List, Dict, Any
import os
import datetime
import traceback
import json
from netraven.config.logger_config import get_logger_config
import sys

# Redis and DB log utils
try:
    from redis import Redis
except ImportError:
    Redis = None
from netraven.db.log_utils import save_log

class UnifiedLogger:
    """
    Unified logger for NetRaven supporting multiple destinations per log event.
    """
    class StdoutFormatter(logging.Formatter):
        def format(self, record):
            # Extract extra fields if present
            level = getattr(record, 'levelname', 'INFO')
            timestamp = self.formatTime(record, self.datefmt) if hasattr(self, 'datefmt') else datetime.datetime.utcnow().isoformat() + 'Z'
            # Try to get 'source' from record or fallback to '-'
            source = getattr(record, 'source', None)
            if not source and hasattr(record, 'args') and isinstance(record.args, dict):
                source = record.args.get('source', '-')
            if not source:
                source = '-'
            msg = record.getMessage()
            return f"[UnifiedLogger][{level}][{timestamp}][{source}] {msg}"

    def __init__(self, config: dict):
        self.config = config
        self.file_logger = None
        self.stdout_logger = None
        self.redis_config = None
        self.db_enabled = False
        self.redis_client = None
        print(f"[UnifiedLogger DEBUG] Logger initialized with config: {self.config}")
        self._init_destinations()

    def _init_destinations(self):
        """Initialize log destinations based on config."""
        logging_config = self.config or {}

        # --- File Logger Setup ---
        file_cfg = logging_config.get('file', {})
        if file_cfg.get('enabled', False):
            file_path = file_cfg.get('path', '/data/logs/netraven.log')
            file_level = getattr(logging, file_cfg.get('level', 'INFO').upper(), logging.INFO)
            file_format = file_cfg.get('format', 'json')
            rotation = file_cfg.get('rotation', {})
            when = rotation.get('when', 'midnight')
            interval = int(rotation.get('interval', 1))
            backup_count = int(rotation.get('backupCount', 7))
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            handler = TimedRotatingFileHandler(
                file_path, when=when, interval=interval, backupCount=backup_count, encoding='utf-8'
            )
            if file_format == 'json':
                formatter = logging.Formatter('{"timestamp": "%(asctime)s", "level": "%(levelname)s", "message": %(message)s}')
            else:
                formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            handler.setLevel(file_level)
            self.file_logger = logging.getLogger('netraven.file')
            self.file_logger.setLevel(file_level)
            self.file_logger.addHandler(handler)
            self.file_logger.propagate = False
        else:
            self.file_logger = None

        # --- Stdout Logger Setup ---
        stdout_cfg = logging_config.get('stdout', {})
        if stdout_cfg.get('enabled', False):
            stdout_level = getattr(logging, stdout_cfg.get('level', 'INFO').upper(), logging.INFO)
            handler = logging.StreamHandler(sys.stdout)
            handler.setLevel(stdout_level)
            # Use custom formatter
            handler.setFormatter(self.StdoutFormatter())
            self.stdout_logger = logging.getLogger('netraven.stdout')
            self.stdout_logger.setLevel(stdout_level)
            self.stdout_logger.addHandler(handler)
            self.stdout_logger.propagate = False
        else:
            self.stdout_logger = None

        # --- Redis Config (for container-to-container use) ---
        redis_cfg = logging_config.get('redis', {})
        if redis_cfg.get('enabled', False) and Redis is not None:
            self.redis_config = redis_cfg
            try:
                self.redis_client = Redis(
                    host=redis_cfg.get('host', 'redis'),
                    port=redis_cfg.get('port', 6379),
                    db=redis_cfg.get('db', 0),
                    password=redis_cfg.get('password'),
                    decode_responses=True
                )
            except Exception as e:
                self.redis_client = None
                print(f"[LOGGER WARNING] Could not connect to Redis: {e}")
        else:
            self.redis_config = None
            self.redis_client = None

        # --- DB Logging Enabled ---
        db_cfg = logging_config.get('db', {})
        self.db_enabled = db_cfg.get('enabled', False)

    def log(self, message: str, level: str = "INFO", destinations: Optional[List[str]] = None,
            job_id: Optional[int] = None, device_id: Optional[int] = None, extra: Optional[Dict[str, Any]] = None,
            source: Optional[str] = None, is_connection_log: bool = False, **kwargs):
        """
        Log a message to one or more destinations.

        Parameters:
            message (str): The log message.
            level (str, optional): Log level (e.g., "INFO", "ERROR"). Defaults to "INFO".
            destinations (List[str], optional): List of destinations ("stdout", "file", "redis", "db"). If None, uses enabled destinations from config.
            job_id (int, optional): Associated job ID.
            device_id (int, optional): Associated device ID.
            extra (dict, optional): Arbitrary structured data to include in the log record. This is the intended way to pass custom metadata for jobs or other log events. The contents of 'extra' will be stored in the database 'meta' column (JSONB) and made available for UI/API consumption. Use this to pass any job-specific or structured data you want to persist and view in the UI.
            source (str, optional): Source module or service name.
            is_connection_log (bool, optional): If True, log_type defaults to "connection" if not otherwise specified.
            log_type (str, optional): Log type for DB logging ("job", "connection", "session", etc.). Pass as a keyword argument.
            Any additional keyword arguments (**kwargs) will be added to the log record and, if logging to DB, stored in the log entry.

        Example:
            logger.log(
                "Device session started",
                level="INFO",
                log_type="session",  # Sets the log_type for DB logging
                job_id=123,
                device_id=456,
                source="worker.executor",
                extra={"custom_field": "value", "result": {"status": "success", "duration": 12.5}},
                custom_param="custom_value"  # This will be included in the log record but not in the DB meta column unless included in 'extra'.
            )
        """
        # Build log record with metadata
        record = {
            "timestamp": datetime.datetime.utcnow().isoformat() + 'Z',
            "level": level.upper(),
            "message": message,
            "job_id": job_id,
            "device_id": device_id,
            "source": source,
            "extra": extra or {},
        }
        # Add any additional kwargs to record
        record.update(kwargs)

        # Determine destinations
        default_dests = []
        if self.stdout_logger:
            default_dests.append("stdout")
        if self.file_logger:
            default_dests.append("file")
        if self.redis_client:
            default_dests.append("redis")
        if self.db_enabled:
            default_dests.append("db")
        if destinations is None:
            destinations = default_dests

        errors = []
        for dest in destinations:
            try:
                if dest == "file" and self.file_logger:
                    self._log_to_file(record)
                elif dest == "stdout" and self.stdout_logger:
                    self._log_to_stdout(record)
                elif dest == "redis" and self.redis_client:
                    self._log_to_redis(record)
                elif dest == "db" and self.db_enabled:
                    self._log_to_db(record, is_connection_log=is_connection_log)
            except Exception as e:
                errors.append((dest, str(e), traceback.format_exc()))

        # Fallback: If all destinations failed, print to stdout
        if errors and len(errors) == len(destinations):
            print(f"[LOGGER FALLBACK] {record['timestamp']} - {record['level']} - {record['message']}")
            for dest, err, tb in errors:
                print(f"[LOGGER ERROR] Destination: {dest}, Error: {err}\n{tb}")

    # --- Destination Handlers ---
    def _log_to_file(self, record: dict):
        """Log to file (with rotation, JSON/plain)."""
        msg = record["message"]
        level = getattr(logging, record["level"].upper(), logging.INFO)
        # Use the file logger to log the message
        self.file_logger.log(level, msg)

    def _log_to_stdout(self, record: dict):
        """Log to stdout (human-readable)."""
        msg = record["message"]
        level = getattr(logging, record["level"].upper(), logging.INFO)
        # Pass 'source' as extra for the formatter
        extra = {"source": record.get("source", "-")}
        self.stdout_logger.log(level, msg, extra=extra)

    def _log_to_redis(self, record: dict):
        """Log to Redis (real-time streaming)."""
        if not self.redis_client or not self.redis_config:
            return
        channel = self.redis_config.get('channel_prefix', 'netraven-logs')
        try:
            self.redis_client.publish(channel, json.dumps(record))
        except Exception as e:
            print(f"[LOGGER ERROR] Failed to publish log to Redis: {e}")

    def _log_to_db(self, record: dict, is_connection_log: bool = False):
        print(f"[UnifiedLogger DEBUG] _log_to_db called with record: {record}")
        try:
            # Determine log_type
            log_type = record.get("log_type")
            if not log_type:
                log_type = "connection" if is_connection_log else "system"
            # Use save_log for all DB log events
            save_log(
                message=record.get("message"),
                log_type=log_type,
                level=record.get("level", "INFO"),
                job_id=record.get("job_id"),
                device_id=record.get("device_id"),
                source=record.get("source"),
                meta=record.get("extra")
            )
        except Exception as e:
            print(f"[LOGGER ERROR] Failed to save log to DB: {e}")

_unified_logger_instance = None

def get_unified_logger() -> UnifiedLogger:
    """
    Returns a singleton instance of UnifiedLogger, initialized with config from the logger_config module.
    Usage: from netraven.utils.unified_logger import get_unified_logger
           logger = get_unified_logger()
    """
    global _unified_logger_instance
    if _unified_logger_instance is None:
        config = get_logger_config()
        _unified_logger_instance = UnifiedLogger(config)
    return _unified_logger_instance

# TODO: Provide a global logger instance, initialized at app startup
# Example:
# config = load_config().get('logging', {})
# unified_logger = UnifiedLogger(config) 