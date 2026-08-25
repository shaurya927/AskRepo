"""Repository statistics model — aggregate metrics per repository."""

import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, Float, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel


class RepositoryStats(BaseModel):
    __tablename__ = "repository_stats"

    repository_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), unique=True
    )

    # Phase 1 fields
    total_files: Mapped[int] = mapped_column(Integer)
    total_directories: Mapped[int] = mapped_column(Integer)
    total_lines: Mapped[int] = mapped_column(Integer)
    total_size: Mapped[int] = mapped_column(Integer)
    languages: Mapped[dict] = mapped_column(JSON)
    primary_language: Mapped[str | None] = mapped_column(String, nullable=True)
    frameworks: Mapped[list[str]] = mapped_column(JSON)
    package_managers: Mapped[list[str]] = mapped_column(JSON)
    entry_points: Mapped[list[str]] = mapped_column(JSON)
    config_files: Mapped[list[str]] = mapped_column(JSON)
    test_files_count: Mapped[int] = mapped_column(Integer, default=0)

    # Phase 2 fields — code intelligence metrics
    total_functions: Mapped[int] = mapped_column(Integer, default=0)
    total_classes: Mapped[int] = mapped_column(Integer, default=0)
    total_methods: Mapped[int] = mapped_column(Integer, default=0)
    avg_complexity: Mapped[float] = mapped_column(Float, default=0.0)
    max_complexity: Mapped[int] = mapped_column(Integer, default=0)
    complexity_distribution: Mapped[dict] = mapped_column(JSON, default=dict)
    internal_dependencies: Mapped[int] = mapped_column(Integer, default=0)
    external_dependencies: Mapped[int] = mapped_column(Integer, default=0)
