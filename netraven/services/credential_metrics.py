"""Services for tracking credential usage metrics.

This module provides functions for updating credential usage statistics
including last used timestamps and success rates.
"""

from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session

from netraven.db import models


def update_credential_success(db: Session, credential_id: int) -> None:
    """Update success metrics for a credential.
    
    Args:
        db: Database session
        credential_id: ID of the credential to update
    """
    if not db or not credential_id:
        return
        
    credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if credential:
        # Update last used timestamp
        credential.last_used = datetime.utcnow()
        
        # Update success rate (simple approach - could be more sophisticated)
        # This assumes success_rate is between 0.0 and 1.0
        # Successful connection moves rate toward 1.0
        if credential.success_rate is None:
            credential.success_rate = 1.0
        else:
            # Weighted average: 90% previous rate, 10% new result (success = 1.0)
            credential.success_rate = credential.success_rate * 0.9 + 0.1
        
        db.commit()


def update_credential_failure(db: Session, credential_id: int) -> None:
    """Update failure metrics for a credential.
    
    Args:
        db: Database session
        credential_id: ID of the credential to update
    """
    if not db or not credential_id:
        return
        
    credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
    if credential:
        # Update last used timestamp
        credential.last_used = datetime.utcnow()
        
        # Update success rate (simple approach - could be more sophisticated)
        # Failed connection moves rate toward 0.0
        if credential.success_rate is None:
            credential.success_rate = 0.0
        else:
            # Weighted average: 90% previous rate, 10% new result (failure = 0.0)
            credential.success_rate = credential.success_rate * 0.9
        
        db.commit()


def record_credential_attempt(
    db: Session,
    device_id: int,
    credential_id: int,
    job_id: Optional[int] = None,
    success: bool = False,
    error: Optional[str] = None
) -> None:
    """Record a credential usage attempt for auditing and analytics.
    
    This can be extended to store detailed attempt information in a separate table
    if that level of tracking is desired.
    
    Args:
        db: Database session
        device_id: ID of the device
        credential_id: ID of the credential used
        job_id: Optional job ID
        success: Whether the connection succeeded
        error: Optional error message
    """
    # This is a placeholder for more sophisticated tracking if needed
    if success:
        update_credential_success(db, credential_id)
    else:
        update_credential_failure(db, credential_id)
        
    # Log the attempt
    device_name = "Unknown"
    credential_name = "Unknown"
    
    try:
        device = db.query(models.Device).filter(models.Device.id == device_id).first()
        if device:
            device_name = device.hostname
            
        credential = db.query(models.Credential).filter(models.Credential.id == credential_id).first()
        if credential:
            credential_name = credential.username
            
        # Could add a dedicated log entry or database record here
        # For now, just use standard logging
        import logging
        log = logging.getLogger(__name__)
        log.info(
            f"[Job: {job_id}] Credential attempt: {credential_name} on {device_name} - "
            f"{'SUCCESS' if success else 'FAILURE'}"
        )
    except Exception as e:
        # Don't let logging failures impact operations
        pass 