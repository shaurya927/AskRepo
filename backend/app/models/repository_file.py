import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, Integer, Boolean
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class RepositoryFile(BaseModel):
    __tablename__ = "repository_files"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    path: Mapped[str] = mapped_column(String, index=True)
    language: Mapped[str | None] = mapped_column(String, nullable=True)
    size: Mapped[int] = mapped_column(Integer)
    line_count: Mapped[int] = mapped_column(Integer)
    is_test: Mapped[bool] = mapped_column(Boolean, default=False)
    is_config: Mapped[bool] = mapped_column(Boolean, default=False)
    is_entry_point: Mapped[bool] = mapped_column(Boolean, default=False)
