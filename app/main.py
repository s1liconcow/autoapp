from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from app.config.settings import settings
from app.api.routes import router
from app.utils.logger import logger
from app.db.redis_client import redis_client
from app.llm.database_init import DatabaseInitializer

app = FastAPI(
    title=settings.APPLICATION_TITLE,
    description=settings.APPLICATION_DESCRIPTION,
    version="1.0.0",
    debug=settings.DEV_MODE
)

# Include API routes
app.include_router(router)

# Initialize database initializer
db_initializer = DatabaseInitializer(redis_client)

@app.on_event("startup")
async def startup_event():
    """Initialize application on startup"""
    try:
        await db_initializer.initialize_database()
        logger.info("Database initialization complete")
    except Exception as e:
        logger.error("Failed to initialize database: %s", str(e))
        raise

if __name__ == "__main__":
    import uvicorn
    
    uvicorn_config = {
        "app": "app.main:app",
        "host": settings.SERVER_HOST,
        "port": settings.SERVER_PORT,
        "reload": settings.DEV_MODE,
        "reload_dirs": ["templates"] if settings.DEV_MODE else None,
        "workers": settings.WORKERS,
        "log_level": "debug" if settings.DEV_MODE else "info",
    }
    
    logger.info("Server starting with config: %s", uvicorn_config)
    uvicorn.run(**uvicorn_config) 