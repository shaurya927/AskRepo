from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class RepositoryCreateFromURL(BaseModel):
    url: str

class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str | None
    source: str
    description: str | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RepositoryFileResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    path: str
    language: str | None
    size: int
    line_count: int
    is_test: bool
    is_config: bool
    is_entry_point: bool
    model_config = ConfigDict(from_attributes=True)

class RepositoryStatsResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    total_files: int
    total_directories: int
    total_lines: int
    total_size: int
    languages: dict
    primary_language: str | None
    frameworks: list[str]
    package_managers: list[str]
    entry_points: list[str]
    config_files: list[str]
    test_files_count: int
    model_config = ConfigDict(from_attributes=True)
