# NetRaven API Standardization

This document outlines the standardized patterns for API router implementation in the NetRaven application. These patterns should be followed for all new router implementations and when modifying existing routers.

## Standardized Patterns

### 1. Permission Checks

All endpoints that require authentication and authorization should use this standardized permission check pattern:

```python
# Standardized permission check
if not current_principal.has_scope("required:scope") and not current_principal.is_admin:
    logger.warning(f"Access denied: user={current_principal.username}, " 
                 f"resource=resource_name, scope=required:scope, reason=insufficient_permissions")
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Insufficient permissions: required:scope required"
    )
```

### 2. Resource Access Checks

For endpoints that access a specific resource, use the appropriate access check function:

```python
# Use standardized resource access check
resource = check_resource_access(
    principal=current_principal,
    resource_id_or_obj=resource_id,
    required_scope="required:scope",
    db=db
)
```

The framework provides the following access check functions:
- `check_device_access`
- `check_backup_access`
- `check_tag_access`
- `check_tag_rule_access`
- `check_job_log_access`
- `check_user_access`
- `check_scheduled_job_access`

### 3. Error Handling

All endpoints should use standardized error handling with try-except blocks:

```python
try:
    # Operation code
    
    # Standardized access granted log
    logger.info(f"Access granted: user={current_principal.username}, " 
              f"resource=resource_name, scope=required:scope")
    return result
except HTTPException:
    # Re-raise HTTP exceptions
    raise
except Exception as e:
    # Standardized error handling
    logger.exception(f"Error performing operation: {str(e)}")
    raise HTTPException(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        detail=f"Error performing operation: {str(e)}"
    )
```

### 4. Logging Format

#### Access Granted Log

```python
logger.info(f"Access granted: user={current_principal.username}, " 
          f"resource=resource_name, scope=required:scope, action=action_name")
```

#### Access Denied Log

```python
logger.warning(f"Access denied: user={current_principal.username}, " 
             f"resource=resource_name, scope=required:scope, reason=insufficient_permissions")
```

#### Error Log

```python
logger.exception(f"Error message: {str(e)}")
```

## Router Implementation Checklist

When implementing or modifying a router, ensure:

1. All endpoints use the standardized permission check pattern
2. All endpoints use the appropriate resource access check functions
3. All endpoints have try-except blocks for error handling
4. All endpoints use the standardized logging format
5. HTTP status codes are appropriate for the response
6. Error messages are clear and consistent

## Example Implementation

```python
@router.get("/{resource_id}")
async def get_resource(
    resource_id: str,
    current_principal: UserPrincipal = Depends(get_current_principal),
    db: Session = Depends(get_db)
) -> Dict[str, Any]:
    """
    Get a specific resource.
    
    Args:
        resource_id: The resource ID
        current_principal: The authenticated user
        db: Database session
        
    Returns:
        Dict[str, Any]: Resource details
        
    Raises:
        HTTPException: If the resource is not found or user is not authorized
    """
    try:
        # Use standardized resource access check
        resource = check_resource_access(
            principal=current_principal,
            resource_id_or_obj=resource_id,
            required_scope="read:resource",
            db=db
        )
        
        # Standardized access granted log
        logger.info(f"Access granted: user={current_principal.username}, " 
                  f"resource=resource:{resource_id}, scope=read:resource, action=get")
        return resource
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error retrieving resource: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error retrieving resource: {str(e)}"
        )
```

## Security Considerations

- Always validate user permissions before accessing resources
- Use the check_*_access functions for resource-specific access control
- Log all access attempts (successful and failed) for security auditing
- Use appropriate HTTP status codes for different error scenarios
- Provide detailed error messages for easier troubleshooting

By following these standardized patterns, we ensure consistent behavior, better security, and easier maintenance across the entire API. 