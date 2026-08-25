"""SQLAlchemy models — import all models here to ensure they register with Base.metadata."""

from app.core.database import Base  # noqa: F401 — needed for metadata.create_all
from app.models.repository import Repository  # noqa: F401
from app.models.analysis_job import AnalysisJob  # noqa: F401
from app.models.repository_file import RepositoryFile  # noqa: F401
from app.models.repository_stats import RepositoryStats  # noqa: F401
from app.models.code_symbol import CodeSymbol  # noqa: F401
from app.models.code_import import CodeImport  # noqa: F401

__all__ = [
    "Base", "Repository", "AnalysisJob", "RepositoryFile",
    "RepositoryStats", "CodeSymbol", "CodeImport",
]
