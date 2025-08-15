from typing import Optional, Dict, Any
from fastapi import HTTPException, status


class BaseAPIException(HTTPException):
    """Base exception for API errors."""
    
    def __init__(
        self,
        status_code: int,
        detail: str,
        headers: Optional[Dict[str, str]] = None,
        extra: Optional[Dict[str, Any]] = None
    ):
        super().__init__(status_code=status_code, detail=detail, headers=headers)
        self.extra = extra or {}


class ValidationError(BaseAPIException):
    """Raised when request validation fails."""
    
    def __init__(self, detail: str, field: Optional[str] = None):
        extra = {"field": field} if field else {}
        super().__init__(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=detail,
            extra=extra
        )


class AuthenticationError(BaseAPIException):
    """Raised when authentication fails."""
    
    def __init__(self, detail: str = "Authentication required"):
        super().__init__(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=detail,
            headers={"WWW-Authenticate": "Bearer"}
        )


class AuthorizationError(BaseAPIException):
    """Raised when user lacks required permissions."""
    
    def __init__(self, detail: str = "Insufficient permissions"):
        super().__init__(
            status_code=status.HTTP_403_FORBIDDEN,
            detail=detail
        )


class NotFoundError(BaseAPIException):
    """Raised when a resource is not found."""
    
    def __init__(self, resource: str, identifier: Optional[str] = None):
        detail = f"{resource} not found"
        if identifier:
            detail = f"{resource} with id '{identifier}' not found"
        super().__init__(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=detail,
            extra={"resource": resource, "identifier": identifier}
        )


class ConflictError(BaseAPIException):
    """Raised when there's a conflict with existing data."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_409_CONFLICT,
            detail=detail
        )


class RateLimitError(BaseAPIException):
    """Raised when rate limit is exceeded."""
    
    def __init__(
        self,
        detail: str = "Rate limit exceeded",
        retry_after: Optional[int] = None
    ):
        headers = {"Retry-After": str(retry_after)} if retry_after else None
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=detail,
            headers=headers,
            extra={"retry_after": retry_after}
        )


class ExternalServiceError(BaseAPIException):
    """Raised when an external service fails."""
    
    def __init__(
        self,
        service: str,
        detail: Optional[str] = None,
        status_code: int = status.HTTP_503_SERVICE_UNAVAILABLE
    ):
        detail = detail or f"{service} service is currently unavailable"
        super().__init__(
            status_code=status_code,
            detail=detail,
            extra={"service": service}
        )


class LLMProviderError(ExternalServiceError):
    """Raised when LLM provider fails."""
    
    def __init__(self, provider: str, detail: Optional[str] = None):
        super().__init__(
            service=f"LLM Provider ({provider})",
            detail=detail or f"Failed to get response from {provider}"
        )


class DatabaseError(BaseAPIException):
    """Raised when database operation fails."""
    
    def __init__(self, detail: str = "Database operation failed"):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=detail
        )


class ConfigurationError(BaseAPIException):
    """Raised when there's a configuration issue."""
    
    def __init__(self, detail: str):
        super().__init__(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Configuration error: {detail}"
        )