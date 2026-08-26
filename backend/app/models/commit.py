import uuid
from datetime import datetime
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class Commit(BaseModel):
    __tablename__ = "commits"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    sha: Mapped[str] = mapped_column(String(40), index=True)
    message: Mapped[str] = mapped_column(Text)
    author_name: Mapped[str] = mapped_column(String)
    author_email: Mapped[str] = mapped_column(String)
    authored_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    committed_date: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    files_changed: Mapped[int] = mapped_column(Integer, default=0)
    insertions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
