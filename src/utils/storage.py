"""
Storage backend module for handling different types of backup storage locations.

This module provides a unified interface for storing backups in different locations:
- Local filesystem
- Network mounted filesystems
- Amazon S3
- (Extensible for other storage backends)
"""

import os
from pathlib import Path
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, BinaryIO
import boto3
from botocore.exceptions import ClientError
import logging

logger = logging.getLogger(__name__)

class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def write_file(self, content: str, filepath: str) -> bool:
        """Write content to a file."""
        pass
    
    @abstractmethod
    def read_file(self, filepath: str) -> Optional[str]:
        """Read content from a file."""
        pass
    
    @abstractmethod
    def ensure_directory(self, directory: str) -> bool:
        """Ensure a directory exists."""
        pass

class LocalStorageBackend(StorageBackend):
    """Storage backend for local and network mounted filesystems."""
    
    def __init__(self, base_path: str):
        """
        Initialize local storage backend.
        
        Args:
            base_path: Base directory path
        """
        self.base_path = Path(base_path).expanduser().resolve()
    
    def write_file(self, content: str, filepath: str) -> bool:
        """
        Write content to a local file.
        
        Args:
            content: Content to write
            filepath: Relative path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            full_path = self.base_path / filepath
            full_path.parent.mkdir(parents=True, exist_ok=True)
            with open(full_path, 'w') as f:
                f.write(content)
            return True
        except Exception as e:
            logger.error(f"Error writing to file {filepath}: {e}")
            return False
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read content from a local file.
        
        Args:
            filepath: Relative path to the file
            
        Returns:
            str: File content if successful, None otherwise
        """
        try:
            full_path = self.base_path / filepath
            with open(full_path, 'r') as f:
                return f.read()
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {e}")
            return None
    
    def ensure_directory(self, directory: str) -> bool:
        """
        Ensure a directory exists in the local filesystem.
        
        Args:
            directory: Relative path to the directory
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            full_path = self.base_path / directory
            full_path.mkdir(parents=True, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Error creating directory {directory}: {e}")
            return False

class S3StorageBackend(StorageBackend):
    """Storage backend for Amazon S3."""
    
    def __init__(self, bucket: str, prefix: str = "", **kwargs):
        """
        Initialize S3 storage backend.
        
        Args:
            bucket: S3 bucket name
            prefix: Key prefix (like a directory)
            **kwargs: Additional arguments for boto3.client
        """
        self.bucket = bucket
        self.prefix = prefix.rstrip('/') + '/' if prefix else ""
        self.s3 = boto3.client('s3', **kwargs)
    
    def write_file(self, content: str, filepath: str) -> bool:
        """
        Write content to an S3 object.
        
        Args:
            content: Content to write
            filepath: Relative path to the file
            
        Returns:
            bool: True if successful, False otherwise
        """
        try:
            key = self.prefix + filepath
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode('utf-8')
            )
            return True
        except Exception as e:
            logger.error(f"Error writing to S3 {filepath}: {e}")
            return False
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read content from an S3 object.
        
        Args:
            filepath: Relative path to the file
            
        Returns:
            str: File content if successful, None otherwise
        """
        try:
            key = self.prefix + filepath
            response = self.s3.get_object(Bucket=self.bucket, Key=key)
            return response['Body'].read().decode('utf-8')
        except Exception as e:
            logger.error(f"Error reading from S3 {filepath}: {e}")
            return None
    
    def ensure_directory(self, directory: str) -> bool:
        """
        Ensure a prefix exists in S3 (not strictly necessary but useful for consistency).
        
        Args:
            directory: Relative path to the directory
            
        Returns:
            bool: Always returns True as S3 doesn't need directory creation
        """
        return True

def get_storage_backend(config: Dict[str, Any]) -> StorageBackend:
    """
    Factory function to create appropriate storage backend based on configuration.
    
    Args:
        config: Configuration dictionary containing storage settings
        
    Returns:
        StorageBackend: Configured storage backend instance
        
    Example config structure:
        backup:
          storage:
            type: local  # or 's3'
            local:
              directory: "/path/to/backups"
            s3:
              bucket: "my-bucket"
              prefix: "backups/"
              region: "us-west-2"
              access_key: "..."
              secret_key: "..."
              endpoint_url: null  # optional
    """
    storage_config = config['backup']['storage']
    storage_type = storage_config.get('type', 'local')
    
    if storage_type == 's3':
        s3_config = storage_config.get('s3', {})
        return S3StorageBackend(
            bucket=s3_config['bucket'],
            prefix=s3_config.get('prefix', ''),
            aws_access_key_id=s3_config.get('access_key'),
            aws_secret_access_key=s3_config.get('secret_key'),
            region_name=s3_config.get('region'),
            endpoint_url=s3_config.get('endpoint_url')  # For custom endpoints
        )
    else:  # default to local
        local_config = storage_config.get('local', {})
        directory = local_config.get('directory')
        if not directory:
            raise ValueError("Local storage backend requires 'directory' to be specified")
        return LocalStorageBackend(
            base_path=directory
        ) 