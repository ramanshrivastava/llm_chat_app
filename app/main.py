from fastapi import FastAPI, Request
from fastapi.responses import HTMLResponse
from app.core.config import settings
from app.api import chat
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware
import logging
import uvicorn

logger = logging.getLogger(__name__)

class ChatApp:
    """Encapsulates FastAPI application setup."""

    def __init__(self) -> None:
        self.logger = logging.getLogger(__name__)
        logging.basicConfig(
            level=getattr(logging, settings.LOG_LEVEL),
            format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        )
        self.app = FastAPI(
            title="LLM Chat App",
            description="A chat application powered by Azure OpenAI",
            version="0.1.0",
        )
        self._configure_middlewares()
        self._mount_static()
        self._templates = Jinja2Templates(directory="app/templates")
        self.app.include_router(chat.router, prefix="/api", tags=["chat"])
        self._add_routes()

    def _configure_middlewares(self) -> None:
        self.app.add_middleware(
            CORSMiddleware,
            allow_origins=["*"],
            allow_credentials=True,
            allow_methods=["*"],
            allow_headers=["*"],
        )

    def _mount_static(self) -> None:
        self.app.mount("/static", StaticFiles(directory="app/static"), name="static")

    def _add_routes(self) -> None:
        @self.app.get("/", response_class=HTMLResponse)
        async def root(request: Request):
            return self._templates.TemplateResponse("index.html", {"request": request})

        @self.app.get("/health")
        async def health_check():
            return {"status": "healthy"}


def create_app() -> FastAPI:
    return ChatApp().app


app = create_app()

if __name__ == "__main__":
    logger.info(f"Starting server on {settings.HOST}:{settings.PORT}")
    uvicorn.run(
        "app.main:app",
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )