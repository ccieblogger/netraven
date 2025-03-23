"""
Authentication router for NetRaven web API.

This module handles authentication endpoints for token issuance and management.
"""

from typing import List, Optional, Dict
from datetime import datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer

from netraven.core.auth import jwt, AuthError
from netraven.core.token_store import token_store
from netraven.core.logging import get_logger
from netraven.web.auth import (
    authenticate_user,
    create_user_token,
    create_service_token,
    get_current_principal,
    require_scope,
    UserPrincipal,
    extract_token_from_header
)
from netraven.web.models.auth import (
    TokenRequest,
    TokenResponse,
    ServiceTokenRequest,
    TokenMetadata
)
from netraven.web.database import get_db
from sqlalchemy.orm import Session
from netraven.web.services.audit_service import AuditService

# Setup logger
logger = get_logger("netraven.web.routers.auth")

# Create router
router = APIRouter(prefix="", tags=["authentication"])

# Security scheme for OpenAPI
security = HTTPBearer()

# Track failed login attempts for rate limiting
# This is a simple in-memory implementation
# In a production environment, this should be stored in a distributed cache like Redis
login_attempts = {}
MAX_LOGIN_ATTEMPTS = 5  # Maximum failed attempts before rate limiting
LOCKOUT_PERIOD = 15 * 60  # 15 minutes in seconds


@router.post("/token", response_model=TokenResponse)
async def login_for_access_token(form_data: TokenRequest, request: Request, db: Session = Depends(get_db)):
    """
    Issue a JWT token for user authentication.
    
    This endpoint authenticates a user with username and password,
    and returns a JWT token if authentication is successful.
    """
    client_ip = request.client.host if request.client else "unknown"
    
    # Check for rate limiting
    key = f"{form_data.username}:{client_ip}"
    
    # Check if user is locked out due to too many failed attempts
    if key in login_attempts:
        attempts = login_attempts[key]
        if attempts["count"] >= MAX_LOGIN_ATTEMPTS:
            # Check if the lockout period has expired
            lockout_time = attempts["timestamp"]
            if (datetime.utcnow() - lockout_time).total_seconds() < LOCKOUT_PERIOD:
                logger.warning(f"Rate limited login attempt: username={form_data.username}, ip={client_ip}")
                
                # Log rate limiting to audit log
                AuditService.log_auth_event(
                    db=db,
                    event_name="login_rate_limited",
                    actor_id=form_data.username,
                    status="failure",
                    description=f"Login attempt rate limited after {MAX_LOGIN_ATTEMPTS} failed attempts",
                    event_metadata={
                        "ip_address": client_ip,
                        "attempts": attempts["count"],
                        "lockout_time": lockout_time.isoformat()
                    },
                    request=request
                )
                
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Too many failed login attempts. Please try again later."
                )
            else:
                # Reset attempts if lockout period has expired
                login_attempts[key] = {"count": 0, "timestamp": datetime.utcnow()}
    else:
        # Initialize attempts counter for new IP/username combinations
        login_attempts[key] = {"count": 0, "timestamp": datetime.utcnow()}
    
    try:
        # Authenticate user
        user = authenticate_user(form_data.username, form_data.password)
        if not user:
            # Increment failed attempts
            login_attempts[key]["count"] += 1
            login_attempts[key]["timestamp"] = datetime.utcnow()
            
            # Standardized security log for failed login
            logger.warning(f"Authentication failed: username={form_data.username}, ip={client_ip}, attempts={login_attempts[key]['count']}")
            
            # Log failed login to audit log
            AuditService.log_auth_event(
                db=db,
                event_name="login_failed",
                actor_id=form_data.username,
                status="failure",
                description=f"Failed login attempt: Invalid username or password",
                event_metadata={
                    "ip_address": client_ip,
                    "attempt_number": login_attempts[key]["count"] if key in login_attempts else 1
                },
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Reset failed attempts on successful login
        if key in login_attempts:
            login_attempts.pop(key)
        
        # Create and return token
        token = create_user_token(user)
        
        # Decode token to get expiration
        token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
        expires_at = None
        if "exp" in token_data:
            expires_at = datetime.fromtimestamp(token_data["exp"])
        
        # Standardized security log for successful login
        logger.info(f"Authentication successful: username={user.username}, token_id={token_data.get('jti', 'unknown')}, ip={client_ip}")
        
        # Log successful login to audit log
        AuditService.log_auth_event(
            db=db,
            event_name="login_success",
            actor_id=user.username,
            status="success",
            description=f"Successful login",
            event_metadata={
                "ip_address": client_ip,
                "username": user.username,
                "email": user.email
            },
            request=request
        )
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at
        )
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error during authentication: {str(e)}")
        
        # Log error to audit log
        AuditService.log_auth_event(
            db=db,
            event_name="login_error",
            actor_id=form_data.username,
            status="error",
            description=f"Error during authentication: {str(e)}",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Authentication error: {str(e)}"
        )


@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(request: Request, db: Session = Depends(get_db)):
    """
    Refresh an existing token to extend its expiration time.
    
    This endpoint takes an existing valid token and issues a new token with a fresh expiration time.
    The original token is revoked to prevent reuse.
    """
    try:
        # Extract token from Authorization header
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Token refresh failed: No Authorization header")
            
            # Log to audit log
            AuditService.log_auth_event(
                db=db,
                event_name="token_refresh_failed",
                status="failure",
                description="Token refresh failed: No Authorization header",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No Authorization header found",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning("Token refresh failed: Invalid Authorization header format")
            
            # Log to audit log
            AuditService.log_auth_event(
                db=db,
                event_name="token_refresh_failed",
                status="failure",
                description="Token refresh failed: Invalid Authorization header format",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        # Validate the token
        try:
            # Decode the token to extract claims
            payload = jwt.decode(
                token,
                "dummy-key-not-used",
                options={"verify_signature": False}
            )
            
            # Extract token ID and check if it's valid
            token_id = payload.get("jti")
            if not token_id:
                logger.warning("Token refresh failed: Token missing 'jti' claim")
                
                # Log to audit log
                AuditService.log_auth_event(
                    db=db,
                    event_name="token_refresh_failed",
                    status="failure",
                    description="Token refresh failed: Token missing 'jti' claim",
                    request=request
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token format: missing token ID (jti)",
                    headers={"WWW-Authenticate": "Bearer"},
                )
                
            # Check if token is in token store (not revoked)
            if not token_store.is_valid_token(token_id):
                logger.warning(f"Token refresh failed: Invalid or revoked token {token_id}")
                
                # Log to audit log
                AuditService.log_auth_event(
                    db=db,
                    event_name="token_refresh_failed",
                    status="failure",
                    description=f"Token refresh failed: Invalid or revoked token {token_id}",
                    event_metadata={"token_id": token_id},
                    request=request
                )
                
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked token",
                    headers={"WWW-Authenticate": "Bearer"},
                )
            
            # Check token expiration
            if "exp" in payload:
                now = datetime.utcnow().timestamp()
                exp = payload.get("exp")
                
                # Calculate time until expiration
                time_until_expiration = exp - now
                
                # Log remaining time for debugging
                logger.debug(f"Token {token_id} expires in {time_until_expiration:.2f} seconds")
                
                # If token is too far from expiration (more than 10 minutes), reject refresh
                # This prevents users from constantly refreshing tokens that are still valid for a long time
                if time_until_expiration > 600:  # 10 minutes in seconds
                    logger.warning(f"Token refresh rejected: Token {token_id} not near expiration (still valid for {time_until_expiration:.2f} seconds)")
                    
                    # Log to audit log
                    AuditService.log_auth_event(
                        db=db,
                        event_name="token_refresh_rejected",
                        status="failure",
                        actor_id=payload.get("sub"),
                        description=f"Token refresh rejected: Token not near expiration",
                        event_metadata={
                            "token_id": token_id, 
                            "time_until_expiration": time_until_expiration,
                            "exp": exp,
                            "now": now
                        },
                        request=request
                    )
                    
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail="Token is not near expiration yet"
                    )
            
            # Get token metadata for user information
            username = payload.get("sub")
            token_type = payload.get("type", "unknown")
            scopes = payload.get("scope", [])
            
            # Only allow refresh for user tokens, not service tokens
            if token_type != "user":
                logger.warning(f"Token refresh failed: Only user tokens can be refreshed, got {token_type}")
                
                # Log to audit log
                AuditService.log_auth_event(
                    db=db,
                    event_name="token_refresh_failed",
                    status="failure",
                    description=f"Token refresh failed: Only user tokens can be refreshed, got {token_type}",
                    event_metadata={"token_id": token_id, "token_type": token_type},
                    request=request
                )
                
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only user tokens can be refreshed"
                )
            
            # Revoke the old token to prevent reuse
            token_store.revoke_token(token_id)
            logger.info(f"Token revoked for refresh: {token_id}")
            
            # Create a new token with the same permissions
            from netraven.web.models.auth import User
            user = User(
                username=username,
                email=f"{username}@example.com",  # Placeholder email
                permissions=scopes,
                is_active=True
            )
            
            # Create a new token with fresh expiration
            new_token = create_user_token(user)
            
            # Decode new token to get expiration
            new_token_data = jwt.decode(
                new_token,
                "dummy-key-not-used",
                options={"verify_signature": False}
            )
            
            # Get new token expiration time for response
            expires_at = None
            if "exp" in new_token_data:
                expires_at = datetime.fromtimestamp(new_token_data["exp"])
            
            # Log successful token refresh
            logger.info(f"Token refreshed: old={token_id}, new={new_token_data.get('jti')}, user={username}")
            
            # Log to audit log
            AuditService.log_auth_event(
                db=db,
                event_name="token_refreshed",
                actor_id=username,
                status="success",
                description=f"Token refresh successful",
                event_metadata={"token_id": new_token_data.get("jti")},
                request=request
            )
            
            # Return new token response
            return TokenResponse(
                access_token=new_token,
                token_type="bearer",
                expires_at=expires_at
            )
            
        except HTTPException:
            # Re-raise HTTP exceptions
            raise
        except Exception as e:
            logger.warning(f"Token refresh failed during validation: {str(e)}")
            
            # Log to audit log
            AuditService.log_auth_event(
                db=db,
                event_name="token_refresh_failed",
                status="failure",
                description=f"Token refresh failed during validation: {str(e)}",
                request=request
            )
            
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=f"Invalid token: {str(e)}",
                headers={"WWW-Authenticate": "Bearer"},
            )
            
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        # Standardized error handling
        logger.exception(f"Error during token refresh: {str(e)}")
        
        # Log to audit log
        AuditService.log_auth_event(
            db=db,
            event_name="token_refresh_error",
            status="error",
            description=f"Error during token refresh: {str(e)}",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Token refresh error: {str(e)}"
        )


@router.post("/service-token", response_model=TokenResponse)
async def create_service_access_token(
    request: ServiceTokenRequest,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    Create a service token for API access.
    
    This endpoint creates a JWT token for service-to-service authentication
    with specific scopes and an optional expiration.
    """
    try:
        from netraven.web.models.auth import ServiceAccount
        
        # Create service account
        service = ServiceAccount(
            name=request.service_name,
            permissions=request.scopes,
            description=request.description
        )
        
        # Create token
        token = create_service_token(
            service=service,
            expires_in_days=request.expires_in_days
        )
        
        # Decode token to get metadata
        token_data = jwt.decode(
            token,
            "dummy-key-not-used",
            options={"verify_signature": False}
        )
        
        expires_at = None
        if "exp" in token_data:
            expires_at = datetime.fromtimestamp(token_data["exp"])
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="service_token_created",
            actor_id=principal.username,
            target_id=request.service_name,
            target_type="service",
            description=f"Created service token for {request.service_name}",
            event_metadata={
                "token_id": token_data.get("jti"),
                "service_name": request.service_name,
                "expires_at": expires_at.isoformat() if expires_at else None,
                "scopes": request.scopes,
                "description": request.description
            },
            request=request
        )
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at
        )
    except Exception as e:
        logger.exception(f"Error creating service token: {str(e)}")
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="service_token_creation_error",
            actor_id=principal.username,
            target_id=request.service_name,
            target_type="service",
            description=f"Error creating service token: {str(e)}",
            status="error",
            request=request
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error creating service token: {str(e)}"
        )


@router.get("/tokens", response_model=List[TokenMetadata])
async def list_tokens(
    subject: Optional[str] = None,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    List active tokens with optional filtering by subject.
    
    This endpoint requires admin:tokens scope and returns a list of active tokens.
    """
    try:
        # Get tokens from token store
        tokens = token_store.list_tokens(
            filter_criteria={"subject": subject} if subject else None
        )
        
        # Convert to response model
        token_list = [
            TokenMetadata(
                token_id=token["token_id"],
                subject=token["subject"],
                token_type=token["type"],
                created_at=datetime.fromisoformat(token["created"]) if isinstance(token["created"], str) else token["created"],
                created_by=token.get("created_by"),
                expires_at=datetime.fromisoformat(token["expires"]) if token.get("expires") and isinstance(token["expires"], str) else token.get("expires")
            )
            for token in tokens
        ]
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="tokens_listed",
            actor_id=principal.username,
            description=f"Listed tokens" + (f" for subject {subject}" if subject else ""),
            event_metadata={"count": len(token_list), "subject": subject}
        )
        
        return token_list
    except Exception as e:
        logger.exception(f"Error listing tokens: {str(e)}")
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="tokens_listing_error",
            actor_id=principal.username,
            description=f"Error listing tokens: {str(e)}",
            status="error"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error listing tokens: {str(e)}"
        )


@router.delete("/tokens/{token_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_token(
    token_id: str,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    Revoke a specific token by ID.
    
    This endpoint requires admin:tokens scope and revokes (invalidates) a token,
    preventing its further use for authentication.
    """
    try:
        # Get token metadata first for audit log
        token_meta = None
        tokens = token_store.list_tokens(filter_criteria={"token_id": token_id})
        if tokens:
            token_meta = tokens[0]
        
        # Revoke the token
        success = token_store.revoke_token(token_id)
        
        if not success:
            # Log to audit log
            AuditService.log_admin_event(
                db=db,
                event_name="token_revocation_failed",
                actor_id=principal.username,
                target_id=token_id,
                target_type="token",
                description=f"Failed to revoke token: {token_id} (not found)",
                status="failure"
            )
            
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Token with ID {token_id} not found"
            )
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="token_revoked",
            actor_id=principal.username,
            target_id=token_id,
            target_type="token",
            description=f"Revoked token: {token_id}",
            event_metadata=token_meta
        )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error revoking token: {str(e)}")
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="token_revocation_error",
            actor_id=principal.username,
            target_id=token_id,
            target_type="token",
            description=f"Error revoking token: {str(e)}",
            status="error"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking token: {str(e)}"
        )


@router.delete("/tokens", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_all_tokens_for_subject(
    subject: str,
    db: Session = Depends(get_db),
    principal: UserPrincipal = Depends(require_scope(["admin:tokens"]))
):
    """
    Revoke all tokens for a specific subject.
    
    This endpoint requires admin:tokens scope and revokes all tokens
    issued to the specified subject (user or service).
    """
    try:
        # Get tokens for the subject first for audit log
        tokens = token_store.list_tokens(filter_criteria={"subject": subject})
        token_count = len(tokens)
        
        if token_count == 0:
            # Log to audit log
            AuditService.log_admin_event(
                db=db,
                event_name="tokens_revocation_warning",
                actor_id=principal.username,
                target_id=subject,
                description=f"No tokens found for subject: {subject}",
                status="warning"
            )
            
            return None
        
        # Revoke all tokens for the subject
        success = token_store.revoke_tokens_for_subject(subject)
        
        if not success:
            # Log to audit log
            AuditService.log_admin_event(
                db=db,
                event_name="tokens_revocation_failed",
                actor_id=principal.username,
                target_id=subject,
                description=f"Failed to revoke tokens for subject: {subject}",
                status="failure"
            )
            
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to revoke tokens for subject: {subject}"
            )
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="tokens_revoked",
            actor_id=principal.username,
            target_id=subject,
            description=f"Revoked all tokens ({token_count}) for subject: {subject}",
            event_metadata={"token_count": token_count, "token_ids": [t["token_id"] for t in tokens]}
        )
        
        return None
    except HTTPException:
        # Re-raise HTTP exceptions
        raise
    except Exception as e:
        logger.exception(f"Error revoking tokens for subject: {str(e)}")
        
        # Log to audit log
        AuditService.log_admin_event(
            db=db,
            event_name="tokens_revocation_error",
            actor_id=principal.username,
            target_id=subject,
            description=f"Error revoking tokens for subject: {str(e)}",
            status="error"
        )
        
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error revoking tokens for subject: {str(e)}"
        ) 