"""
Backup file operations module for NetRaven.

This module provides functions for storing, retrieving, and comparing backup files.
"""

import os
import difflib
from datetime import datetime
from typing import Dict, Any, Optional, List, Tuple

from netraven.core.storage import get_storage_backend, hash_content
from netraven.core.config import get_config, get_backup_filename_format
import logging

logger = logging.getLogger(__name__)

def construct_backup_path(device_hostname: str, device_id: str, timestamp: Optional[datetime] = None) -> str:
    """
    Construct a path for storing a backup file.
    
    Args:
        device_hostname: The hostname of the device
        device_id: The ID of the device
        timestamp: Optional timestamp for the backup (defaults to current time)
    
    Returns:
        str: The constructed file path
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    # Format: device_id/YYYY/MM/hostname_YYYYMMDD_HHMMSS.txt
    date_path = timestamp.strftime("%Y/%m")
    file_name = f"{device_hostname}_{timestamp.strftime('%Y%m%d_%H%M%S')}.txt"
    
    return os.path.join(device_id, date_path, file_name)

def store_backup_content(device_hostname: str, device_id: str, content: str, timestamp: Optional[datetime] = None) -> Dict[str, Any]:
    """
    Store backup content in the configured storage backend.
    
    Args:
        device_hostname: The hostname of the device
        device_id: The ID of the device
        content: The content to store
        timestamp: Optional timestamp for the backup (defaults to current time)
    
    Returns:
        Dict[str, Any]: Metadata about the stored backup including file_path, file_size, and content_hash
    
    Raises:
        Exception: If there's an error storing the backup
    """
    if timestamp is None:
        timestamp = datetime.utcnow()
    
    try:
        # Get the storage backend from configuration
        config = get_config()
        storage = get_storage_backend(config)
        
        # Construct the file path
        file_path = construct_backup_path(device_hostname, device_id, timestamp)
        
        # Calculate content hash and size
        content_hash = hash_content(content)
        file_size = len(content.encode('utf-8'))
        
        # Store the content
        success = storage.write_file(content, file_path)
        if not success:
            raise RuntimeError(f"Failed to write backup file: {file_path}")
        
        logger.info(f"Successfully stored backup for device {device_hostname} at {file_path}")
        
        return {
            "file_path": file_path,
            "file_size": file_size,
            "content_hash": content_hash,
            "timestamp": timestamp
        }
    
    except Exception as e:
        logger.error(f"Error storing backup for device {device_hostname}: {str(e)}")
        raise

def retrieve_backup_content(file_path: str) -> Optional[str]:
    """
    Retrieve backup content from the configured storage backend.
    
    Args:
        file_path: The path to the backup file
    
    Returns:
        Optional[str]: The backup content, or None if the file could not be read
    """
    try:
        # Get the storage backend from configuration
        config = get_config()
        storage = get_storage_backend(config)
        
        # Read the content
        content = storage.read_file(file_path)
        
        if content is None:
            logger.error(f"Failed to read backup file: {file_path}")
            return None
        
        logger.info(f"Successfully retrieved backup from {file_path}")
        return content
    
    except Exception as e:
        logger.error(f"Error retrieving backup from {file_path}: {str(e)}")
        return None

def delete_backup_file(file_path: str) -> bool:
    """
    Delete a backup file from the configured storage backend.
    
    Args:
        file_path: The path to the backup file
    
    Returns:
        bool: True if the file was deleted, False otherwise
    """
    try:
        # Get the storage backend from configuration
        config = get_config()
        storage = get_storage_backend(config)
        
        # For local storage, we can use the filesystem to delete
        if isinstance(storage, __import__('netraven.core.storage').core.storage.LocalStorageBackend):
            full_path = os.path.join(storage.base_path, file_path)
            if os.path.exists(full_path):
                os.remove(full_path)
                logger.info(f"Successfully deleted backup file: {file_path}")
                return True
            else:
                logger.warning(f"Backup file not found: {file_path}")
                return False
        
        # For S3 and other backends, we'd need to implement specific delete methods
        # Currently, we'll log a warning and return False
        logger.warning(f"Delete operation not implemented for storage backend type: {type(storage).__name__}")
        return False
    
    except Exception as e:
        logger.error(f"Error deleting backup file {file_path}: {str(e)}")
        return False

def compare_backup_content(content1: str, content2: str) -> Dict[str, Any]:
    """
    Compare two backup contents and generate a diff.
    
    Args:
        content1: The first backup content
        content2: The second backup content
    
    Returns:
        Dict[str, Any]: Comparison results including diff lines and summary
    """
    try:
        # Split content into lines
        lines1 = content1.splitlines()
        lines2 = content2.splitlines()
        
        # Generate unified diff
        differ = difflib.unified_diff(
            lines1, 
            lines2,
            lineterm=''
        )
        
        # Collect diff lines
        diff_lines = list(differ)
        
        # Count changes
        additions = len([line for line in diff_lines if line.startswith('+')])
        deletions = len([line for line in diff_lines if line.startswith('-')])
        
        # Format as HTML with highlighting
        html_diff = difflib.HtmlDiff().make_file(lines1, lines2)
        
        return {
            "diff": diff_lines,
            "html_diff": html_diff,
            "summary": {
                "lines_added": additions,
                "lines_removed": deletions,
                "total_changes": additions + deletions
            }
        }
    
    except Exception as e:
        logger.error(f"Error comparing backup contents: {str(e)}")
        return {
            "diff": [],
            "html_diff": "",
            "summary": {
                "lines_added": 0,
                "lines_removed": 0,
                "total_changes": 0,
                "error": str(e)
            }
        } 