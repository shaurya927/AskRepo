"""UsageLog model — tracks API request usage for monitoring and rate limiting."""

import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean
from app.models.base import BaseModel


class UsageLog(BaseModel):
    __tablename__ = "usage_logs"
    client_ip: Mapped[str] = mapped_column(String, index=True)
    endpoint: Mapped[str] = mapped_column(String)
    method: Mapped[str] = mapped_column(String(10))
    status_code: Mapped[int] = mapped_column(Integer, default=200)
    response_time_ms: Mapped[int] = mapped_column(Integer, default=0)
    query_category: Mapped[str | None] = mapped_column(String, nullable=True)
    agents_used: Mapped[str | None] = mapped_column(String, nullable=True)
    used_llm: Mapped[bool] = mapped_column(Boolean, default=False)
