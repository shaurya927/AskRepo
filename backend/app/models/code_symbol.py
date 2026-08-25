import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class CodeSymbol(BaseModel):
    __tablename__ = "code_symbols"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    symbol_type: Mapped[str] = mapped_column(String, index=True)  # function, class, method, interface
    language: Mapped[str] = mapped_column(String)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    class_name: Mapped[str | None] = mapped_column(String, nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    docstring: Mapped[str | None] = mapped_column(Text, nullable=True)
    decorators: Mapped[list] = mapped_column(JSON, default=list)
    complexity: Mapped[int] = mapped_column(Integer, default=1)
