"""Chat request/response schemas."""

from __future__ import annotations

import uuid
from datetime import datetime

from pydantic import BaseModel, ConfigDict


class ChatRequest(BaseModel):
    message: str
    api_key: str | None = None  # BYOK


class SourceReference(BaseModel):
    file_path: str
    start_line: int
    end_line: int
    symbol_name: str | None = None


class ChatResponse(BaseModel):
    id: uuid.UUID
    message: str
    sources: list[SourceReference]
    query_category: str
    model_used: str


class ChatMessageResponse(BaseModel):
    id: uuid.UUID
    role: str
    content: str
    sources: list[SourceReference] | None = None
    query_category: str | None = None
    model_used: str | None = None
    created_at: datetime
    model_config = ConfigDict(from_attributes=True)


class ChatHistoryResponse(BaseModel):
    messages: list[ChatMessageResponse]
