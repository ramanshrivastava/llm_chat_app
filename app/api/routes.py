from fastapi import APIRouter, Request
from fastapi.responses import HTMLResponse
from fastapi.templating import Jinja2Templates
from typing import Annotated
from fastapi import Depends

from app.core.dependencies import get_settings
from app.core.config import Settings

# Initialize templates
templates = Jinja2Templates(directory="app/templates")

# Create main router
main_router = APIRouter()


@main_router.get("/", response_class=HTMLResponse, tags=["UI"])
async def root(
    request: Request,
    settings: Annotated[Settings, Depends(get_settings)]
):
    """Serve the main chat interface."""
    return templates.TemplateResponse(
        "index.html", 
        {
            "request": request,
            "app_name": "LLM Chat App",
            "environment": settings.APP_ENV
        }
    )


@main_router.get("/health", tags=["System"])
async def health_check(
    settings: Annotated[Settings, Depends(get_settings)]
):
    """Health check endpoint for monitoring."""
    return {
        "status": "healthy",
        "environment": settings.APP_ENV,
        "provider": settings.LLM_PROVIDER,
        "version": "0.1.0"
    }


@main_router.get("/metrics", tags=["System"])
async def metrics():
    """Basic metrics endpoint."""
    # This could be expanded to include actual metrics
    return {
        "uptime": "placeholder",
        "requests_total": 0,
        "requests_per_second": 0,
        "average_response_time": 0
    }