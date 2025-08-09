from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.trustedhost import TrustedHostMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from contextlib import asynccontextmanager
import logging
import uvicorn
import time

from app.core.config import settings
from app.api import chat


# Configure logging
logging.basicConfig(
    level=getattr(logging, settings.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler(f"app_{settings.APP_ENV}.log") if settings.APP_ENV != "development" else logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan manager."""
    logger.info(f"Starting LLM Chat App in {settings.APP_ENV} mode")
    logger.info(f"LLM Provider: {settings.LLM_PROVIDER}")
    yield
    logger.info("Shutting down LLM Chat App")

class ChatApp:
    """Encapsulates FastAPI application setup."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        
        self.app = FastAPI(
            title="LLM Chat App",
            description="A secure chat application powered by multiple LLM providers",
            version="0.1.0",
            lifespan=lifespan,
            docs_url="/docs" if settings.DEBUG else None,
            redoc_url="/redoc" if settings.DEBUG else None,
        )
        
        self._configure_middlewares()
        self._mount_static()
        self._templates = Jinja2Templates(directory="app/templates")
        self.app.include_router(chat.router, prefix="/api", tags=["chat"])
        self._add_routes()
        self._add_exception_handlers()

    def _configure_middlewares(self) -> None:
        """Configure security and CORS middlewares."""
        
        # Trusted host middleware for production
        if settings.APP_ENV == "production":
            self.app.add_middleware(
                TrustedHostMiddleware, 
                allowed_hosts=["yourdomain.com", "*.yourdomain.com"]
            )
        
        # CORS middleware with restricted origins
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=settings.ALLOWED_ORIGINS,
            allow_credentials=True,
            allow_methods=["GET", "POST"],
            allow_headers=["*"],
        )
        
        # Add request logging middleware
        @self.app.middleware("http")
        async def log_requests(request: Request, call_next):
            start_time = time.time()
            
            # Log request
            self.logger.info(f"Request: {request.method} {request.url}")
            
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            self.logger.info(f"Response: {response.status_code} in {process_time:.2f}s")
            
            return response

    def _mount_static(self) -> None:
        """Mount static files."""
        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")

    def _add_routes(self) -> None:
        """Add application routes."""
        
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            """Serve the main chat interface."""
            return self._templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/health")
        async def health_check():
            """Health check endpoint for monitoring."""
            return {
                "status": "healthy",
                "environment": settings.APP_ENV,
                "provider": settings.LLM_PROVIDER
            }

    def _add_exception_handlers(self) -> None:
        """Add global exception handlers."""
        
        @self.app.exception_handler(404)
        async def not_found_handler(request: Request, exc: HTTPException):
            return {"error": "Resource not found", "status_code": 404}
        
        @self.app.exception_handler(500)
        async def internal_error_handler(request: Request, exc: Exception):
            self.logger.error(f"Internal server error: {str(exc)}")
            return {"error": "Internal server error", "status_code": 500}


def create_app() -> FastAPI:
    """Create and configure the FastAPI application."""
    return ChatApp().app


app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )