from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import logging
import time
import uuid
from typing import Callable


logger = logging.getLogger(__name__)


class LoggingMiddleware(BaseHTTPMiddleware):
    """Middleware for request/response logging with correlation IDs."""
    
    def __init__(self, app: ASGIApp, log_level: str = "INFO"):
        super().__init__(app)
        self.log_level = log_level
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response with timing information."""
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        start_time = time.time()
        
        # Log request
        logger.info(
            f"[{request_id}] Request: {request.method} {request.url.path}",
            extra={
                "request_id": request_id,
                "method": request.method,
                "path": str(request.url.path),
                "client_host": request.client.host if request.client else None,
            }
        )
        
        try:
            response = await call_next(request)
            
            # Calculate processing time
            process_time = time.time() - start_time
            
            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)
            
            # Log response
            logger.info(
                f"[{request_id}] Response: {response.status_code} in {process_time:.3f}s",
                extra={
                    "request_id": request_id,
                    "status_code": response.status_code,
                    "process_time": process_time,
                }
            )
            
            return response
            
        except Exception as e:
            process_time = time.time() - start_time
            logger.error(
                f"[{request_id}] Error: {str(e)} after {process_time:.3f}s",
                extra={
                    "request_id": request_id,
                    "error": str(e),
                    "process_time": process_time,
                },
                exc_info=True
            )
            raise