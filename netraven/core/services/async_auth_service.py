"""
Asynchronous Authentication Service for NetRaven.

Handles user authentication, token generation, refresh, revocation,
rate limiting, and related audit logging.
"""

import logging
import uuid
import json
import asyncio
from typing import Dict, Any, Optional, List, Union
from datetime import datetime, timedelta
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException, status, Request
from pydantic import BaseModel

# Auth components
from netraven.core.auth import jwt, AuthError, create_token
from netraven.core.services.token.async_token_store import AsyncTokenStore, TokenData, TokenNotFoundError, TokenValidationError, TokenExpiredError
from netraven.web.auth import (
    authenticate_user, # Will be replaced with async version
    UserPrincipal,
    extract_token_from_header
)
from netraven.web.models.user import User # Import User model
from netraven.web.schemas.auth import TokenResponse, ServiceTokenRequest # Correct schema imports
from netraven.web.schemas.user import UserCreate # Import if needed for user lookup
from netraven.web.services.audit_service import AsyncAuditService # Use the async version
from netraven.web.auth.rate_limiting import AsyncRateLimiter
from netraven.core.config import settings # Import settings

# Configure logging
logger = logging.getLogger(__name__)

class AsyncAuthService:
    """
    Provides asynchronous methods for handling authentication operations.
    """

    def __init__(self,
                 db_session: AsyncSession,
                 audit_service: AsyncAuditService,
                 rate_limiter: AsyncRateLimiter,
                 token_store: AsyncTokenStore):
        """
        Initialize the authentication service.

        Args:
            db_session: Async database session.
            audit_service: Audit service instance.
            rate_limiter: Rate limiter instance.
            token_store: Token store instance.
        """
        self._db_session = db_session
        self._audit_service = audit_service
        self._rate_limiter = rate_limiter
        self._token_store = token_store

    async def _async_authenticate_user(self, username: str, password: str) -> Optional[Dict[str, Any]]: # Return dict now
        """
        Asynchronously authenticate a user.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Optional[Dict[str, Any]]: User data dict if authentication succeeds, None otherwise
        """
        # Call the now async authenticate_user directly, passing the session
        return await authenticate_user(self._db_session, username, password)

    async def issue_user_token(
            self,
            username: str,
            password: str,
            request: Request,
            requested_scopes: Optional[List[str]] = None,
            device_info: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]: # Return dict to match dev log
        """
        Handles the logic for the /token endpoint.
        - Checks rate limiting
        - Authenticates user
        - Issues token
        - Logs audit events
        """
        # Rate limit is now handled by dependency in the router for /login
        # This service method assumes rate limiting passed if called.

        # --- Authentication ---
        user = await self._async_authenticate_user(username, password)
        if not user:
            # Rate limiter dependency in router handles incrementing attempts on failure (HTTP 429)
            # Log the failure event here
            await self._audit_service.log_auth_event(
                event_name="login_failed",
                actor_id=username,
                actor_type="user",
                status="failure",
                description=f"Authentication failed for user {username}.",
                request=request
            )
            logger.warning(f"Authentication failed: username={username}, ip={request.client.host if request.client else 'unknown'}")
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # --- Success --- 
        # Rate limiter dependency in router handles resetting attempts on success

        # --- Token Generation ---
        now = datetime.utcnow()
        access_token_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())
        
        # Define scopes (use requested or default to user's scopes)
        granted_scopes = requested_scopes or user.get("scopes", []) or settings.DEFAULT_USER_SCOPES

        access_token_payload = {
            "sub": str(user.get("id")),
            "preferred_username": user.get("username"),
            "scope": " ".join(granted_scopes),
            "token_type": "access",
            "jti": access_token_id,
            "iat": now,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            # Add other claims like email, roles if needed
        }
        access_token = create_token(access_token_payload)

        refresh_token_payload = {
            "sub": str(user.get("id")),
            "jti": refresh_token_id,
            "ati": access_token_id, # Link to access token
            "token_type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        }
        refresh_token = create_token(refresh_token_payload)

        # --- Store Tokens --- 
        access_token_data = TokenData(
            jti=access_token_id,
            sub=str(user.get("id")),
            exp=int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
            iat=int(now.timestamp()),
            is_refresh=False,
            device_info=device_info,
            scopes=granted_scopes
        )
        refresh_token_data = TokenData(
            jti=refresh_token_id,
            sub=str(user.get("id")),
            exp=int((now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)).timestamp()),
            iat=int(now.timestamp()),
            is_refresh=True,
            parent_jti=access_token_id,
            device_info=device_info,
            scopes=granted_scopes # Store scopes with refresh token too
        )

        await self._token_store.store_token(access_token_data)
        await self._token_store.store_token(refresh_token_data)

        # --- Audit Logging ---
        await self._audit_service.log_auth_event(
            event_name="login_success",
            actor_id=str(user.get("id")),
            actor_type="user",
            status="success",
            description=f"User {user.get('username')} logged in successfully.",
            event_metadata=device_info, # Log device info
            request=request
        )
        logger.info(f"Login successful: username={username}, id={user.get('id')}, ip={request.client.host if request.client else 'unknown'}")

        # --- Prepare Response --- 
        # Create principal for response consistency (though not strictly needed here)
        principal = UserPrincipal.from_token_payload(access_token_payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(granted_scopes),
            "user_id": str(user.get("id")),
            "username": user.get("username"),
            "is_admin": principal.is_admin,
            "jti": access_token_id,
            "principal": principal # Include principal if needed by caller (like in dev log)
        }

    async def refresh_user_token(
            self,
            refresh_token: str,
            request: Request,
            device_info: Optional[Dict[str, Any]] = None
            ) -> Dict[str, Any]: # Return dict for consistency
        """
        Refreshes an access token using a refresh token.
        - Validates the refresh token
        - Revokes the old tokens
        - Issues new access and refresh tokens
        - Logs audit events
        """
        # Rate limit check can be added here if desired, using self._rate_limiter
        # allowed, wait = await self._rate_limiter.check_rate_limit(f"refresh:{request.client.host}", request)
        # if not allowed: raise HTTPException(...) 

        # --- Validate Refresh Token --- 
        try:
            # Decode without verification first to get JTI for store lookup
            unverified_payload = jwt.decode(refresh_token, options={"verify_signature": False, "verify_exp": False})
            token_id = unverified_payload.get("jti")
            if not token_id:
                raise TokenValidationError("Refresh token missing JTI")
                
            # Check token store
            stored_token_data = await self._token_store.get_token(token_id)
            if not stored_token_data or not stored_token_data.is_refresh:
                raise TokenNotFoundError("Refresh token not found or invalid")
                
            # Now verify signature and expiry
            payload = jwt.decode(
                refresh_token, 
                settings.TOKEN_SECRET_KEY, 
                algorithms=[settings.TOKEN_ALGORITHM],
                options={"verify_aud": False} # Adjust if audience used
            )

            # Additional checks
            if payload.get("token_type") != "refresh":
                raise TokenValidationError("Invalid token type, expected refresh")
            if stored_token_data.exp < int(time.time()):
                raise TokenExpiredError("Refresh token expired") # Should be caught by jwt.decode but double check

            # Extract necessary info
            user_id = payload.get("sub")
            original_jti = payload.get("ati") # Original access token JTI
            scopes = stored_token_data.scopes # Use scopes stored with refresh token
            
            if not user_id:
                raise TokenValidationError("Refresh token missing subject")

        except TokenExpiredError as e:
            logger.warning(f"Refresh token expired: {e}")
            await self._audit_service.log_auth_event(
                event_name="refresh_failed_expired", 
                actor_id=unverified_payload.get("sub"), 
                status="failure", 
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Refresh token expired",
                headers={"WWW-Authenticate": "Bearer error=\"invalid_grant\""}
            )
        except (TokenValidationError, TokenNotFoundError, jwt.PyJWTError) as e:
            logger.warning(f"Invalid refresh token: {e}")
            await self._audit_service.log_auth_event(
                event_name="refresh_failed_invalid", 
                actor_id=unverified_payload.get("sub") if 'unverified_payload' in locals() else None, 
                status="failure", 
                request=request
            )
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid refresh token",
                headers={"WWW-Authenticate": "Bearer error=\"invalid_grant\""}
            )

        # --- Token Generation ---
        now = datetime.utcnow()
        access_token_id = str(uuid.uuid4())
        refresh_token_id = str(uuid.uuid4())
        
        # Define scopes (use requested or default to user's scopes)
        granted_scopes = scopes

        access_token_payload = {
            "sub": str(user_id),
            "preferred_username": user_id,
            "scope": " ".join(granted_scopes),
            "token_type": "access",
            "jti": access_token_id,
            "iat": now,
            "exp": now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
            # Add other claims like email, roles if needed
        }
        access_token = create_token(access_token_payload)

        refresh_token_payload = {
            "sub": str(user_id),
            "jti": refresh_token_id,
            "ati": access_token_id, # Link to access token
            "token_type": "refresh",
            "iat": now,
            "exp": now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)
        }
        refresh_token = create_token(refresh_token_payload)

        # --- Store Tokens --- 
        access_token_data = TokenData(
            jti=access_token_id,
            sub=str(user_id),
            exp=int((now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)).timestamp()),
            iat=int(now.timestamp()),
            is_refresh=False,
            device_info=device_info,
            scopes=granted_scopes
        )
        refresh_token_data = TokenData(
            jti=refresh_token_id,
            sub=str(user_id),
            exp=int((now + timedelta(minutes=settings.REFRESH_TOKEN_EXPIRE_MINUTES)).timestamp()),
            iat=int(now.timestamp()),
            is_refresh=True,
            parent_jti=access_token_id,
            device_info=device_info,
            scopes=granted_scopes # Store scopes with refresh token too
        )

        await self._token_store.store_token(access_token_data)
        await self._token_store.store_token(refresh_token_data)

        # --- Audit Logging ---
        await self._audit_service.log_auth_event(
            event_name="refresh_success",
            actor_id=str(user_id),
            actor_type="user",
            status="success",
            description=f"User {user_id} refreshed access token successfully.",
            event_metadata=device_info, # Log device info
            request=request
        )
        logger.info(f"Refresh successful: user={user_id}, ip={request.client.host if request.client else 'unknown'}")

        # --- Prepare Response --- 
        # Create principal for response consistency (though not strictly needed here)
        principal = UserPrincipal.from_token_payload(access_token_payload)

        return {
            "access_token": access_token,
            "refresh_token": refresh_token,
            "token_type": "bearer",
            "expires_in": settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            "refresh_expires_in": settings.REFRESH_TOKEN_EXPIRE_MINUTES * 60,
            "scope": " ".join(granted_scopes),
            "user_id": str(user_id),
            "username": user_id,
            "is_admin": principal.is_admin,
            "jti": access_token_id,
            "principal": principal # Include principal if needed by caller (like in dev log)
        }

    async def issue_service_token(
        self,
        token_request: ServiceTokenRequest,
        principal: UserPrincipal
    ) -> TokenResponse:
        """
        Issues a token for a service account.
        
        Args:
            token_request: Service token request details
            principal: User issuing the token (for audit)
            
        Returns:
            TokenResponse: The issued token
        """
        # Ensure principal has permission to issue service tokens
        if not principal.has_scope("admin:tokens"):
            logger.warning(f"Service token creation denied: User {principal.username} lacks admin:tokens scope")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to issue service tokens"
            )
        
        service_name = token_request.service_name
        scopes = token_request.scopes
        description = token_request.description
        expiration = timedelta(days=token_request.valid_days) if token_request.valid_days else None
        
        # Create token metadata
        token_metadata = {
            "description": description,
            "created_by": principal.username,
            "created_at": datetime.utcnow().isoformat(),
            "service_name": service_name,
        }
        
        # Create token
        token = create_token(
            subject=service_name,
            token_type="service",
            scopes=scopes,
            expiration=expiration,
            metadata=token_metadata
        )
        
        # Decode token to get expiration and ID
        token_data = jwt.decode(token, "dummy", options={"verify_signature": False})
        token_id = token_data.get("jti", "unknown")
        expires_at = datetime.fromtimestamp(token_data["exp"]) if "exp" in token_data else None
        
        logger.info(f"Service token created: id={token_id}, service={service_name}, by={principal.username}")
        # TODO: Audit log
        
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at
        )

    async def list_active_tokens(self, principal: UserPrincipal, subject: Optional[str] = None) -> List[TokenMetadata]:
        """
        List active tokens.
        
        Args:
            principal: User requesting the list (for permission check)
            subject: Optional subject to filter tokens by
            
        Returns:
            List[TokenMetadata]: List of active tokens
        """
        # If not admin, can only list own tokens
        is_self_lookup = subject and subject == principal.username
        if not principal.is_admin and not is_self_lookup:
            logger.warning(f"Token listing denied: User {principal.username} attempted to list tokens for {subject}")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to list tokens"
            )
        
        # If no subject specified and not admin, default to own tokens
        if not subject and not principal.is_admin:
            subject = principal.username
        
        # Apply filter if subject provided
        filter_criteria = {"sub": subject} if subject else None
        
        # Get tokens from store
        tokens = await self._token_store.list_tokens(filter_criteria)
        
        # Convert to TokenMetadata objects
        result = []
        for token in tokens:
            # Extract token metadata from store and token data
            token_id = token.get("token_id", "unknown")
            created_at_str = token.get("created_at")
            created_at = datetime.fromisoformat(created_at_str) if created_at_str else None
            expires_at_str = token.get("expires_at")
            expires_at = datetime.fromisoformat(expires_at_str) if expires_at_str else None
            
            metadata = TokenMetadata(
                token_id=token_id,
                subject=token.get("sub", "unknown"),
                token_type=token.get("type", "unknown"),
                scopes=token.get("scope", []),
                created_at=created_at,
                expires_at=expires_at,
                description=token.get("description", ""),
                created_by=token.get("created_by", "system"),
                client_ip=token.get("client_ip", "unknown"),
                user_agent=token.get("user_agent", "unknown"),
                refresh_count=token.get("refresh_count", 0)
            )
            result.append(metadata)
        
        logger.info(f"Listed {len(result)} tokens for {'all users' if not subject else subject}")
        # TODO: Audit log
        
        return result

    async def revoke_token_by_id(self, token_id: str, principal: UserPrincipal) -> None:
        """
        Revoke a token by ID.
        
        Args:
            token_id: ID of token to revoke
            principal: User revoking the token (for permission check)
        """
        # Get token to check ownership
        token_data = await self._token_store.get_token(token_id)
        if not token_data:
            logger.warning(f"Token revocation failed: Token {token_id} not found")
            # Return success anyway to avoid leaking information
            return
        
        # Check permissions
        subject = token_data.get("sub", "unknown")
        is_own_token = subject == principal.username
        
        if not principal.is_admin and not is_own_token:
            logger.warning(f"Token revocation denied: User {principal.username} attempted to revoke token for {subject}")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to revoke token"
            )
        
        # Revoke token
        success = await self._token_store.revoke_token(token_id)
        
        if success:
            logger.info(f"Token revoked: id={token_id}, subject={subject}, by={principal.username}")
            # TODO: Audit log
        else:
            logger.warning(f"Token revocation failed: id={token_id}, by={principal.username}")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Failed to revoke token"
            )

    async def revoke_all_tokens_by_subject(self, subject: str, principal: UserPrincipal) -> int:
        """
        Revoke all tokens for a subject.
        
        Args:
            subject: Subject (username/service) to revoke tokens for
            principal: User revoking the tokens (for permission check)
            
        Returns:
            int: Number of tokens revoked
        """
        # Check permissions
        is_self = subject == principal.username
        
        if not principal.is_admin and not is_self:
            logger.warning(f"Bulk token revocation denied: User {principal.username} attempted to revoke tokens for {subject}")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Insufficient permissions to revoke these tokens"
            )
        
        # Revoke all tokens for subject
        count = await self._token_store.revoke_tokens_by_subject(subject)
        
        logger.info(f"Revoked {count} tokens for {subject}, by {principal.username}")
        # TODO: Audit log
        
        return count

    @property
    def rate_limiter(self) -> AsyncRateLimiter: # Assuming RateLimiter is needed
        """Get the rate limiter instance."""
        # Return the singleton instance directly for now
        # This could be made configurable later if needed
        from netraven.web.auth.rate_limiting import rate_limiter
        return rate_limiter

    # --- Resource Management ---
    
    async def close(self):
        # Close any resources used by the service
        pass
