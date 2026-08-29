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

    # Preload the embedding model in a separate thread so it doesn't block startup too much,
    # but gets loaded before the user makes a query
    import asyncio
    from app.services.embeddings.embedding_service import get_embedding_service
    
    async def _preload():
        logger.info("Preloading embedding model...")
        try:
            emb_service = get_embedding_service()
            await asyncio.to_thread(emb_service._load_model)
            logger.info("Embedding model preloaded successfully")
        except Exception as e:
            logger.error("Failed to preload embedding model: %s", e)
            
    asyncio.create_task(_preload())
    
    # Auto-ping mechanism to keep Render Free Tier and Neon Database awake
    import os
    async def _keep_alive():
        url = os.environ.get("RENDER_EXTERNAL_URL")
        from app.core.database import async_session_maker
        from sqlalchemy import text
        import httpx
        
        logger.info("Keep-alive task started for %s and Neon DB", url or "local")
        
        async with httpx.AsyncClient() as client:
            while True:
                await asyncio.sleep(240)  # Ping every 4 minutes to prevent 5-min DB sleep
                
                # 1. Keep Neon Postgres Awake
                try:
                    async with async_session_maker() as session:
                        await session.execute(text("SELECT 1"))
                    logger.debug("Database keep-alive ping successful")
                except Exception as e:
                    logger.warning("Database keep-alive ping failed: %s", e)
                
                # 2. Keep Render Web Service Awake
                if url:
                    try:
                        await client.get(f"{url.rstrip('/')}/api/health", timeout=10.0)
                        logger.debug("Web service keep-alive ping successful")
                    except Exception as e:
                        logger.warning("Web service keep-alive ping failed: %s", e)

    asyncio.create_task(_keep_alive())

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
    expose_headers=["X-RateLimit-Limit", "X-RateLimit-Remaining", "X-RateLimit-Reset"],
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

import os
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

# Serve frontend static files if they exist (Production Docker Mode)
if os.path.exists("static"):
    app.mount("/assets", StaticFiles(directory="static/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Allow API routes to return 404 naturally
        if full_path.startswith("api/"):
            raise StarletteHTTPException(status_code=404, detail="Not Found")
            
        file_path = os.path.join("static", full_path)
        if os.path.isfile(file_path):
            return FileResponse(file_path)
        
        # SPA Fallback
        return FileResponse("static/index.html")
