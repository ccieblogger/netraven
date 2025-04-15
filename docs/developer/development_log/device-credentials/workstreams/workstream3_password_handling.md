# Work Stream 3: Password Handling Consistency

## Overview

This work stream focuses on addressing inconsistencies in password handling throughout the NetRaven system. It aims to ensure that passwords are stored securely and accessed consistently with proper encryption/decryption and hashing where appropriate.

## Technical Background

The current implementation has several inconsistencies:
1. The `Credential` model defines a `password` field for plaintext storage
2. The credential API router references a `hashed_password` field when creating credentials
3. There's a TODO comment in the model: "Implement password encryption/decryption mechanism"
4. The code mentions using the `auth.get_password_hash()` function but doesn't consistently apply it

## Implementation Tasks

### 1. Update Credential Model

**File:** `netraven/db/models/credential.py`

Update the model to use consistent naming and add password access methods:

```python
from sqlalchemy import Column, Integer, String, DateTime, Float, Boolean
from sqlalchemy.orm import relationship
from sqlalchemy.sql import expression

from netraven.db.base import Base
from .tag import credential_tag_association
from netraven.api import auth  # Import auth utils for hashing

class Credential(Base):
    """Stores credential information used to access network devices."""
    __tablename__ = "credentials"

    id = Column(Integer, primary_key=True)
    username = Column(String, nullable=False)
    # Rename from password to hashed_password for clarity
    hashed_password = Column(String, nullable=False)  # Stores the hashed password
    priority = Column(Integer, default=100)
    last_used = Column(DateTime(timezone=True))
    success_rate = Column(Float, default=1.0)
    description = Column(String, nullable=True)
    is_system = Column(Boolean, server_default=expression.false(), nullable=True)

    tags = relationship(
        "Tag",
        secondary=credential_tag_association,
        back_populates="credentials"
    )
    
    # Property to retrieve password for device connections
    @property
    def password(self):
        """Get the password for device connection.
        
        For now, this just returns the hashed_password value since we're
        not truly hashing/encrypting yet. In a secure implementation,
        this would decrypt the stored password.
        
        Returns:
            str: The password to use for device authentication
        """
        # TODO: Replace with actual decryption if you implement encryption
        # For now, we assume hashed_password contains the usable password
        return self.hashed_password
    
    @classmethod
    def create_with_hashed_password(cls, username, password, **kwargs):
        """Create a new credential with a hashed password.
        
        This factory method ensures password hashing happens consistently.
        
        Args:
            username: The username
            password: The plaintext password to hash
            **kwargs: Additional fields for the credential
            
        Returns:
            Credential: A new unsaved Credential object
        """
        # In a real secure implementation, hashed_password would be properly hashed
        # We'll get it ready for that future state
        hashed = auth.get_password_hash(password) if auth else password
        
        return cls(
            username=username,
            hashed_password=hashed,
            **kwargs
        )
```

### 2. Create Database Migration

**File:** `alembic/versions/xxxx_rename_password_to_hashed_password.py`

Create a migration script to rename the column:

```python
"""Rename password column to hashed_password.

Revision ID: xxxx
Revises: <previous_revision>
Create Date: YYYY-MM-DD

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'xxxx'  # Replace with a unique identifier
down_revision = '<previous_revision>'  # Replace with the previous revision ID
branch_labels = None
depends_on = None


def upgrade():
    # For SQLite (which doesn't support column rename directly)
    # Check the database dialect and use appropriate approach
    context = op.get_context()
    if context.dialect.name == 'sqlite':
        # For SQLite, we need to create a new table, copy data, and swap
        with op.batch_alter_table('credentials') as batch_op:
            batch_op.alter_column('password', new_column_name='hashed_password')
    else:
        # For PostgreSQL and most other databases
        op.alter_column('credentials', 'password', new_column_name='hashed_password')


def downgrade():
    # Revert the column name change
    context = op.get_context()
    if context.dialect.name == 'sqlite':
        with op.batch_alter_table('credentials') as batch_op:
            batch_op.alter_column('hashed_password', new_column_name='password')
    else:
        op.alter_column('credentials', 'hashed_password', new_column_name='password')
```

### 3. Update Credential Router

**File:** `netraven/api/routers/credentials.py`

Update the router to use the new model method and consistent field names:

```python
@router.post("/", response_model=schemas.credential.Credential, status_code=status.HTTP_201_CREATED)
def create_credential(
    credential: schemas.credential.CredentialCreate,
    db: Session = Depends(get_db_session),
):
    """Create a new credential set.

    Password will be hashed before storing.
    """
    # Use the factory method to create credential with hashed password
    db_credential = models.Credential.create_with_hashed_password(
        username=credential.username,
        password=credential.password,
        priority=credential.priority,
        description=credential.description,
    )
    
    # Handle tags if provided
    if credential.tags:
        tags = get_tags_by_ids(db, credential.tags)
        db_credential.tags = tags

    db.add(db_credential)
    db.commit()
    db.refresh(db_credential)
    
    # Eager load tags for response
    db.query(models.Credential).options(selectinload(models.Credential.tags)).filter(models.Credential.id == db_credential.id).first()
    return db_credential

@router.put("/{credential_id}", response_model=schemas.credential.Credential)
def update_credential(
    credential_id: int,
    credential: schemas.credential.CredentialUpdate,
    db: Session = Depends(get_db_session)
):
    """Update a credential set.
    
    If password is provided, it will be re-hashed.
    """
    db_credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if db_credential is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Credential not found")

    update_data = credential.model_dump(exclude_unset=True)

    # Update simple attributes and hash password if provided
    for key, value in update_data.items():
        if key == "password" and value:
            # Update hashed_password field
            db_credential.hashed_password = auth.get_password_hash(value)
        elif key != "tags" and key != "password":
            setattr(db_credential, key, value)

    # Handle tags update
    if "tags" in update_data:
        if update_data["tags"] is None:
            db_credential.tags = []
        else:
            tags = get_tags_by_ids(db, update_data["tags"])
            db_credential.tags = tags

    db.commit()
    db.refresh(db_credential)
    return db_credential
```

### 4. Update Credential Schemas

**File:** `netraven/api/schemas/credential.py`

Ensure the schemas align with the model changes:

```python
# Update the base schema to ensure it doesn't have password
class CredentialBase(BaseSchema):
    """Base schema for credential data shared by multiple credential schemas."""
    username: str = Field(...)
    priority: int = Field(100)
    description: Optional[str] = Field(None)
    # Note: no password field here

# Update to ensure password is required for create
class CredentialCreate(CredentialBase):
    """Schema for creating a new credential."""
    password: str = Field(...)  # Required for creation
    tags: Optional[List[int]] = Field(None)

# Update to ensure password is optional for update
class CredentialUpdate(BaseSchema):
    """Schema for updating an existing credential."""
    username: Optional[str] = Field(None)
    password: Optional[str] = Field(None)  # Optional for updates
    priority: Optional[int] = Field(None)
    description: Optional[str] = Field(None)
    tags: Optional[List[int]] = Field(None)

# Response model should not include password
class Credential(CredentialBase, BaseSchemaWithId):
    """Complete credential schema used for responses."""
    is_system: bool = Field(default=False)
    tags: List[Tag] = Field(default=[])
    # Note: No password or hashed_password field
```

### 5. Implement Password Security Enhancement (Optional)

If stronger password security is required, implement actual encryption/decryption:

**File:** `netraven/services/crypto.py`

```python
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
# IMPORTANT: In production, this should come from secure storage
# such as environment variables or a secrets management system
from netraven.config.loader import load_config
config = load_config()
SECRET_KEY = config.get('security', {}).get('encryption_key', os.environ.get('NETRAVEN_ENCRYPTION_KEY'))

# Salt should be stored securely and separately
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
        return None
        
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
        
    Raises:
        ValueError: If decryption fails
    """
    if not encrypted_password:
        return None
        
    # Convert to bytes if string
    if isinstance(encrypted_password, str):
        encrypted_password = encrypted_password.encode()
        
    # Get encryption key
    key = get_encryption_key()
    
    try:
        # Create cipher and decrypt
        f = Fernet(key)
        decrypted = f.decrypt(encrypted_password)
        
        # Return as string
        return decrypted.decode()
    except Exception as e:
        raise ValueError(f"Failed to decrypt password: {e}")
```

Then update the Credential model to use this:

```python
from netraven.services.crypto import encrypt_password, decrypt_password

class Credential(Base):
    # ... existing fields ...
    
    @property
    def password(self):
        """Get the decrypted password for device connection."""
        try:
            return decrypt_password(self.hashed_password)
        except ValueError:
            # If decryption fails, the password might be stored in plain text
            # This handles backward compatibility
            return self.hashed_password
    
    @classmethod
    def create_with_hashed_password(cls, username, password, **kwargs):
        """Create a new credential with an encrypted password."""
        encrypted = encrypt_password(password)
        
        return cls(
            username=username,
            hashed_password=encrypted,
            **kwargs
        )
```

### 6. Add Configuration for Password Encryption

**File:** `.env.dev` and `.env.prod`

Add configuration entries for encryption:

```
# Security settings
NETRAVEN_ENCRYPTION_KEY=your_very_secure_encryption_key
NETRAVEN_ENCRYPTION_SALT=your_encryption_salt
```

**File:** `netraven/config/default_config.yml`

Add security section to the config:

```yaml
security:
  encryption_key: ""  # Set via environment variable
  encryption_salt: ""  # Set via environment variable
  password_min_length: 8
```

### 7. Create Unit Tests

**File:** `tests/db/models/test_credential.py`

```python
import pytest
from sqlalchemy.orm import Session

from netraven.db.models.credential import Credential

class TestCredentialModel:
    def test_create_with_hashed_password(self):
        """Test that the factory method hashes passwords."""
        # Create a credential with the factory method
        cred = Credential.create_with_hashed_password(
            username="test_user",
            password="test_password",
            priority=10
        )
        
        # Verify that the hashed_password field is set and different from the original
        assert cred.hashed_password is not None
        assert cred.hashed_password != "test_password"
        
        # Verify that the password property returns the usable password
        assert cred.password is not None
        
    def test_credential_password_property(self):
        """Test that the password property works correctly."""
        # Create a credential manually
        cred = Credential(
            username="test_user",
            hashed_password="stored_password",
            priority=10
        )
        
        # Verify password property returns the stored value
        assert cred.password == "stored_password"
        
    # If implementing encryption, add tests for that
    @pytest.mark.skipif("NETRAVEN_ENCRYPTION_KEY" not in os.environ,
                       reason="Encryption key not available")
    def test_password_encryption_decryption(self):
        """Test encryption and decryption of passwords."""
        original_password = "secret_password"
        
        # Create with encryption
        cred = Credential.create_with_hashed_password(
            username="test_user",
            password=original_password,
            priority=10
        )
        
        # Verify hashed value is not the original
        assert cred.hashed_password != original_password
        
        # Verify decryption works
        assert cred.password == original_password
```

**File:** `tests/services/test_crypto.py` (if implementing encryption)

```python
import pytest
import os
from unittest.mock import patch

from netraven.services.crypto import encrypt_password, decrypt_password, get_encryption_key

@pytest.mark.skipif("NETRAVEN_ENCRYPTION_KEY" not in os.environ,
                   reason="Encryption key not available")
class TestCryptoService:
    def test_encryption_decryption(self):
        """Test that encryption and decryption work properly."""
        original = "test_password"
        
        # Encrypt
        encrypted = encrypt_password(original)
        
        # Verify it's not the original
        assert encrypted != original
        
        # Decrypt
        decrypted = decrypt_password(encrypted)
        
        # Verify decryption returns the original
        assert decrypted == original
    
    def test_different_passwords_encrypt_differently(self):
        """Test that different passwords encrypt to different values."""
        pw1 = "password1"
        pw2 = "password2"
        
        enc1 = encrypt_password(pw1)
        enc2 = encrypt_password(pw2)
        
        # Different passwords should encrypt to different values
        assert enc1 != enc2
    
    def test_encryption_is_consistent(self):
        """Test that the same password encrypts differently each time (due to salt)."""
        pw = "same_password"
        
        enc1 = encrypt_password(pw)
        enc2 = encrypt_password(pw)
        
        # Same password should encrypt to different values each time
        # This is due to the random IV used in Fernet
        assert enc1 != enc2
        
        # But both should decrypt to the original
        assert decrypt_password(enc1) == pw
        assert decrypt_password(enc2) == pw
    
    def test_handle_empty_values(self):
        """Test handling of empty values."""
        assert encrypt_password(None) is None
        assert encrypt_password("") is None
        assert decrypt_password(None) is None
        assert decrypt_password("") is None
```

## Integration Points

The changes in this work stream interface with:
1. The credential model used throughout the system
2. The API router for credential operations
3. Work Stream 1's DeviceWithCredentials which uses the password property
4. Work Stream 4's retry logic which uses password information

## Compatibility Considerations

1. **Existing Data Migration**
   - The column rename migration should preserve existing passwords
   - If implementing encryption, consider adding a separate migration that encrypts existing passwords
   - Test thoroughly with a copy of production data before deploying

2. **API Compatibility**
   - The API response schemas should not change externally
   - Input handling should remain compatible with existing clients

## Testing Approach

1. Unit tests should cover:
   - Model methods and properties
   - Password hashing/encryption functionality
   - API router behavior with password changes

2. Integration tests should verify:
   - Database migrations work correctly
   - API endpoints handle password fields properly
   - If implementing encryption, test the full credential lifecycle

## Expected Outcomes

1. Consistent password field naming throughout the codebase
2. Proper handling of passwords in the API
3. Enhanced security through proper password storage
4. Clear migration path for existing data
5. (Optional) Encryption and decryption of passwords for maximum security

## Completion Criteria

This work stream is complete when:
1. All implementation tasks are finished
2. All unit tests pass
3. Database migrations run successfully
4. API endpoints work correctly with the updated model
5. Code review has been completed and approved

## Estimated Effort

- Basic Implementation (Tasks 1-4): 1 developer day
- Encryption Enhancement (Tasks 5-6): 1 developer day
- Testing and Quality Assurance: 1 developer day
- Total: 2-3 developer days depending on encryption implementation 