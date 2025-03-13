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
import logging

# Importing AWS SDK conditionally to allow the module to be imported
# even if boto3 is not available
try:
    import boto3
    from botocore.exceptions import ClientError
    BOTO3_AVAILABLE = True
except ImportError:
    BOTO3_AVAILABLE = False

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
    """Storage backend for local filesystem."""
    
    def __init__(self, base_path: str):
        """
        Initialize the local storage backend.
        
        Args:
            base_path: The base directory for storing files
        """
        self.base_path = Path(base_path)
        self.ensure_directory("")  # Ensure base directory exists
        logger.debug(f"Initialized local storage backend with base path: {self.base_path}")
    
    def write_file(self, content: str, filepath: str) -> bool:
        """
        Write content to a file in the local filesystem.
        
        Args:
            content: The content to write
            filepath: The path to the file, relative to the base path
        
        Returns:
            bool: True if the write was successful, False otherwise
        """
        try:
            full_path = self.base_path / filepath
            
            # Ensure the parent directory exists
            parent_dir = os.path.dirname(full_path)
            if parent_dir:
                self.ensure_directory(os.path.dirname(filepath))
            
            # Write the content to the file
            with open(full_path, "w", encoding="utf-8") as f:
                f.write(content)
            
            logger.debug(f"Successfully wrote file: {full_path}")
            return True
        except Exception as e:
            logger.error(f"Error writing file {filepath}: {str(e)}")
            return False
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read content from a file in the local filesystem.
        
        Args:
            filepath: The path to the file, relative to the base path
        
        Returns:
            str: The file content, or None if the read failed
        """
        try:
            full_path = self.base_path / filepath
            
            if not os.path.exists(full_path):
                logger.error(f"File does not exist: {full_path}")
                return None
            
            with open(full_path, "r", encoding="utf-8") as f:
                content = f.read()
            
            logger.debug(f"Successfully read file: {full_path}")
            return content
        except Exception as e:
            logger.error(f"Error reading file {filepath}: {str(e)}")
            return None
    
    def ensure_directory(self, directory: str) -> bool:
        """
        Ensure a directory exists in the local filesystem.
        
        Args:
            directory: The directory path, relative to the base path
        
        Returns:
            bool: True if the directory exists or was created, False otherwise
        """
        try:
            full_path = self.base_path
            if directory:
                full_path = self.base_path / directory
            
            if not os.path.exists(full_path):
                os.makedirs(full_path, exist_ok=True)
                logger.debug(f"Created directory: {full_path}")
            
            return True
        except Exception as e:
            logger.error(f"Error ensuring directory {directory}: {str(e)}")
            return False


class S3StorageBackend(StorageBackend):
    """Storage backend for Amazon S3."""
    
    def __init__(self, bucket: str, prefix: str = "", **kwargs):
        """
        Initialize the S3 storage backend.
        
        Args:
            bucket: The S3 bucket name
            prefix: The prefix for all keys (like a directory)
            **kwargs: Additional arguments for boto3 client
        """
        if not BOTO3_AVAILABLE:
            raise ImportError("boto3 is required for S3StorageBackend")
        
        self.bucket = bucket
        self.prefix = prefix
        self.s3 = boto3.client('s3', **kwargs)
        logger.debug(f"Initialized S3 storage backend with bucket: {bucket}, prefix: {prefix}")
    
    def write_file(self, content: str, filepath: str) -> bool:
        """
        Write content to a file in Amazon S3.
        
        Args:
            content: The content to write
            filepath: The path to the file, will be appended to the prefix
        
        Returns:
            bool: True if the write was successful, False otherwise
        """
        try:
            key = self.prefix + filepath if self.prefix else filepath
            
            # Upload the content to S3
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=content.encode('utf-8')
            )
            
            logger.debug(f"Successfully wrote file to S3: {self.bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"Error writing file to S3 {filepath}: {str(e)}")
            return False
    
    def read_file(self, filepath: str) -> Optional[str]:
        """
        Read content from a file in Amazon S3.
        
        Args:
            filepath: The path to the file, will be appended to the prefix
        
        Returns:
            str: The file content, or None if the read failed
        """
        try:
            key = self.prefix + filepath if self.prefix else filepath
            
            # Download the object from S3
            response = self.s3.get_object(
                Bucket=self.bucket,
                Key=key
            )
            
            # Read the content
            content = response['Body'].read().decode('utf-8')
            
            logger.debug(f"Successfully read file from S3: {self.bucket}/{key}")
            return content
        except ClientError as e:
            if e.response['Error']['Code'] == 'NoSuchKey':
                logger.error(f"File does not exist in S3: {self.bucket}/{key}")
            else:
                logger.error(f"Error reading file from S3 {filepath}: {str(e)}")
            return None
        except Exception as e:
            logger.error(f"Error reading file from S3 {filepath}: {str(e)}")
            return None
    
    def ensure_directory(self, directory: str) -> bool:
        """
        Ensure a directory exists in Amazon S3.
        
        S3 doesn't have directories, but we can create an empty object
        with a trailing slash to simulate a directory.
        
        Args:
            directory: The directory path, will be appended to the prefix
        
        Returns:
            bool: True if the directory marker was created, False otherwise
        """
        # S3 doesn't have directories, but we can create an empty object
        # with a trailing slash to simulate a directory
        if not directory:
            return True
        
        try:
            # Add trailing slash if not present
            if not directory.endswith('/'):
                directory += '/'
            
            key = self.prefix + directory if self.prefix else directory
            
            # Create an empty object with a trailing slash
            self.s3.put_object(
                Bucket=self.bucket,
                Key=key,
                Body=b''
            )
            
            logger.debug(f"Created directory marker in S3: {self.bucket}/{key}")
            return True
        except Exception as e:
            logger.error(f"Error creating directory marker in S3 {directory}: {str(e)}")
            return False


def get_storage_backend(config: Dict[str, Any]) -> StorageBackend:
    """
    Factory function to create a storage backend based on configuration.
    
    Args:
        config: The configuration dictionary
    
    Returns:
        StorageBackend: The configured storage backend
    
    Raises:
        ValueError: If the storage type is not supported
        Exception: If there's an error creating the storage backend
    """
    storage_type = config.get('backup', {}).get('storage', {}).get('type', 'local')
    
    try:
        if storage_type == 'local':
            path = config.get('backup', {}).get('storage', {}).get('local', {}).get('directory')
            if not path:
                path = str(Path.home() / 'network_backups')
            return LocalStorageBackend(path)
        
        elif storage_type == 's3':
            s3_config = config.get('backup', {}).get('storage', {}).get('s3', {})
            bucket = s3_config.get('bucket')
            prefix = s3_config.get('prefix', 'network_backups/')
            
            if not bucket:
                raise ValueError("S3 bucket name is required")
            
            # Extract other AWS parameters
            aws_params = {}
            for key in ['region', 'access_key', 'secret_key']:
                if s3_config.get(key):
                    # Convert access_key to aws_access_key_id format
                    if key == 'access_key':
                        aws_params['aws_access_key_id'] = s3_config[key]
                    elif key == 'secret_key':
                        aws_params['aws_secret_access_key'] = s3_config[key]
                    else:
                        aws_params[key] = s3_config[key]
            
            return S3StorageBackend(bucket, prefix, **aws_params)
        
        else:
            raise ValueError(f"Unsupported storage type: {storage_type}")
    
    except Exception as e:
        logger.error(f"Error creating storage backend: {str(e)}")
        raise 