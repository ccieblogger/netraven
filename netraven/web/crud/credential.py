"""
CRUD operations for credentials in the NetRaven web interface.

This module provides functions for creating, reading, updating, and deleting credentials,
as well as managing credential-tag associations.
"""

from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any, Tuple
import uuid
from datetime import datetime
from sqlalchemy import func

# Import credential store function only, not the models
from netraven.core.credential_store import get_credential_store
# Import models directly from web.models
from netraven.web.models.credential import Credential, CredentialTag
from netraven.web.models.tag import Tag
from netraven.web.schemas.credential import CredentialCreate, CredentialUpdate, CredentialTagAssociation
from netraven.web.crud.device import get_device

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

def get_credentials(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    include_tags: bool = True
) -> List[Dict[str, Any]]:
    """
    Get all credentials.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        include_tags: Whether to include tag information with each credential
        
    Returns:
        List of credentials
    """
    credential_store = get_credential_store()
    
    # Use the credential store session
    cs_db = credential_store.get_db()
    try:
        # Query all credentials with pagination
        credentials = cs_db.query(Credential).offset(skip).limit(limit).all()
        
        # Convert to dictionary format
        result = []
        for cred in credentials:
            # Convert to dict format
            cred_dict = {
                "id": cred.id,
                "name": cred.name,
                "username": cred.username,
                "description": cred.description,
                "use_keys": cred.use_keys,
                "key_file": cred.key_file,
                "success_count": cred.success_count,
                "failure_count": cred.failure_count,
                "last_used": cred.last_used,
                "last_success": cred.last_success,
                "last_failure": cred.last_failure,
                "created_at": cred.created_at,
                "updated_at": cred.updated_at,
            }
            
            # Include tag information if requested
            if include_tags:
                cred_tags = []
                for ct in cred.credential_tags:
                    # Get the tag from the main database
                    tag = db.query(Tag).filter(Tag.id == ct.tag_id).first()
                    if tag:
                        cred_tags.append({
                            "id": tag.id,
                            "name": tag.name,
                            "color": tag.color,
                            "priority": ct.priority,
                            "success_count": ct.success_count,
                            "failure_count": ct.failure_count
                        })
                
                cred_dict["tags"] = cred_tags
            
            result.append(cred_dict)
        
        return result
    finally:
        cs_db.close()

def get_credential(
    db: Session, 
    credential_id: str,
    include_tags: bool = True
) -> Optional[Dict[str, Any]]:
    """
    Get a credential by ID.
    
    Args:
        db: Database session
        credential_id: Credential ID
        include_tags: Whether to include tag information
        
    Returns:
        Credential if found, None otherwise
    """
    credential_store = get_credential_store()
    
    # First try to get the credential directly from the credential store
    cred_dict = credential_store.get_credential(credential_id)
    if not cred_dict:
        return None
    
    # Include tag information if requested
    if include_tags:
        cs_db = credential_store.get_db()
        try:
            # Get the credential object to access its tags
            cred = cs_db.query(Credential).filter(Credential.id == credential_id).first()
            if cred:
                cred_tags = []
                for ct in cred.credential_tags:
                    # Get the tag from the main database
                    tag = db.query(Tag).filter(Tag.id == ct.tag_id).first()
                    if tag:
                        cred_tags.append({
                            "id": tag.id,
                            "name": tag.name,
                            "color": tag.color,
                            "priority": ct.priority,
                            "success_count": ct.success_count,
                            "failure_count": ct.failure_count
                        })
                
                cred_dict["tags"] = cred_tags
        finally:
            cs_db.close()
    
    return cred_dict

def create_credential(
    db: Session, 
    credential: CredentialCreate
) -> Dict[str, Any]:
    """
    Create a new credential.
    
    Args:
        db: Database session
        credential: Credential creation data
        
    Returns:
        Created credential
    """
    credential_store = get_credential_store()
    
    # Add the credential to the store
    credential_id = credential_store.add_credential(
        name=credential.name,
        username=credential.username,
        password=credential.password,
        use_keys=credential.use_keys,
        key_file=credential.key_file,
        description=credential.description,
        tags=credential.tags
    )
    
    # Get the created credential with tag information
    new_credential = get_credential(db, credential_id, include_tags=True)
    
    logger.info(f"Created credential: {credential.name} (ID: {credential_id})")
    return new_credential

def update_credential(
    db: Session, 
    credential_id: str, 
    credential: CredentialUpdate
) -> Optional[Dict[str, Any]]:
    """
    Update a credential.
    
    Args:
        db: Database session
        credential_id: Credential ID
        credential: Credential update data
        
    Returns:
        Updated credential if found, None otherwise
    """
    credential_store = get_credential_store()
    cs_db = credential_store.get_db()
    
    try:
        # Get the credential from the store
        cred = cs_db.query(Credential).filter(Credential.id == credential_id).first()
        if not cred:
            return None
        
        # Update fields if provided
        if credential.name is not None:
            cred.name = credential.name
        if credential.username is not None:
            cred.username = credential.username
        if credential.description is not None:
            cred.description = credential.description
        if credential.use_keys is not None:
            cred.use_keys = credential.use_keys
        if credential.key_file is not None:
            cred.key_file = credential.key_file
        
        # Update password if provided (requires special handling for encryption)
        if credential.password is not None:
            # Re-encrypt the password using the credential store
            encrypted_password = credential_store._encrypt(credential.password)
            cred.password = encrypted_password
        
        cred.updated_at = datetime.utcnow()
        cs_db.commit()
        cs_db.refresh(cred)
        
        logger.info(f"Updated credential: {cred.name} (ID: {cred.id})")
        
        # Get the updated credential with tag information
        return get_credential(db, credential_id, include_tags=True)
    finally:
        cs_db.close()

def delete_credential(
    db: Session, 
    credential_id: str
) -> bool:
    """
    Delete a credential.
    
    Args:
        db: Database session
        credential_id: Credential ID
        
    Returns:
        True if credential was deleted, False otherwise
    """
    credential_store = get_credential_store()
    return credential_store.delete_credential(credential_id)

def get_credentials_by_tag(
    db: Session, 
    tag_id: str
) -> List[Dict[str, Any]]:
    """
    Get all credentials for a tag.
    
    Args:
        db: Database session
        tag_id: Tag ID
        
    Returns:
        List of credentials associated with the tag
    """
    credential_store = get_credential_store()
    
    # Get credentials from the credential store
    credentials = credential_store.get_credentials_by_tag(tag_id)
    
    # Convert to the format expected by the API
    for cred in credentials:
        # Add tag information
        tag = db.query(Tag).filter(Tag.id == tag_id).first()
        if tag:
            cred["tag"] = {
                "id": tag.id,
                "name": tag.name,
                "color": tag.color
            }
    
    return credentials

def associate_credential_with_tag(
    db: Session, 
    association: CredentialTagAssociation
) -> Optional[Dict[str, Any]]:
    """
    Associate a credential with a tag.
    
    Args:
        db: Database session
        association: Credential-tag association data
        
    Returns:
        Association information if successful, None otherwise
    """
    credential_store = get_credential_store()
    cs_db = credential_store.get_db()
    
    try:
        # Check if the credential exists
        cred = cs_db.query(Credential).filter(Credential.id == association.credential_id).first()
        if not cred:
            logger.warning(f"Credential not found: {association.credential_id}")
            return None
        
        # Check if the tag exists
        tag = db.query(Tag).filter(Tag.id == association.tag_id).first()
        if not tag:
            logger.warning(f"Tag not found: {association.tag_id}")
            return None
        
        # Check if the association already exists
        existing = cs_db.query(CredentialTag).filter(
            CredentialTag.credential_id == association.credential_id,
            CredentialTag.tag_id == association.tag_id
        ).first()
        
        if existing:
            # Update the priority if the association already exists
            existing.priority = association.priority
            existing.updated_at = datetime.utcnow()
            cs_db.commit()
            cs_db.refresh(existing)
            
            logger.info(f"Updated credential-tag association: {existing.id}")
            
            return {
                "id": existing.id,
                "credential_id": existing.credential_id,
                "tag_id": existing.tag_id,
                "priority": existing.priority,
                "success_count": existing.success_count,
                "failure_count": existing.failure_count,
                "last_used": existing.last_used,
                "created_at": existing.created_at,
                "updated_at": existing.updated_at
            }
        else:
            # Create a new association
            new_association = CredentialTag(
                id=str(uuid.uuid4()),
                credential_id=association.credential_id,
                tag_id=association.tag_id,
                priority=association.priority
            )
            
            cs_db.add(new_association)
            cs_db.commit()
            cs_db.refresh(new_association)
            
            logger.info(f"Created credential-tag association: {new_association.id}")
            
            return {
                "id": new_association.id,
                "credential_id": new_association.credential_id,
                "tag_id": new_association.tag_id,
                "priority": new_association.priority,
                "success_count": new_association.success_count,
                "failure_count": new_association.failure_count,
                "last_used": new_association.last_used,
                "created_at": new_association.created_at,
                "updated_at": new_association.updated_at
            }
    finally:
        cs_db.close()

def remove_credential_from_tag(
    db: Session, 
    credential_id: str,
    tag_id: str
) -> bool:
    """
    Remove a credential from a tag.
    
    Args:
        db: Database session
        credential_id: Credential ID
        tag_id: Tag ID
        
    Returns:
        True if association was removed, False otherwise
    """
    credential_store = get_credential_store()
    cs_db = credential_store.get_db()
    
    try:
        # Find the association
        association = cs_db.query(CredentialTag).filter(
            CredentialTag.credential_id == credential_id,
            CredentialTag.tag_id == tag_id
        ).first()
        
        if not association:
            logger.warning(f"Credential-tag association not found: {credential_id}, {tag_id}")
            return False
        
        # Remove the association
        cs_db.delete(association)
        cs_db.commit()
        
        logger.info(f"Removed credential-tag association: {credential_id}, {tag_id}")
        return True
    finally:
        cs_db.close()

def test_credential(
    db: Session,
    credential_id: str,
    device_id: Optional[str] = None,
    hostname: Optional[str] = None,
    device_type: Optional[str] = None,
    port: int = 22
) -> Dict[str, Any]:
    """
    Test a credential against a device.
    
    Args:
        db: Database session
        credential_id: Credential ID
        device_id: Device ID (optional)
        hostname: Device hostname/IP (optional)
        device_type: Device type (optional)
        port: Device port
        
    Returns:
        Test result with success status and message
    """
    import time
    from netraven.core.device_comm import DeviceConnector
    
    credential_store = get_credential_store()
    
    # Get the credential
    cred_dict = credential_store.get_credential(credential_id)
    if not cred_dict:
        return {
            "success": False,
            "message": f"Credential not found: {credential_id}",
            "time_taken": 0.0,
            "device_info": None
        }
    
    # If device_id is provided, get the device details
    if device_id:
        device = get_device(db, device_id)
        if not device:
            return {
                "success": False,
                "message": f"Device not found: {device_id}",
                "time_taken": 0.0,
                "device_info": None
            }
        
        hostname = device.ip_address or device.hostname
        device_type = device.device_type
        port = device.port or 22
    
    # Ensure we have all required parameters
    if not hostname:
        return {
            "success": False,
            "message": "Device hostname/IP is required for testing",
            "time_taken": 0.0,
            "device_info": None
        }
    
    if not device_type:
        return {
            "success": False,
            "message": "Device type is required for testing",
            "time_taken": 0.0,
            "device_info": None
        }
    
    # Create a device connector for testing
    connector = DeviceConnector(
        host=hostname,
        device_type=device_type,
        port=port,
        username=cred_dict["username"],
        password=cred_dict["password"],
        use_keys=cred_dict["use_keys"],
        key_file=cred_dict["key_file"]
    )
    
    # Test the connection
    start_time = time.time()
    try:
        # Connect to the device
        connector.connect()
        
        # Get device info if available
        device_info = None
        try:
            # Try to get hostname/version info from the device
            device_prompt = connector.get_prompt() if hasattr(connector, 'get_prompt') else None
            device_info = {
                "prompt": device_prompt,
                "hostname": hostname,
                "device_type": device_type
            }
        except Exception as e:
            logger.warning(f"Error getting device info: {str(e)}")
        
        # Record connection success
        if device_id:
            credential_store.update_credential_status(
                credential_id=credential_id,
                tag_id=None,  # No specific tag for this test
                success=True
            )
        
        # Calculate time taken
        time_taken = time.time() - start_time
        
        return {
            "success": True,
            "message": "Connection successful",
            "time_taken": time_taken,
            "device_info": device_info
        }
    except Exception as e:
        # Calculate time taken
        time_taken = time.time() - start_time
        
        # Record connection failure
        if device_id:
            credential_store.update_credential_status(
                credential_id=credential_id,
                tag_id=None,  # No specific tag for this test
                success=False
            )
        
        return {
            "success": False,
            "message": f"Connection failed: {str(e)}",
            "time_taken": time_taken,
            "device_info": None
        }
    finally:
        # Ensure connection is closed
        try:
            connector.disconnect()
        except Exception as e:
            logger.warning(f"Error disconnecting: {str(e)}")

def bulk_associate_credentials_with_tags(
    db: Session, 
    credential_ids: List[str], 
    tag_ids: List[str],
    priority: float = 0.0
) -> Dict[str, Any]:
    """
    Associate multiple credentials with multiple tags.
    
    Args:
        db: Database session
        credential_ids: List of credential IDs
        tag_ids: List of tag IDs
        priority: Priority for the associations
        
    Returns:
        Dict with operation results
    """
    results = {
        "success": True,
        "successful_operations": 0,
        "failed_operations": 0,
        "failures": []
    }
    
    credential_store = get_credential_store()
    cs_db = credential_store.get_db()
    
    try:
        for credential_id in credential_ids:
            # Check if credential exists
            cred = cs_db.query(Credential).filter(Credential.id == credential_id).first()
            if not cred:
                results["failed_operations"] += len(tag_ids)
                for tag_id in tag_ids:
                    results["failures"].append({
                        "credential_id": credential_id,
                        "tag_id": tag_id,
                        "reason": "Credential not found"
                    })
                continue
            
            for tag_id in tag_ids:
                # Check if tag exists
                tag = db.query(Tag).filter(Tag.id == tag_id).first()
                if not tag:
                    results["failed_operations"] += 1
                    results["failures"].append({
                        "credential_id": credential_id,
                        "tag_id": tag_id,
                        "reason": "Tag not found"
                    })
                    continue
                
                try:
                    # Check if association already exists
                    existing = cs_db.query(CredentialTag).filter(
                        CredentialTag.credential_id == credential_id,
                        CredentialTag.tag_id == tag_id
                    ).first()
                    
                    if existing:
                        # Update priority
                        existing.priority = priority
                        existing.updated_at = datetime.utcnow()
                        results["successful_operations"] += 1
                    else:
                        # Create new association
                        new_association = CredentialTag(
                            id=str(uuid.uuid4()),
                            credential_id=credential_id,
                            tag_id=tag_id,
                            priority=priority
                        )
                        cs_db.add(new_association)
                        results["successful_operations"] += 1
                except Exception as e:
                    results["failed_operations"] += 1
                    results["failures"].append({
                        "credential_id": credential_id,
                        "tag_id": tag_id,
                        "reason": str(e)
                    })
        
        cs_db.commit()
        
        if results["failed_operations"] > 0:
            results["success"] = False
        
        logger.info(f"Bulk associated credentials with tags: {results['successful_operations']} successful, {results['failed_operations']} failed")
        return results
    finally:
        cs_db.close()

def bulk_remove_credentials_from_tags(
    db: Session, 
    credential_ids: List[str], 
    tag_ids: List[str]
) -> Dict[str, Any]:
    """
    Remove multiple credentials from multiple tags.
    
    Args:
        db: Database session
        credential_ids: List of credential IDs
        tag_ids: List of tag IDs
        
    Returns:
        Dict with operation results
    """
    results = {
        "success": True,
        "successful_operations": 0,
        "failed_operations": 0,
        "failures": []
    }
    
    credential_store = get_credential_store()
    cs_db = credential_store.get_db()
    
    try:
        for credential_id in credential_ids:
            for tag_id in tag_ids:
                try:
                    # Find the association
                    association = cs_db.query(CredentialTag).filter(
                        CredentialTag.credential_id == credential_id,
                        CredentialTag.tag_id == tag_id
                    ).first()
                    
                    if association:
                        # Remove the association
                        cs_db.delete(association)
                        results["successful_operations"] += 1
                    else:
                        # Association doesn't exist, count as successful
                        results["successful_operations"] += 1
                except Exception as e:
                    results["failed_operations"] += 1
                    results["failures"].append({
                        "credential_id": credential_id,
                        "tag_id": tag_id,
                        "reason": str(e)
                    })
        
        cs_db.commit()
        
        if results["failed_operations"] > 0:
            results["success"] = False
        
        logger.info(f"Bulk removed credentials from tags: {results['successful_operations']} successful, {results['failed_operations']} failed")
        return results
    finally:
        cs_db.close()

async def get_credential_stats(db: Session) -> Dict[str, Any]:
    """
    Get statistics about credentials usage and success rates.
    
    Args:
        db: Database session
        
    Returns:
        Dictionary with various credential usage statistics
    """
    try:
        credential_store = get_credential_store()
        cs_db = credential_store.get_db()
        
        try:
            # Get total counts
            total_credentials = cs_db.query(Credential).count()
            
            # Query to get sum of success and failure counts
            counts = cs_db.query(
                func.sum(Credential.success_count).label("total_success"),
                func.sum(Credential.failure_count).label("total_failure")
            ).first()
            
            total_success = counts.total_success or 0
            total_failure = counts.total_failure or 0
            total_attempts = total_success + total_failure
            
            # Calculate success rate
            success_rate = 0.0
            if total_attempts > 0:
                success_rate = (total_success / total_attempts) * 100
                
            # Get most successful credentials (at least 5 attempts and success rate > 0)
            most_successful = []
            most_successful_query = cs_db.query(Credential).filter(
                (Credential.success_count + Credential.failure_count) >= 5
            ).order_by(
                (Credential.success_count / (Credential.success_count + Credential.failure_count)).desc()
            ).limit(5)
            
            for cred in most_successful_query:
                total = cred.success_count + cred.failure_count
                if total > 0:
                    success_rate = (cred.success_count / total) * 100
                    most_successful.append({
                        "id": cred.id,
                        "name": cred.name,
                        "username": cred.username,
                        "success_count": cred.success_count,
                        "failure_count": cred.failure_count,
                        "success_rate": success_rate
                    })
            
            # Get least successful credentials (at least 5 attempts and success rate < 100)
            least_successful = []
            least_successful_query = cs_db.query(Credential).filter(
                (Credential.success_count + Credential.failure_count) >= 5,
                Credential.failure_count > 0
            ).order_by(
                (Credential.success_count / (Credential.success_count + Credential.failure_count)).asc()
            ).limit(5)
            
            for cred in least_successful_query:
                total = cred.success_count + cred.failure_count
                if total > 0:
                    success_rate = (cred.success_count / total) * 100
                    least_successful.append({
                        "id": cred.id,
                        "name": cred.name,
                        "username": cred.username,
                        "success_count": cred.success_count,
                        "failure_count": cred.failure_count,
                        "success_rate": success_rate
                    })
            
            # For now, we don't have credential_usage_log so we'll return empty data for those sections
            device_type_breakdown = []
            recent_failures = []
            recent_successes = []
            usage_over_time = {
                "dates": [],
                "success": [],
                "failure": []
            }
            
            return {
                "total_credentials": total_credentials,
                "total_success_count": total_success,
                "total_failure_count": total_failure,
                "success_rate": success_rate,
                "most_successful": most_successful,
                "least_successful": least_successful,
                "device_type_breakdown": device_type_breakdown,
                "recent_failures": recent_failures,
                "recent_successes": recent_successes,
                "usage_over_time": usage_over_time
            }
        finally:
            cs_db.close()
    except Exception as e:
        logger.error(f"Error getting credential statistics: {str(e)}")
        raise 