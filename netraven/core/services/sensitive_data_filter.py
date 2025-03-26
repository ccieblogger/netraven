"""
Sensitive data filter for NetRaven.

This module provides a utility for identifying and redacting sensitive information
from log data, such as passwords, authentication tokens, and private keys.
"""

import re
from typing import Dict, Any, List, Union, Pattern, Tuple, Optional, Set

class SensitiveDataFilter:
    """
    Utility for filtering sensitive data from logs and API responses.
    
    This class provides methods for identifying and redacting sensitive information
    from dictionaries, strings, and other data structures. It uses a combination of
    pattern matching and known key detection to find and redact sensitive data.
    """
    
    # Default replacement string for redacted values
    DEFAULT_REDACTION = "********"
    
    # Keys that commonly contain sensitive data
    SENSITIVE_KEYS = {
        # Authentication-related keys
        "password", "passwd", "pwd", "secret", "api_key", "apikey", "api_token", 
        "auth_token", "token", "access_token", "refresh_token", "private_key",
        "secret_key", "passphrase", "pin", "otp", "authentication",
        
        # Connection-related keys
        "ssh_key", "ssh_password", "key_file", "keyfile", "private_key_file",
        
        # Credential-related keys
        "credential", "credentials", "cred", "creds",
        
        # Security question answers
        "security_answer", "security_question_answer", "answer",
        
        # Certificate-related keys
        "ssl_key", "cert_key", "certificate_key",
        
        # Two-factor authentication
        "two_factor_code", "2fa_code", "totp", "hotp",
    }
    
    # Patterns that might contain sensitive data
    SENSITIVE_PATTERNS = [
        # Common password patterns in command outputs or logs
        re.compile(r"password\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"passwd\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"secret\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"credential\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"api[_-]?key\s*[:=]\s*\S+", re.IGNORECASE),
        re.compile(r"token\s*[:=]\s*\S+", re.IGNORECASE),
        
        # Private key patterns
        re.compile(r"-----BEGIN( RSA)? PRIVATE KEY-----.*?-----END( RSA)? PRIVATE KEY-----", re.DOTALL),
        
        # Common token formats
        re.compile(r"eyJ[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+\.[a-zA-Z0-9_-]+"),  # JWT token
        
        # Sensitive CLI arguments
        re.compile(r"--password[= ]\S+"),
        re.compile(r"-p\s+\S+"),  # Common password flag in CLI tools
        re.compile(r"--token[= ]\S+"),
        re.compile(r"--key[= ]\S+"),
        
        # Authentication in URLs
        re.compile(r"(https?://)([^:@/]+):([^@/]+)@"),  # http://user:password@example.com
    ]
    
    def __init__(self, 
                 custom_sensitive_keys: Optional[Set[str]] = None,
                 custom_sensitive_patterns: Optional[List[Pattern]] = None,
                 redaction_string: str = DEFAULT_REDACTION):
        """
        Initialize the sensitive data filter.
        
        Args:
            custom_sensitive_keys: Additional keys to consider sensitive
            custom_sensitive_patterns: Additional regex patterns to match sensitive data
            redaction_string: String to use for redacting sensitive values
        """
        # Combine default and custom sensitive keys
        self.sensitive_keys = self.SENSITIVE_KEYS.copy()
        if custom_sensitive_keys:
            self.sensitive_keys.update(custom_sensitive_keys)
        
        # Combine default and custom sensitive patterns
        self.sensitive_patterns = self.SENSITIVE_PATTERNS.copy()
        if custom_sensitive_patterns:
            self.sensitive_patterns.extend(custom_sensitive_patterns)
        
        self.redaction_string = redaction_string
    
    def _is_sensitive_key(self, key: str) -> bool:
        """
        Check if a key is likely to contain sensitive information.
        
        Args:
            key: The key to check
            
        Returns:
            bool: True if the key is likely sensitive, False otherwise
        """
        # Convert the key to lowercase for case-insensitive matching
        key_lower = key.lower()
        
        # Check if the key is in our sensitive keys set
        if key_lower in self.sensitive_keys:
            return True
        
        # Check if any sensitive key is a substring of the key
        for sensitive_key in self.sensitive_keys:
            if sensitive_key in key_lower:
                return True
        
        return False
    
    def _redact_sensitive_patterns(self, value: str) -> str:
        """
        Redact sensitive patterns from a string.
        
        Args:
            value: The string to process
            
        Returns:
            str: The string with sensitive data redacted
        """
        if not isinstance(value, str):
            return value
        
        # Apply each pattern and replace matches
        result = value
        for pattern in self.sensitive_patterns:
            result = pattern.sub(self.redaction_string, result)
        
        return result
    
    def filter_dict(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Filter sensitive data from a dictionary.
        
        Args:
            data: Dictionary to filter
            
        Returns:
            Dict with sensitive data redacted
        """
        if not isinstance(data, dict):
            return data
        
        result = {}
        for key, value in data.items():
            # Check if this is a sensitive key
            if self._is_sensitive_key(key):
                result[key] = self.redaction_string
            # Recursively filter nested dictionaries
            elif isinstance(value, dict):
                result[key] = self.filter_dict(value)
            # Filter lists and tuples
            elif isinstance(value, (list, tuple)):
                result[key] = self.filter_list(value)
            # Redact sensitive patterns in strings
            elif isinstance(value, str):
                result[key] = self._redact_sensitive_patterns(value)
            # Pass through other types unchanged
            else:
                result[key] = value
        
        return result
    
    def filter_list(self, data: Union[List[Any], Tuple[Any, ...]]) -> Union[List[Any], Tuple[Any, ...]]:
        """
        Filter sensitive data from a list or tuple.
        
        Args:
            data: List or tuple to filter
            
        Returns:
            List or tuple with sensitive data redacted
        """
        if not isinstance(data, (list, tuple)):
            return data
        
        # Process each item in the list/tuple
        result = []
        for item in data:
            if isinstance(item, dict):
                result.append(self.filter_dict(item))
            elif isinstance(item, (list, tuple)):
                result.append(self.filter_list(item))
            elif isinstance(item, str):
                result.append(self._redact_sensitive_patterns(item))
            else:
                result.append(item)
        
        # Return the same type as the input
        if isinstance(data, tuple):
            return tuple(result)
        return result
    
    def filter_value(self, value: Any) -> Any:
        """
        Filter sensitive data from any value.
        
        Args:
            value: Value to filter
            
        Returns:
            Value with sensitive data redacted
        """
        if isinstance(value, dict):
            return self.filter_dict(value)
        elif isinstance(value, (list, tuple)):
            return self.filter_list(value)
        elif isinstance(value, str):
            return self._redact_sensitive_patterns(value)
        else:
            return value
    
    def filter_command(self, command: str) -> str:
        """
        Filter sensitive data from a command string.
        
        Args:
            command: Command string to filter
            
        Returns:
            Command with sensitive data redacted
        """
        # Handle the special case of command strings, which often contain
        # passwords and other sensitive data as arguments
        return self._redact_sensitive_patterns(command) 