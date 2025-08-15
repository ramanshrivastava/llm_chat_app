from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from typing import Callable
import logging
import traceback


logger = logging.getLogger(__name__)


class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """Global error handling middleware."""
    
    def __init__(self, app: ASGIApp, debug: bool = False):
        super().__init__(app)
        self.debug = debug
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle errors globally with appropriate responses."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            # Let FastAPI handle HTTPExceptions normally
            raise
            
        except ValueError as e:
            logger.warning(f"Validation error: {str(e)}")
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Validation Error",
                    "detail": str(e),
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
            
        except PermissionError as e:
            logger.warning(f"Permission denied: {str(e)}")
            return JSONResponse(
                status_code=403,
                content={
                    "error": "Permission Denied",
                    "detail": "You don't have permission to access this resource",
                    "request_id": getattr(request.state, "request_id", None)
                }
            )
            
        except Exception as e:
            logger.error(f"Unhandled exception: {str(e)}", exc_info=True)
            
            content = {
                "error": "Internal Server Error",
                "detail": "An unexpected error occurred",
                "request_id": getattr(request.state, "request_id", None)
            }
            
            if self.debug:
                content["debug"] = {
                    "exception": str(e),
                    "traceback": traceback.format_exc()
                }
            
            return JSONResponse(
                status_code=500,
                content=content
            )