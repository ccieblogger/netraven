"""
Unit tests for GlobalErrorHandlingMiddleware.
"""

import pytest
from fastapi import FastAPI, Request, HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse, PlainTextResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp, Receive, Scope, Send

from netraven.web.middleware.error_handling import GlobalErrorHandlingMiddleware
from netraven.web.schemas.errors import StandardErrorResponse # For checking response structure

# Mock Request and call_next for middleware testing

class MockRequest:
    def __init__(self, url_path: str = "/test", method: str = "GET"):
        self.url = MockURL(url_path)
        self.method = method

class MockURL:
    def __init__(self, path: str):
        self.path = path

async def call_next_raise_http_exception(request: Request) -> None:
    raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Resource not found")

async def call_next_raise_validation_error(request: Request) -> None:
    # Simulate Pydantic validation errors
    errors = [
        {"loc": ["body", "field1"], "msg": "value is not a valid integer", "type": "type_error.integer"},
        {"loc": ["query", "param"], "msg": "field required", "type": "value_error.missing"},
    ]
    raise RequestValidationError(errors=errors)

async def call_next_raise_unhandled_exception(request: Request) -> None:
    raise ValueError("Something unexpected went wrong")

async def call_next_success(request: Request) -> PlainTextResponse:
    return PlainTextResponse("OK", status_code=200)

# --- Tests --- 

@pytest.mark.asyncio
async def test_middleware_handles_http_exception():
    """Test that HTTPException is caught and formatted correctly."""
    middleware = GlobalErrorHandlingMiddleware(app=None) # app isn't used in dispatch
    request = MockRequest()
    
    response = await middleware.dispatch(request, call_next_raise_http_exception)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_404_NOT_FOUND
    content = response.body.decode()
    # Check structure (using StandardErrorResponse principles)
    assert '"detail":"Resource not found"' in content
    assert '"code":null' in content # No specific code set
    assert '"errors":null' in content # No validation errors

@pytest.mark.asyncio
async def test_middleware_handles_validation_error():
    """Test that RequestValidationError is caught and formatted correctly."""
    middleware = GlobalErrorHandlingMiddleware(app=None)
    request = MockRequest()
    
    response = await middleware.dispatch(request, call_next_raise_validation_error)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
    content = response.body.decode()
    # Check structure
    assert '"detail":"Validation Error"' in content
    assert '"code":"VALIDATION_FAILED"' in content
    assert '"errors":[' in content
    assert '"loc":["body","field1"]' in content
    assert '"loc":["query","param"]' in content
    assert '"msg":"value is not a valid integer"' in content
    assert '"msg":"field required"' in content

@pytest.mark.asyncio
async def test_middleware_handles_unhandled_exception():
    """Test that unhandled exceptions result in a 500 error."""
    middleware = GlobalErrorHandlingMiddleware(app=None)
    request = MockRequest()
    
    response = await middleware.dispatch(request, call_next_raise_unhandled_exception)
    
    assert isinstance(response, JSONResponse)
    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    content = response.body.decode()
    # Check structure
    assert '"detail":"Internal Server Error"' in content
    assert '"code":"INTERNAL_SERVER_ERROR"' in content
    assert '"errors":null' in content

@pytest.mark.asyncio
async def test_middleware_passes_through_successful_response():
    """Test that successful responses are passed through unmodified."""
    middleware = GlobalErrorHandlingMiddleware(app=None)
    request = MockRequest()
    
    response = await middleware.dispatch(request, call_next_success)
    
    assert isinstance(response, PlainTextResponse)
    assert response.status_code == 200
    assert response.body == b"OK" 