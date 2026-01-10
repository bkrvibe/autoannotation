"""Rate limiting utilities for auth endpoints."""
import time
from collections import defaultdict
from typing import Dict, Tuple, Optional
from threading import Lock
from fastapi import HTTPException, Request, status


class RateLimiter:
    """
    Simple in-memory rate limiter.
    For production, consider using Redis for distributed rate limiting.
    """
    
    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = Lock()
    
    def _cleanup_old_requests(self, key: str, window_seconds: int):
        """Remove requests older than the window."""
        current_time = time.time()
        cutoff = current_time - window_seconds
        self._requests[key] = [t for t in self._requests[key] if t > cutoff]
    
    def is_rate_limited(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60
    ) -> Tuple[bool, int]:
        """
        Check if a key is rate limited.
        
        Args:
            key: Unique identifier (e.g., IP address, email)
            max_requests: Maximum allowed requests in the window
            window_seconds: Time window in seconds
            
        Returns:
            Tuple of (is_limited, remaining_requests)
        """
        with self._lock:
            self._cleanup_old_requests(key, window_seconds)
            
            current_count = len(self._requests[key])
            remaining = max(0, max_requests - current_count)
            
            if current_count >= max_requests:
                return True, 0
            
            # Record this request
            self._requests[key].append(time.time())
            return False, remaining - 1
    
    def check_rate_limit(
        self,
        key: str,
        max_requests: int,
        window_seconds: int = 60,
        error_message: str = "Too many requests. Please try again later."
    ):
        """
        Check rate limit and raise HTTPException if exceeded.
        """
        is_limited, remaining = self.is_rate_limited(key, max_requests, window_seconds)
        
        if is_limited:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=error_message,
                headers={"Retry-After": str(window_seconds)}
            )
        
        return remaining


# Global rate limiter instance
rate_limiter = RateLimiter()


def get_client_ip(request: Request) -> str:
    """Extract client IP from request, considering proxies."""
    # Check for forwarded header (when behind proxy/load balancer)
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        # Take the first IP in the chain
        return forwarded.split(",")[0].strip()
    
    # Check for real IP header
    real_ip = request.headers.get("X-Real-IP")
    if real_ip:
        return real_ip
    
    # Fall back to direct client IP
    if request.client:
        return request.client.host
    
    return "unknown"


def rate_limit_login(request: Request):
    """Rate limit for login endpoint: 5 per minute per IP."""
    from app.core.config import settings
    
    ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        key=f"login:{ip}",
        max_requests=settings.RATE_LIMIT_LOGIN_PER_MINUTE,
        window_seconds=60,
        error_message="Too many login attempts. Please wait before trying again."
    )


def rate_limit_magic_link(email: str):
    """Rate limit for magic link endpoint: 3 per minute per email."""
    from app.core.config import settings
    
    rate_limiter.check_rate_limit(
        key=f"magic_link:{email.lower()}",
        max_requests=settings.RATE_LIMIT_MAGIC_LINK_PER_MINUTE,
        window_seconds=60,
        error_message="Too many magic link requests. Please wait before trying again."
    )


def rate_limit_password_reset(email: str):
    """Rate limit for password reset endpoint: 3 per minute per email."""
    rate_limiter.check_rate_limit(
        key=f"password_reset:{email.lower()}",
        max_requests=3,
        window_seconds=60,
        error_message="Too many password reset requests. Please wait before trying again."
    )


def rate_limit_invite_accept(request: Request):
    """Rate limit for invite acceptance: 5 per minute per IP."""
    ip = get_client_ip(request)
    rate_limiter.check_rate_limit(
        key=f"invite_accept:{ip}",
        max_requests=5,
        window_seconds=60,
        error_message="Too many attempts. Please wait before trying again."
    )
