from app.main import app as application

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings
    
    uvicorn.run(
        application,
        host=settings.HOST,
        port=settings.PORT,
        reload=settings.DEBUG,
    )
