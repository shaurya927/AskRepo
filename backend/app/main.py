"""AskRepo FastAPI application entry point."""

import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from app.core.logging_config import configure_logging
from app.core.cleanup import cleanup_stale_workspaces
from app.middleware.error_handler import register_error_handlers

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Application lifespan: initialize DB, configure logging, clean up stale workspaces."""
    settings = get_settings()
    configure_logging(settings.LOG_LEVEL)

    await init_db()

    # Clean up any orphaned temp directories from previous runs
    cleaned = cleanup_stale_workspaces(settings.TEMP_REPOSITORY_PATH, settings.CLEANUP_MAX_AGE_HOURS)
    if cleaned:
        logger.info("Startup cleanup: removed %d stale workspace(s)", cleaned)

    logger.info("AskRepo v%s started", settings.APP_VERSION)
    yield
    logger.info("AskRepo shutting down")


settings = get_settings()

app = FastAPI(
    title=settings.APP_NAME,
    version=settings.APP_VERSION,
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

# Register global error handlers
register_error_handlers(app)

# CORS — allow frontend to communicate with backend
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.BACKEND_CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Rate limiter
from app.middleware.rate_limiter import RateLimiter  # noqa: E402
app.add_middleware(
    RateLimiter,
    max_analyses=settings.MAX_ANALYSES_PER_DAY,
    max_ai_requests=settings.MAX_AI_REQUESTS_PER_DAY,
)

# Usage tracker
from app.middleware.usage_tracker import UsageTracker  # noqa: E402
app.add_middleware(UsageTracker)

app.include_router(api_router, prefix="/api")
