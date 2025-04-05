"""
Middleware for validating JWT tokens and extracting user principal.
"""

import time
import logging
from typing import Optional, Tuple, Any

from fastapi import Request, HTTPException, status, Response
from fastapi.security.utils import get_authorization_scheme_param
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint
from starlette.responses import JSONResponse

from netraven.core.services.service_factory import ServiceFactory, get_service_factory
from netraven.web.auth import UserPrincipal
from netraven.core.config import settings
from netraven.core.services.token.async_token_store import TokenValidationError, TokenExpiredError, TokenNotFoundError

logger = logging.getLogger(__name__)

# Paths to exclude from token validation
EXCLUDED_PATHS = [
    "/api/v1/auth/login",
    "/api/v1/auth/refresh",
    "/api/v1/health",
    "/docs",
    "/openapi.json",
    # Add other public paths like password reset request (when implemented)
]

class TokenValidationMiddleware(BaseHTTPMiddleware):
    """Validates JWT tokens from Authorization header or cookies."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Middleware dispatch logic."""
        
        # Skip validation for excluded paths
        if any(request.url.path.startswith(path) for path in EXCLUDED_PATHS):
            logger.debug(f"Skipping token validation for excluded path: {request.url.path}")
            return await call_next(request)

        token = None
        principal: Optional[UserPrincipal] = None
        scheme = None
        
        # 1. Try extracting token from Authorization header
        auth_header = request.headers.get("Authorization")
        if auth_header:
            scheme, token = get_authorization_scheme_param(auth_header)
            if scheme.lower() != "bearer":
                logger.warning(f"Unsupported Authorization scheme: {scheme}")
                # Allow request to proceed, endpoint will handle auth if required
                token = None 
                scheme = None

        # 2. If no header token, try extracting from cookie (if enabled)
        if not token and settings.USE_AUTH_COOKIES:
            token = request.cookies.get("access_token")
            if token:
                scheme = "cookie"
                logger.debug("Using token from cookie")

        # If no token found, proceed; endpoint decorators will enforce auth if needed
        if not token or not scheme:
            logger.debug(f"No token found for path: {request.url.path}. Proceeding without principal.")
            request.state.principal = None
            return await call_next(request)
        
        # 3. Validate the token
        try:
            # We need a service factory instance, but middleware doesn't get dependencies easily.
            # We'll get a session manually for the auth service.
            # NOTE: This is not ideal, ideally dependencies are injected.
            # Consider refactoring ServiceFactory or using request state if possible.
            from netraven.web.database import SessionLocal # Direct import - reconsider if possible
            async with SessionLocal() as session:
                factory = get_service_factory(session)
                start_time = time.perf_counter()
                principal = await factory.auth_service.validate_token(token)
                validation_time = (time.perf_counter() - start_time) * 1000
                logger.info(f"Token validated successfully for user: {principal.username}. Scheme: {scheme}. Validation time: {validation_time:.2f} ms")
                request.state.principal = principal
        
        except TokenExpiredError as e:
            logger.warning(f"Token validation failed: Expired token. Scheme: {scheme}. Path: {request.url.path}. Error: {e}")
            return self._build_error_response(status.HTTP_401_UNAUTHORIZED, "Token has expired", scheme)
        except TokenValidationError as e:
            logger.warning(f"Token validation failed: Invalid token. Scheme: {scheme}. Path: {request.url.path}. Error: {e}")
            return self._build_error_response(status.HTTP_401_UNAUTHORIZED, "Invalid token", scheme)
        except TokenNotFoundError as e:
             logger.warning(f"Token validation failed: Token not found in store (likely revoked). Scheme: {scheme}. Path: {request.url.path}. Error: {e}")
             return self._build_error_response(status.HTTP_401_UNAUTHORIZED, "Token not found or revoked", scheme)
        except Exception as e:
            logger.error(f"Unexpected error during token validation: {e}", exc_info=True)
            return self._build_error_response(status.HTTP_500_INTERNAL_SERVER_ERROR, "Internal server error during authentication")

        # Call the next middleware or endpoint
        response = await call_next(request)
        return response

    def _build_error_response(self, status_code: int, detail: str, scheme: Optional[str] = "Bearer") -> JSONResponse:
        """Builds a standard JSON error response."""
        headers = {}
        if status_code == 401 and scheme and scheme.lower() == "bearer":
             # Only add WWW-Authenticate for Bearer scheme to avoid issues with cookies/other methods
            headers["WWW-Authenticate"] = f"Bearer error=\"invalid_token\", error_description=\"{detail}\""
       
        return JSONResponse(
            status_code=status_code,
            content={"detail": detail},
            headers=headers
        ) 