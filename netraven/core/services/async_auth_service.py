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
from netraven.core.services.token.async_token_store import async_token_store
from netraven.web.auth import (
    authenticate_user, # Will be replaced with async version
    UserPrincipal,
    extract_token_from_header
)
from netraven.web.models.auth import TokenRequest, TokenResponse, ServiceTokenRequest, TokenMetadata, User
from netraven.web.services.audit_service import AuditService # Will be replaced with async version

# Setup Redis connection if available for rate limiting
try:
    import redis.asyncio as redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logging.warning("Redis not available for rate limiting, using in-memory fallback")

# Configure logging
logger = logging.getLogger(__name__)

# Rate limiting settings
MAX_LOGIN_ATTEMPTS = 5
LOCKOUT_PERIOD = timedelta(minutes=15)

class LoginAttempt(BaseModel):
    """Model for tracking login attempts."""
    count: int = 0
    timestamp: datetime = datetime.utcnow()

class AsyncAuthService:
    """
    Provides asynchronous methods for handling authentication operations.
    """

    def __init__(self, db_session: AsyncSession, audit_service: Any):
        """
        Initialize the authentication service.

        Args:
            db_session: Async database session.
            audit_service: Audit service instance.
        """
        self._db_session = db_session
        self._audit_service = audit_service
        
        # Set up Redis for rate limiting if available
        self._redis_client = None
        if REDIS_AVAILABLE:
            try:
                self._redis_client = redis.Redis(
                    host="localhost",  # Should be configurable
                    port=6379,          # Should be configurable
                    db=0,
                    decode_responses=True
                )
                logger.info("Redis client initialized for rate limiting")
            except Exception as e:
                logger.error(f"Failed to initialize Redis client: {e}")
                
        # In-memory fallback for rate limiting
        self._login_attempts = {}

    async def _check_rate_limit(self, key: str) -> bool:
        """
        Check if a key is rate limited.
        
        Args:
            key: The rate limit key (usually username:ip)
            
        Returns:
            bool: True if rate limited, False otherwise
        """
        # Try Redis first if available
        if self._redis_client:
            try:
                # Get the current attempt count and timestamp
                attempts_data = await self._redis_client.get(f"ratelimit:{key}")
                
                if attempts_data:
                    attempts = json.loads(attempts_data)
                    count = attempts.get("count", 0)
                    timestamp_str = attempts.get("timestamp")
                    timestamp = datetime.fromisoformat(timestamp_str) if timestamp_str else datetime.utcnow()
                    
                    # Check if still in lockout period
                    if count >= MAX_LOGIN_ATTEMPTS:
                        if (datetime.utcnow() - timestamp) < LOCKOUT_PERIOD:
                            return True
                        else:
                            # Reset after lockout period
                            await self._redis_client.set(
                                f"ratelimit:{key}",
                                json.dumps({"count": 0, "timestamp": datetime.utcnow().isoformat()}),
                                ex=int(LOCKOUT_PERIOD.total_seconds())
                            )
                return False
            except Exception as e:
                logger.error(f"Redis rate limit check failed: {e}")
                # Fall back to in-memory check
        
        # In-memory fallback
        if key in self._login_attempts:
            attempts = self._login_attempts[key]
            if attempts.count >= MAX_LOGIN_ATTEMPTS:
                if (datetime.utcnow() - attempts.timestamp) < LOCKOUT_PERIOD:
                    return True
                else:
                    # Reset after lockout period
                    self._login_attempts[key] = LoginAttempt()
        else:
            self._login_attempts[key] = LoginAttempt()
            
        return False

    async def _increment_login_attempts(self, key: str) -> None:
        """
        Increment login attempt count for a key.
        
        Args:
            key: The rate limit key (usually username:ip)
        """
        # Try Redis first if available
        if self._redis_client:
            try:
                # Get current attempts
                attempts_data = await self._redis_client.get(f"ratelimit:{key}")
                if attempts_data:
                    attempts = json.loads(attempts_data)
                    count = attempts.get("count", 0) + 1
                else:
                    count = 1
                
                # Update attempts
                await self._redis_client.set(
                    f"ratelimit:{key}",
                    json.dumps({"count": count, "timestamp": datetime.utcnow().isoformat()}),
                    ex=int(LOCKOUT_PERIOD.total_seconds())
                )
                return
            except Exception as e:
                logger.error(f"Redis rate limit increment failed: {e}")
                # Fall back to in-memory increment
        
        # In-memory fallback
        if key in self._login_attempts:
            self._login_attempts[key].count += 1
            self._login_attempts[key].timestamp = datetime.utcnow()
        else:
            self._login_attempts[key] = LoginAttempt(count=1)

    async def _reset_login_attempts(self, key: str) -> None:
        """
        Reset login attempts for a key.
        
        Args:
            key: The rate limit key (usually username:ip)
        """
        # Try Redis first if available
        if self._redis_client:
            try:
                await self._redis_client.delete(f"ratelimit:{key}")
                return
            except Exception as e:
                logger.error(f"Redis rate limit reset failed: {e}")
                # Fall back to in-memory reset
        
        # In-memory fallback
        if key in self._login_attempts:
            del self._login_attempts[key]

    async def _async_authenticate_user(self, username: str, password: str) -> Optional[User]:
        """
        Asynchronously authenticate a user.
        
        Args:
            username: User's username
            password: User's password
            
        Returns:
            Optional[User]: User object if authentication succeeds, None otherwise
        """
        # Current authenticate_user function is synchronous - wrap in asyncio.to_thread
        return await asyncio.to_thread(authenticate_user, username, password)

    async def issue_user_token(self, form_data: TokenRequest, request: Request) -> TokenResponse:
        """
        Handles the logic for the /token endpoint.
        - Checks rate limiting
        - Authenticates user
        - Issues token
        - Logs audit events
        """
        client_ip = request.client.host if request.client else "unknown"
        username = form_data.username
        key = f"{username}:{client_ip}"

        # --- Rate Limiting Check ---
        rate_limited = await self._check_rate_limit(key)
        if rate_limited:
            logger.warning(f"Rate limited login attempt: username={username}, ip={client_ip}")
            # TODO: Use async AuditService
            # await self._audit_service.log_auth_event(...)
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Too many failed login attempts. Please try again later."
            )

        # --- Authentication ---
        user = await self._async_authenticate_user(username, form_data.password)
        if not user:
            # Increment failed attempts
            await self._increment_login_attempts(key)
            attempt_count = self._login_attempts.get(key, LoginAttempt()).count if key in self._login_attempts else 1
            logger.warning(f"Authentication failed: username={username}, ip={client_ip}, attempts={attempt_count}")
            # TODO: Use async AuditService
            # await self._audit_service.log_auth_event(...)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect username or password",
                headers={"WWW-Authenticate": "Bearer"},
            )

        # --- Success --- 
        await self._reset_login_attempts(key)

        # Generate a token with proper expiration and refresh metadata
        token_id = str(uuid.uuid4())
        # Add client fingerprint to metadata for security
        token_metadata = {
            "client_ip": client_ip,
            "user_agent": request.headers.get("User-Agent", "unknown"),
            "created_at": datetime.utcnow().isoformat(),
            "refresh_count": 0
        }
        
        # Create token with expiration (using core auth library)
        token = create_token(
            subject=user.username,
            token_type="user",
            scopes=user.permissions,
            expiration=timedelta(hours=1),  # Should be configurable
            metadata=token_metadata
        )

        # Decode token to get expiration (JWT decoding is typically sync)
        try:
            token_data = jwt.decode(token, "dummy-key-not-used", options={"verify_signature": False})
            expires_at = datetime.fromtimestamp(token_data["exp"]) if "exp" in token_data else None
            token_id = token_data.get('jti', 'unknown')
        except Exception as e:
            logger.error(f"Failed to decode created token: {e}")
            expires_at = None
            token_id = 'decode-error'

        logger.info(f"Authentication successful: username={user.username}, token_id={token_id}, ip={client_ip}")
        # TODO: Use async AuditService
        # await self._audit_service.log_auth_event(...)

        # Return token with refresh token (same token for now)
        return TokenResponse(
            access_token=token,
            token_type="bearer",
            expires_at=expires_at,
            refresh_token=token  # In a more secure implementation, this would be a separate token
        )

    async def refresh_user_token(self, request: Request) -> TokenResponse:
        """
        Handles the logic for the /refresh endpoint.
        - Extracts token from header
        - Validates token (existence, type, expiry)
        - Issues new token
        - Logs audit events
        """
        auth_header = request.headers.get("Authorization")
        if not auth_header:
            logger.warning("Token refresh failed: No Authorization header")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="No Authorization header found",
                headers={"WWW-Authenticate": "Bearer"},
            )

        token = extract_token_from_header(auth_header)
        if not token:
            logger.warning("Token refresh failed: Invalid Authorization header format")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid Authorization header format",
                headers={"WWW-Authenticate": "Bearer"},
            )

        try:
            # Decode token claims (sync ok)
            payload = jwt.decode(token, "dummy", options={"verify_signature": False})
            token_id = payload.get("jti")
            username = payload.get("sub")
            token_type = payload.get("type", "unknown")
            scopes = payload.get("scope", [])

            if not token_id:
                logger.warning("Token refresh failed: Token missing 'jti' claim")
                # TODO: Audit log
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Invalid token format: missing token ID (jti)",
                )

            # Check if token is valid using async token store
            token_metadata = await async_token_store.get_token(token_id)
            if not token_metadata:
                logger.warning(f"Token refresh failed: Invalid or revoked token {token_id}")
                # TODO: Audit log
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Invalid or revoked token",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Only allow refresh for user tokens
            if token_type != "user":
                logger.warning(f"Token refresh failed: Only user tokens can be refreshed, got {token_type}")
                # TODO: Audit log
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Only user tokens can be refreshed"
                )

            # Check token expiration - allow refresh only if token is not expired
            # (previous logic was too restrictive, allowing refresh only near expiration)
            now_ts = datetime.utcnow().timestamp()
            exp_ts = payload.get("exp")
            if exp_ts and now_ts > exp_ts:
                logger.warning(f"Token refresh failed: Token {token_id} has expired.")
                # TODO: Audit log
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Token has expired",
                    headers={"WWW-Authenticate": "Bearer"},
                )

            # Track refresh count for potential abuse detection
            refresh_count = token_metadata.get("refresh_count", 0) + 1
            if refresh_count > 100:  # Arbitrary limit, should be configurable
                logger.warning(f"Token refresh rejected: Too many refreshes for token {token_id}")
                # TODO: Audit log
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="Maximum token refresh limit reached"
                )

            # Create a new token with the same permissions and metadata
            client_ip = request.client.host if request.client else "unknown"
            new_token_metadata = {
                **token_metadata,
                "client_ip": client_ip,
                "user_agent": request.headers.get("User-Agent", "unknown"),
                "refresh_count": refresh_count,
                "refreshed_at": datetime.utcnow().isoformat(),
                "previous_token_id": token_id,
            }

            user_for_new_token = User(
                username=username,
                email=f"{username}@example.com",  # Placeholder
                permissions=scopes,
                is_active=True
            )

            # Create new token
            new_token = create_token(
                subject=user_for_new_token.username,
                token_type="user",
                scopes=user_for_new_token.permissions,
                expiration=timedelta(hours=1),  # Should be configurable
                metadata=new_token_metadata
            )

            # Decode new token to get expiration and ID
            new_token_data = jwt.decode(new_token, "dummy", options={"verify_signature": False})
            new_token_id = new_token_data.get("jti", "unknown")
            expires_at = datetime.fromtimestamp(new_token_data["exp"]) if "exp" in new_token_data else None
            
            # Option 1: Invalidate the old token when issuing new one (more secure)
            await async_token_store.revoke_token(token_id)
            logger.info(f"Token invalidated during refresh: {token_id}")
            
            # Option 2: Keep old token valid but mark it as refreshed (for sliding sessions)
            # This would allow users to continue using old tokens for a grace period
            # await async_token_store.update_token_metadata(token_id, {"refreshed_to": new_token_id})

            logger.info(f"Token refreshed: old={token_id}, new={new_token_id}, user={username}")
            # TODO: Audit log

            return TokenResponse(
                access_token=new_token,
                token_type="bearer",
                expires_at=expires_at,
                refresh_token=new_token  # In a more secure implementation, this would be a separate token
            )

        except AuthError as e:
            logger.warning(f"Token refresh failed: {str(e)}")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail=str(e),
                headers={"WWW-Authenticate": "Bearer"},
            )
        except Exception as e:
            logger.error(f"Unexpected error during token refresh: {str(e)}")
            # TODO: Audit log
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Token refresh error: {str(e)}",
            )

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
        tokens = await async_token_store.list_tokens(filter_criteria)
        
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
        token_data = await async_token_store.get_token(token_id)
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
        success = await async_token_store.revoke_token(token_id)
        
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
        count = await async_token_store.revoke_tokens_by_subject(subject)
        
        logger.info(f"Revoked {count} tokens for {subject}, by {principal.username}")
        # TODO: Audit log
        
        return count
