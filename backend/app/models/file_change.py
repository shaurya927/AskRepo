import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Text, ForeignKey
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class FileChange(BaseModel):
    __tablename__ = "file_changes"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    commit_sha: Mapped[str] = mapped_column(String(40), index=True)
    file_path: Mapped[str] = mapped_column(String, index=True)
    change_type: Mapped[str] = mapped_column(String)  # added, modified, deleted, renamed
    insertions: Mapped[int] = mapped_column(Integer, default=0)
    deletions: Mapped[int] = mapped_column(Integer, default=0)
    patch: Mapped[str | None] = mapped_column(Text, nullable=True)
