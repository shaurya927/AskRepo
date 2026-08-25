import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class CodeImport(BaseModel):
    __tablename__ = "code_imports"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String)
    names: Mapped[list] = mapped_column(JSON, default=list)
    is_relative: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_path: Mapped[str | None] = mapped_column(String, nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    line: Mapped[int] = mapped_column(Integer)
