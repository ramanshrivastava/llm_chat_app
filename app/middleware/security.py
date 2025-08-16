from fastapi import Request, Response
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import hashlib
import hmac


class SecurityMiddleware(BaseHTTPMiddleware):
    """Enhanced security middleware with various protections."""
    
    def __init__(self, app: ASGIApp, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to all responses."""
        response = await call_next(request)
        
        # Security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        
        # Content Security Policy
        csp = (
            "default-src 'self'; "
            "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
            "style-src 'self' 'unsafe-inline'; "
            "img-src 'self' data: https:; "
            "font-src 'self' data:; "
            "connect-src 'self';"
        )
        response.headers["Content-Security-Policy"] = csp
        
        # Strict Transport Security (for HTTPS)
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        
        return response


def setup_trusted_host(app: ASGIApp, allowed_hosts: list[str]) -> ASGIApp:
    """Setup trusted host middleware for production."""
    return TrustedHostMiddleware(app, allowed_hosts=allowed_hosts)


class CSRFMiddleware(BaseHTTPMiddleware):
    """CSRF protection middleware for state-changing operations."""
    
    def __init__(self, app: ASGIApp, secret_key: str):
        super().__init__(app)
        self.secret_key = secret_key.encode()
    
    def generate_csrf_token(self, session_id: str) -> str:
        """Generate CSRF token for a session."""
        message = f"{session_id}".encode()
        return hmac.new(self.secret_key, message, hashlib.sha256).hexdigest()
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Validate CSRF tokens for POST/PUT/DELETE requests."""
        if request.method in ["POST", "PUT", "DELETE", "PATCH"]:
            # Skip CSRF for API endpoints (they should use API keys)
            if not request.url.path.startswith("/api/"):
                csrf_token = request.headers.get("X-CSRF-Token")
                if not csrf_token:
                    # Check form data as fallback
                    form = await request.form()
                    csrf_token = form.get("csrf_token")
                
                # Validate token (implement validation logic based on your session management)
                # This is a simplified example
                if not csrf_token:
                    from fastapi import HTTPException
                    raise HTTPException(status_code=403, detail="CSRF token missing")
        
        return await call_next(request)