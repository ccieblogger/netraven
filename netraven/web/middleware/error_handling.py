"""
Global Error Handling Middleware.

Catches standard FastAPI exceptions (HTTPException, RequestValidationError)
and unhandled Python exceptions, formatting them into a standard error response.
"""

import logging
from typing import Optional

from fastapi import Request, Response, status
from fastapi.exceptions import RequestValidationError, HTTPException as FastAPIHTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint

from netraven.web.schemas.errors import StandardErrorResponse, FieldValidationError

# Get logger for the middleware
logger = logging.getLogger(__name__)

class GlobalErrorHandlingMiddleware(BaseHTTPMiddleware):
    """Catches exceptions and formats them into StandardErrorResponse."""

    async def dispatch(self, request: Request, call_next: RequestResponseEndpoint) -> Response:
        """Middleware entry point."""
        try:
            # Try processing the request
            response = await call_next(request)
            return response
        except RequestValidationError as exc:
            # Handle FastAPI validation errors specifically
            status_code = status.HTTP_422_UNPROCESSABLE_ENTITY
            error_list = [] 
            for error in exc.errors():
                error_list.append(FieldValidationError(
                    loc=list(error["loc"]),
                    msg=error["msg"],
                    type=error["type"]
                ))
            
            error_response = StandardErrorResponse(
                detail="Validation Error",
                code="VALIDATION_FAILED",
                errors=error_list
            )
            logger.warning(
                f"Validation error: Path={request.url.path}, Method={request.method}, Errors={error_list}",
                exc_info=False # Don't need full traceback for validation errors
            )
            return JSONResponse(
                status_code=status_code,
                content=error_response.model_dump(exclude_none=True)
            )
        except FastAPIHTTPException as exc:
            # Handle standard FastAPI HTTPExceptions
            status_code = exc.status_code
            error_response = StandardErrorResponse(
                detail=exc.detail,
                # Optionally, map status codes to custom error codes
                # code=self._get_error_code(status_code) 
            )
            # Log based on severity
            log_level = logging.WARNING if 400 <= status_code < 500 else logging.ERROR
            logger.log(
                log_level,
                f"HTTPException: Status={status_code}, Path={request.url.path}, Method={request.method}, Detail={exc.detail}",
                exc_info=False # Usually don't need full traceback for HTTPErrors
            )
            # Include headers from original exception (like WWW-Authenticate)
            headers = getattr(exc, "headers", None)
            return JSONResponse(
                status_code=status_code,
                content=error_response.model_dump(exclude_none=True),
                headers=headers
            )
        except Exception as exc:
            # Handle unexpected server errors
            status_code = status.HTTP_500_INTERNAL_SERVER_ERROR
            error_response = StandardErrorResponse(
                detail="Internal Server Error",
                code="INTERNAL_SERVER_ERROR"
            )
            logger.error(
                f"Unhandled exception: Path={request.url.path}, Method={request.method}, Error={type(exc).__name__}: {exc}",
                exc_info=True # Include traceback for unexpected errors
            )
            # Potentially add audit log here for critical failures
            # audit_service = ... # Get audit service instance (dependency injection challenge in middleware)
            # await audit_service.log_system_event(...) 
            return JSONResponse(
                status_code=status_code,
                content=error_response.model_dump(exclude_none=True)
            )

    # Optional: Helper to map status codes to your custom codes
    # def _get_error_code(self, status_code: int) -> Optional[str]:
    #     if status_code == 401: return "UNAUTHENTICATED"
    #     if status_code == 403: return "FORBIDDEN"
    #     if status_code == 404: return "NOT_FOUND"
    #     # ... add other mappings
    #     return None 