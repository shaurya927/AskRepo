from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String
from app.models.base import BaseModel

class Repository(BaseModel):
    __tablename__ = "repositories"
    name: Mapped[str] = mapped_column(String, index=True)
    url: Mapped[str | None] = mapped_column(String, nullable=True)
    source: Mapped[str] = mapped_column(String) # github/zip
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, default="pending")
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
