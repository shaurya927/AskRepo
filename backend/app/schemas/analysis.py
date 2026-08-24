from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class AnalysisJobResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    status: str
    progress_detail: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AnalysisStatusResponse(BaseModel):
    repository_id: uuid.UUID
    status: str
    progress_detail: str | None
    model_config = ConfigDict(from_attributes=True)
