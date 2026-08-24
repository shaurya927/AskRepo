from fastapi import APIRouter
from datetime import datetime, timezone
from app.schemas.health import HealthResponse
from app.core.config import get_settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
