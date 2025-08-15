from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from contextlib import asynccontextmanager
import logging

from app.core.config import settings
from app.core.dependencies import get_settings
from app.api import chat
from app.api.routes import main_router
from app.middleware import (
    setup_cors,
    LoggingMiddleware,
    SecurityMiddleware,
    ErrorHandlerMiddleware
)

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
    
    # Startup tasks could go here
    # e.g., initialize database connections, start background tasks
    
    yield
    
    # Shutdown tasks
    logger.info("Shutting down LLM Chat App")


def create_application() -> FastAPI:
    """
    Application factory pattern for creating the FastAPI app.
    This makes the app easier to test and configure.
    """
    
    app = FastAPI(
        title="LLM Chat App",
        description="A secure chat application powered by multiple LLM providers",
        version="0.2.0",  # Bumped version for refactored structure
        lifespan=lifespan,
        docs_url="/docs" if settings.DEBUG else None,
        redoc_url="/redoc" if settings.DEBUG else None,
        openapi_url="/openapi.json" if settings.DEBUG else None,
    )
    
    # Add middlewares in correct order (outermost first)
    app.add_middleware(ErrorHandlerMiddleware, debug=settings.DEBUG)
    app.add_middleware(LoggingMiddleware, log_level=settings.LOG_LEVEL)
    app.add_middleware(SecurityMiddleware, secret_key=settings.SECRET_KEY)
    
    # Setup CORS
    setup_cors(app, settings)
    
    # Mount static files
    app.mount("/static", StaticFiles(directory="app/static"), name="static")
    
    # Include routers
    app.include_router(main_router)
    app.include_router(chat.router, prefix="/api", tags=["chat"])
    
    return app


# Create the application instance
app = create_application()


if __name__ == "__main__":
    import uvicorn
    
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
        log_level=settings.LOG_LEVEL.lower(),
    )