from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.config import Settings


def setup_cors(app: FastAPI, settings: Settings) -> None:
    """Configure CORS middleware with environment-specific settings."""
    
    origins = settings.ALLOWED_ORIGINS
    
    if settings.APP_ENV == "development":
        # More permissive in development
        origins.extend([
            "http://localhost:3000",
            "http://localhost:3001",
            "http://127.0.0.1:3000",
            "http://127.0.0.1:8000",
        ])
    
    app.add_middleware(
        CORSMiddleware,
        allow_origins=origins,
        allow_credentials=True,
        allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
        allow_headers=["*"],
        expose_headers=["X-Total-Count", "X-Request-ID"],
        max_age=3600,  # Cache preflight requests for 1 hour
    )