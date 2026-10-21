"""FastAPI application entrypoint for AI Business Intelligence & Financial Analysis Agent."""

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings
from app.database.connection import init_db
from app.database.seed_data import seed_database
from app.api.routes import router as api_router

# Configure logging
logging.basicConfig(
    level=logging.INFO if settings.DEBUG else logging.WARNING,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("bi_agent")


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Lifecycle event handler for database initialization and dataset seeding."""
    logger.info("Initializing database schema...")
    init_db()

    logger.info("Verifying synthetic dataset...")
    try:
        seed_result = seed_database(force_recreate=False)
        logger.info(f"Database readiness verified: {seed_result}")
    except Exception as e:
        logger.error(f"Error seeding database on startup: {e}")

    yield

    logger.info("Application shutdown completed.")


app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    description="LLM-Powered Business Intelligence and Financial Analysis Agent with LangGraph and Safe SQL.",
    lifespan=lifespan,
)

# Enable CORS for Streamlit frontend and local dev
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register API Router
app.include_router(api_router, prefix="/api")


@app.get("/")
def root():
    return {
        "message": f"Welcome to {settings.APP_NAME}",
        "version": settings.APP_VERSION,
        "docs_url": "/docs",
        "health_check": "/api/health",
    }


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "app.main:app",
        host=settings.API_HOST,
        port=settings.API_PORT,
        reload=settings.DEBUG,
    )
