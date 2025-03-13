"""
CRUD operations for tag rules in the NetRaven web interface.

This module provides functions for creating, reading, updating, and deleting tag rules,
as well as evaluating rules against devices.
"""

from sqlalchemy.orm import Session
import uuid
import json
from typing import List, Optional, Dict, Any

# Import models and schemas
from netraven.web.models.tag import Tag, TagRule, device_tags
from netraven.web.models.device import Device
from netraven.web.schemas.tag_rule import TagRuleCreate, TagRuleUpdate, RuleCondition, RuleOperator

# Create logger
from netraven.core.logging import get_logger
logger = get_logger(__name__)

def get_tag_rules(
    db: Session, 
    skip: int = 0, 
    limit: int = 100,
    tag_id: Optional[str] = None,
    include_tags: bool = True
) -> List[TagRule]:
    """
    Get all tag rules, optionally filtered by tag.
    
    Args:
        db: Database session
        skip: Number of records to skip
        limit: Maximum number of records to return
        tag_id: Optional tag ID to filter by
        include_tags: Whether to include tag information with each rule
        
    Returns:
        List of tag rules
    """
    query = db.query(TagRule)
    
    if tag_id:
        query = query.filter(TagRule.tag_id == tag_id)
    
    rules = query.offset(skip).limit(limit).all()
    
    # If requested, add tag information to each rule
    if include_tags:
        for rule in rules:
            tag = db.query(Tag).filter(Tag.id == rule.tag_id).first()
            if tag:
                rule.tag_name = tag.name
                rule.tag_color = tag.color
    
    return rules

def get_tag_rule(
    db: Session, 
    rule_id: str,
    include_tag: bool = True
) -> Optional[TagRule]:
    """
    Get a tag rule by ID.
    
    Args:
        db: Database session
        rule_id: Tag rule ID
        include_tag: Whether to include tag information with the rule
        
    Returns:
        Tag rule if found, None otherwise
    """
    rule = db.query(TagRule).filter(TagRule.id == rule_id).first()
    
    if rule and include_tag:
        tag = db.query(Tag).filter(Tag.id == rule.tag_id).first()
        if tag:
            rule.tag_name = tag.name
            rule.tag_color = tag.color
    
    return rule

def create_tag_rule(
    db: Session, 
    rule: TagRuleCreate
) -> TagRule:
    """
    Create a new tag rule.
    
    Args:
        db: Database session
        rule: Tag rule creation data
        
    Returns:
        Created tag rule
    """
    # Convert rule criteria to JSON string
    rule_criteria_json = json.dumps(rule.rule_criteria.dict())
    
    db_rule = TagRule(
        id=str(uuid.uuid4()),
        name=rule.name,
        description=rule.description,
        rule_criteria=rule_criteria_json,
        is_active=rule.is_active,
        tag_id=rule.tag_id
    )
    
    db.add(db_rule)
    db.commit()
    db.refresh(db_rule)
    
    logger.info(f"Created tag rule: {db_rule.name} (ID: {db_rule.id}) for tag ID: {db_rule.tag_id}")
    return db_rule

def update_tag_rule(
    db: Session, 
    rule_id: str, 
    rule: TagRuleUpdate
) -> Optional[TagRule]:
    """
    Update a tag rule.
    
    Args:
        db: Database session
        rule_id: Tag rule ID
        rule: Tag rule update data
        
    Returns:
        Updated tag rule if found, None otherwise
    """
    db_rule = db.query(TagRule).filter(TagRule.id == rule_id).first()
    if not db_rule:
        return None
    
    # Update fields if provided
    if rule.name is not None:
        db_rule.name = rule.name
    if rule.description is not None:
        db_rule.description = rule.description
    if rule.is_active is not None:
        db_rule.is_active = rule.is_active
    if rule.rule_criteria is not None:
        db_rule.rule_criteria = json.dumps(rule.rule_criteria.dict())
    if rule.tag_id is not None:
        db_rule.tag_id = rule.tag_id
    
    db.commit()
    db.refresh(db_rule)
    
    logger.info(f"Updated tag rule: {db_rule.name} (ID: {db_rule.id})")
    return db_rule

def delete_tag_rule(
    db: Session, 
    rule_id: str
) -> bool:
    """
    Delete a tag rule.
    
    Args:
        db: Database session
        rule_id: Tag rule ID
        
    Returns:
        True if rule was deleted, False otherwise
    """
    db_rule = db.query(TagRule).filter(TagRule.id == rule_id).first()
    if not db_rule:
        return False
    
    db.delete(db_rule)
    db.commit()
    
    logger.info(f"Deleted tag rule: {db_rule.name} (ID: {db_rule.id})")
    return True

def evaluate_condition(device: Device, condition: Dict[str, Any]) -> bool:
    """
    Evaluate a condition against a device.
    
    Args:
        device: Device to evaluate
        condition: Condition to evaluate
        
    Returns:
        True if condition matches, False otherwise
    """
    field = condition["field"]
    operator = condition["operator"]
    value = condition["value"]
    
    # Get device attribute
    if not hasattr(device, field):
        logger.warning(f"Field '{field}' not found on device")
        return False
    
    device_value = getattr(device, field)
    if device_value is None:
        return False
    
    # Convert to string for comparison
    device_value = str(device_value)
    
    # Evaluate based on operator
    if operator == "equals":
        return device_value == value
    elif operator == "contains":
        return value in device_value
    elif operator == "startswith":
        return device_value.startswith(value)
    elif operator == "endswith":
        return device_value.endswith(value)
    elif operator == "regex":
        import re
        try:
            return bool(re.match(value, device_value))
        except re.error:
            logger.error(f"Invalid regex pattern: {value}")
            return False
    
    logger.warning(f"Unknown operator: {operator}")
    return False

def evaluate_operator(device: Device, operator_data: Dict[str, Any]) -> bool:
    """
    Evaluate a logical operator against a device.
    
    Args:
        device: Device to evaluate
        operator_data: Operator data
        
    Returns:
        True if operator matches, False otherwise
    """
    operator_type = operator_data["type"]
    conditions = operator_data["conditions"]
    
    if operator_type == "and":
        return all(
            evaluate_condition(device, cond) if "field" in cond
            else evaluate_operator(device, cond)
            for cond in conditions
        )
    elif operator_type == "or":
        return any(
            evaluate_condition(device, cond) if "field" in cond
            else evaluate_operator(device, cond)
            for cond in conditions
        )
    
    logger.warning(f"Unknown operator type: {operator_type}")
    return False

def evaluate_rule_against_device(rule: TagRule, device: Device) -> bool:
    """
    Evaluate a tag rule against a device.
    
    Args:
        rule: Tag rule to evaluate
        device: Device to evaluate against
        
    Returns:
        True if rule matches, False otherwise
    """
    try:
        rule_criteria = json.loads(rule.rule_criteria)
        
        # If rule is a simple condition
        if "field" in rule_criteria:
            return evaluate_condition(device, rule_criteria)
        
        # If rule is a complex operator
        if "type" in rule_criteria:
            return evaluate_operator(device, rule_criteria)
        
        logger.warning(f"Invalid rule criteria format for rule ID: {rule.id}")
        return False
    except Exception as e:
        logger.error(f"Error evaluating rule ID: {rule.id} - {str(e)}")
        return False

def apply_rule(
    db: Session, 
    rule_id: str
) -> Dict[str, Any]:
    """
    Apply a tag rule to all devices.
    
    Args:
        db: Database session
        rule_id: Tag rule ID
        
    Returns:
        Dictionary with results
    """
    rule = db.query(TagRule).filter(TagRule.id == rule_id).first()
    if not rule or not rule.is_active:
        return {
            "success": False,
            "error": "Rule not found or inactive",
            "matched_devices": 0,
            "total_devices": 0
        }
    
    tag = db.query(Tag).filter(Tag.id == rule.tag_id).first()
    if not tag:
        return {
            "success": False,
            "error": "Tag not found",
            "matched_devices": 0,
            "total_devices": 0
        }
    
    # Get all devices
    devices = db.query(Device).all()
    matched_devices = 0
    
    for device in devices:
        # Evaluate rule against device
        if evaluate_rule_against_device(rule, device):
            # Add tag to device if not already present
            if tag not in device.tags:
                device.tags.append(tag)
                matched_devices += 1
    
    db.commit()
    
    logger.info(f"Applied rule '{rule.name}' (ID: {rule.id}): tagged {matched_devices} of {len(devices)} devices")
    
    return {
        "success": True,
        "rule_id": rule_id,
        "rule_name": rule.name,
        "tag_id": tag.id,
        "tag_name": tag.name,
        "matched_devices": matched_devices,
        "total_devices": len(devices)
    }

def test_rule(
    db: Session, 
    rule_criteria: Dict[str, Any]
) -> Dict[str, Any]:
    """
    Test a rule criteria against all devices without applying any changes.
    
    Args:
        db: Database session
        rule_criteria: Rule criteria to test
        
    Returns:
        Dictionary with matching devices
    """
    # Get all devices
    devices = db.query(Device).all()
    matching_devices = []
    
    # Convert rule_criteria to a TagRule object for evaluation
    temp_rule = TagRule(
        id="temp",
        name="Test Rule",
        rule_criteria=json.dumps(rule_criteria)
    )
    
    for device in devices:
        if evaluate_rule_against_device(temp_rule, device):
            matching_devices.append({
                "id": device.id,
                "hostname": device.hostname,
                "ip_address": device.ip_address,
                "device_type": device.device_type
            })
    
    return {
        "total_devices": len(devices),
        "matching_count": len(matching_devices),
        "matching_devices": matching_devices
    } 