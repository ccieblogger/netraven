from datetime import datetime, timedelta
import asyncio
import time
from typing import Dict, Any, Optional, Tuple
from fastapi import Request, HTTPException, status
import logging

logger = logging.getLogger(__name__)

class AsyncRateLimiter:
    """Asynchronous rate limiter with TTL-based cleanup and progressive backoff."""
    
    def __init__(self, max_attempts: int = 5, window_seconds: int = 300, max_items: int = 10000, cleanup_interval: int = 60):
        # key: f"{identifier}:{ip_address}" -> value: {"count": int, "timestamp": float, "block_until": Optional[float]}
        self.attempts: Dict[str, Dict[str, Any]] = {}
        self.max_attempts = max_attempts
        self.window_seconds = window_seconds
        self.max_items = max_items
        self.cleanup_interval = cleanup_interval
        self.cleanup_task: Optional[asyncio.Task] = None
        self._lock = asyncio.Lock()
        logger.info(f"AsyncRateLimiter initialized: max_attempts={max_attempts}, window_seconds={window_seconds}, max_items={max_items}")

    async def start_cleanup_task(self):
        """Start the background cleanup task if not already running."""
        async with self._lock:
            if self.cleanup_task is None or self.cleanup_task.done():
                self.cleanup_task = asyncio.create_task(self._cleanup_loop())
                logger.info(f"Rate limiter cleanup task started. Interval: {self.cleanup_interval}s")

    async def stop_cleanup_task(self):
        """Stop the background cleanup task."""
        async with self._lock:
            if self.cleanup_task and not self.cleanup_task.done():
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    logger.info("Rate limiter cleanup task cancelled.")
                self.cleanup_task = None

    async def _cleanup_loop(self):
        """Periodically clean up expired entries."""
        while True:
            try:
                await asyncio.sleep(self.cleanup_interval)
                async with self._lock:
                    self._cleanup_expired()
            except asyncio.CancelledError:
                logger.info("Cleanup loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Error in rate limiter cleanup loop: {str(e)}", exc_info=True)
                # Avoid tight loop on persistent error
                await asyncio.sleep(self.cleanup_interval * 2) 
                
    def _cleanup_expired(self):
        """Remove expired entries. Must be called within the lock."""
        now = time.time()
        expired_keys = [
            key for key, data in self.attempts.items() 
            if (now - data["timestamp"] > self.window_seconds and data.get("block_until", 0) < now)
        ]
        
        count_before = len(self.attempts)
        for key in expired_keys:
            del self.attempts[key]
        
        count_after = len(self.attempts)
        if expired_keys:
            logger.debug(f"Cleaned up {len(expired_keys)} expired rate limit entries. Size before: {count_before}, Size after: {count_after}")

    def _enforce_size_limit(self):
        """Ensure the attempts dictionary doesn't exceed max size. Must be called within the lock."""
        if len(self.attempts) >= self.max_items:
            # Sort by timestamp and remove oldest 10% of entries
            items_to_remove = max(1, int(self.max_items * 0.1)) # Ensure at least one item is removed
            
            # Filter out entries that are currently blocked
            unblocked_items = {k: v for k, v in self.attempts.items() if v.get("block_until", 0) < time.time()}
            
            # Sort the unblocked items by timestamp
            sorted_unblocked = sorted(unblocked_items.items(), key=lambda x: x[1]["timestamp"])
            
            keys_to_remove = [key for key, _ in sorted_unblocked[:items_to_remove]]

            count_before = len(self.attempts)
            for key in keys_to_remove:
                 # Check if key still exists, could have been removed by cleanup
                if key in self.attempts:
                    del self.attempts[key] 
            
            count_after = len(self.attempts)
            logger.warning(f"Rate limit store exceeded max size ({self.max_items}). Removed {len(keys_to_remove)} oldest unblocked entries. Size before: {count_before}, Size after: {count_after}")

    def _get_key(self, identifier: str, request: Request) -> str:
        """Generate a key combining identifier and IP address."""
        client_ip = request.client.host if request.client else "unknown"
        return f"{identifier}:{client_ip}"

    async def check_rate_limit(self, identifier: str, request: Request) -> Tuple[bool, Optional[float]]:
        """
        Check if the rate limit has been exceeded.

        Args:
            identifier: User identifier (username, email, etc.) or endpoint identifier.
            request: FastAPI request object for IP extraction.

        Returns:
            Tuple[bool, Optional[float]]: (allowed, wait_time_seconds)
            - allowed (bool): True if the request is allowed, False otherwise.
            - wait_time_seconds (Optional[float]): Time in seconds the client should wait before retrying, if blocked.
        """
        key = self._get_key(identifier, request)
        now = time.time()

        async with self._lock:
            self._enforce_size_limit() # Check size limit first

            if key in self.attempts:
                data = self.attempts[key]
                
                # Check if currently blocked
                if data.get("block_until", 0) > now:
                    wait_time = data["block_until"] - now
                    logger.warning(f"Rate limit block active for key: {key}. Wait {wait_time:.2f}s")
                    return False, wait_time

                # Check if window expired
                if now - data["timestamp"] > self.window_seconds:
                    # Window expired, reset counter
                    data["count"] = 1
                    data["timestamp"] = now
                    data.pop("block_until", None) # Remove block if it existed
                    logger.debug(f"Rate limit window reset for key: {key}")
                    return True, None
                
                # Check if max attempts reached
                if data["count"] >= self.max_attempts:
                    # Exceeded max attempts, initiate block with progressive backoff
                    data["count"] += 1 # Increment count to calculate backoff correctly
                    excess = data["count"] - self.max_attempts
                    # Backoff multiplier: increases by 1 for every 2 excess attempts, capped at 10x
                    backoff_multiplier = min(10, 1 + excess // 2)  
                    block_time_seconds = self.window_seconds * backoff_multiplier
                    data["block_until"] = now + block_time_seconds
                    data["timestamp"] = now # Update timestamp to start of block
                    
                    logger.warning(f"Rate limit exceeded for key: {key}. Attempts: {data['count']}. Blocking for {block_time_seconds:.2f}s (Multiplier: {backoff_multiplier}x)")
                    return False, block_time_seconds
                
                # Increment attempt count within window
                data["count"] += 1
                logger.debug(f"Rate limit attempt {data['count']}/{self.max_attempts} for key: {key}")

            else:
                # First attempt
                self.attempts[key] = {"count": 1, "timestamp": now}
                logger.debug(f"Rate limit first attempt for key: {key}")
        
        return True, None

    async def reset_attempts(self, identifier: str, request: Request):
        """Reset attempts for a given identifier after a successful operation (e.g., login)."""
        key = self._get_key(identifier, request)
        async with self._lock:
            if key in self.attempts:
                del self.attempts[key]
                logger.info(f"Rate limit attempts reset for key: {key}")

# Singleton instance (can be configured via environment variables or config file later)
# For now, using defaults defined in the class.
rate_limiter = AsyncRateLimiter()

async def get_rate_limiter() -> AsyncRateLimiter:
    """Dependency injector for the rate limiter instance."""
    # Ensure cleanup task is running
    await rate_limiter.start_cleanup_task() 
    return rate_limiter

# Helper function for use in routers as a dependency
async def rate_limit_dependency(
    identifier_key: str, # e.g., 'username' from form data or path parameter
    request: Request, 
    limiter: AsyncRateLimiter = Depends(get_rate_limiter),
    form_data: Optional[Any] = None, # For extracting identifier from form
    path_params: Optional[Dict[str, Any]] = None # For extracting identifier from path
    ):
    """
    FastAPI Dependency to apply rate limiting.
    Extracts identifier from form_data or path_params based on identifier_key.
    Raises HTTPException 429 if rate limited.
    """
    identifier = None
    if form_data and hasattr(form_data, identifier_key):
        identifier = getattr(form_data, identifier_key)
    elif path_params and identifier_key in path_params:
        identifier = path_params[identifier_key]
    
    if identifier is None:
        # Fallback or raise error if identifier cannot be determined
        # For now, use a generic identifier if key not found - adjust as needed
        logger.warning(f"Could not determine rate limit identifier for key '{identifier_key}'. Using request path.")
        identifier = request.url.path 

    allowed, wait_time = await limiter.check_rate_limit(str(identifier), request)
    if not allowed:
        detail = "Too many requests. Please try again later."
        headers = {}
        if wait_time is not None:
            headers["Retry-After"] = str(int(wait_time)) # Retry-After should be seconds
            detail = f"Too many requests. Please try again in {int(wait_time)} seconds."
        
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers
        )
    # Return the identifier used for potential reset later
    return identifier 


async def reset_rate_limit_for_identifier(
    identifier: str,
    request: Request, 
    limiter: AsyncRateLimiter = Depends(get_rate_limiter)):
    """Helper function/dependency to reset rate limit."""
    await limiter.reset_attempts(identifier, request)
    

# Function to start the cleanup task during application startup
async def start_rate_limit_cleanup():
    await rate_limiter.start_cleanup_task()

# Function to stop the cleanup task during application shutdown
async def stop_rate_limit_cleanup():
    await rate_limiter.stop_cleanup_task() 