"""Git schemas for API responses."""

from __future__ import annotations

from datetime import datetime
from pydantic import BaseModel


class CommitResponse(BaseModel):
    id: str
    sha: str
    message: str
    author_name: str
    author_email: str
    authored_date: datetime
    committed_date: datetime
    files_changed: int
    insertions: int
    deletions: int


class FileChangeResponse(BaseModel):
    file_path: str
    change_type: str
    insertions: int
    deletions: int
    patch: str | None = None


class CommitDetailResponse(CommitResponse):
    file_changes: list[FileChangeResponse]


class HotspotResponse(BaseModel):
    file_path: str
    change_count: int
    total_insertions: int
    total_deletions: int


class TimelineEntry(BaseModel):
    week: str  # ISO week string e.g. "2024-W03"
    commit_count: int
    insertions: int
    deletions: int


class CoChangeResponse(BaseModel):
    file_a: str
    file_b: str
    co_change_count: int
