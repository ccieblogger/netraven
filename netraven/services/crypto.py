"""Cryptographic utilities for secure data storage.

This module provides functions for encrypting and decrypting sensitive
information, particularly for credential passwords.
"""

import os
import base64
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC

# Load encryption key from environment or config
from netraven.config.loader import load_config
config = load_config()
SECRET_KEY = config.get('security', {}).get('encryption_key', os.environ.get('NETRAVEN_ENCRYPTION_KEY'))

# Salt should be stored securely
SALT = config.get('security', {}).get('encryption_salt', os.environ.get('NETRAVEN_ENCRYPTION_SALT', b'netraven_salt'))

def get_encryption_key(master_key=None):
    """Derive an encryption key from the master key.
    
    Args:
        master_key: The master key to derive from (defaults to SECRET_KEY)
        
    Returns:
        bytes: A derived key suitable for Fernet encryption
    """
    if master_key is None:
        master_key = SECRET_KEY
        
    if not master_key:
        raise ValueError("No encryption key available")
    
    # Convert string key to bytes if needed
    if isinstance(master_key, str):
        master_key = master_key.encode()
        
    # Convert string salt to bytes if needed
    salt = SALT
    if isinstance(salt, str):
        salt = salt.encode()
    
    # Use PBKDF2 to derive a secure key from the master key
    kdf = PBKDF2HMAC(
        algorithm=hashes.SHA256(),
        length=32,
        salt=salt,
        iterations=100000,
    )
    
    key = base64.urlsafe_b64encode(kdf.derive(master_key))
    return key

def encrypt_password(password):
    """Encrypt a password for secure storage.
    
    Args:
        password: The plaintext password to encrypt
        
    Returns:
        str: The encrypted password as a base64 string
    """
    if not password:
        raise ValueError("Password cannot be empty")
        
    # Convert to bytes if string
    if isinstance(password, str):
        password = password.encode()
        
    # Get encryption key
    key = get_encryption_key()
    
    # Create cipher and encrypt
    f = Fernet(key)
    encrypted = f.encrypt(password)
    
    # Return as string for storage
    return encrypted.decode()

def decrypt_password(encrypted_password):
    """Decrypt a stored password.
    
    Args:
        encrypted_password: The encrypted password from the database
        
    Returns:
        str: The decrypted plaintext password
    """
    if not encrypted_password:
        raise ValueError("Encrypted password cannot be empty")
        
    # Convert to bytes if string
    if isinstance(encrypted_password, str):
        encrypted_password = encrypted_password.encode()
        
    # Get encryption key
    key = get_encryption_key()
    
    # Create cipher and decrypt
    f = Fernet(key)
    decrypted = f.decrypt(encrypted_password)
    
    # Return as string
    return decrypted.decode() 