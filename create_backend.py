import os
from pathlib import Path

base_dir = Path(r"d:\Users\imsha\Documents\Projects\AskRepo\backend")

files = {
    "requirements.txt": """fastapi[standard]
uvicorn[standard]
pydantic
pydantic-settings
sqlalchemy[asyncio]
asyncpg
alembic
gitpython
python-multipart
httpx
python-dotenv
pytest
pytest-asyncio
""",
    "Dockerfile": """FROM python:3.12-slim
RUN apt-get update && apt-get install -y git && rm -rf /var/lib/apt/lists/*
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
EXPOSE 8000
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
""",
    "app/__init__.py": "",
    "app/core/__init__.py": "",
    "app/models/__init__.py": """from .base import Base
from .repository import Repository
from .analysis_job import AnalysisJob
from .repository_file import RepositoryFile
from .repository_stats import RepositoryStats
""",
    "app/schemas/__init__.py": "",
    "app/api/__init__.py": "",
    "app/api/endpoints/__init__.py": "",
    "app/services/__init__.py": "",
    "app/services/repository/__init__.py": "",
    "app/core/config.py": """from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    APP_NAME: str = "AskRepo"
    APP_VERSION: str = "0.1.0"
    DEBUG: bool = False
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/askrepo"
    GITHUB_TOKEN: str | None = None
    LLM_API_KEY: str | None = None
    LLM_MODEL: str = "gpt-4o-mini"
    MAX_REPOSITORY_SIZE_MB: int = 50
    MAX_FILE_COUNT: int = 2000
    MAX_FILE_SIZE_MB: int = 1
    MAX_AI_REQUESTS_PER_DAY: int = 20
    MAX_ANALYSES_PER_DAY: int = 3
    TEMP_REPOSITORY_PATH: str = "./tmp/repos"
    VECTOR_INDEX_PATH: str = "./tmp/indexes"
    BACKEND_CORS_ORIGINS: list[str] = ["http://localhost:5173"]

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')

@lru_cache
def get_settings():
    return Settings()
""",
    "app/core/database.py": """from typing import AsyncGenerator
from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import declarative_base
from app.core.config import get_settings

settings = get_settings()

engine = create_async_engine(settings.DATABASE_URL, echo=settings.DEBUG)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False, class_=AsyncSession)
Base = declarative_base()

async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with AsyncSessionLocal() as session:
        yield session

async def init_db():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
""",
    "app/core/security.py": """import os
from pathlib import Path
import re

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mp3", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".o", ".pyc", ".class", ".woff", ".woff2", ".ttf", ".eot",
    ".ico", ".svg", ".pdf", ".doc", ".docx", ".xls", ".xlsx"
}

def is_path_traversal(path: str) -> bool:
    if os.path.isabs(path) or ".." in path.split(os.sep) or ".." in path.split("/"):
        return True
    return False

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)

def is_binary_extension(ext: str) -> bool:
    return ext.lower() in BINARY_EXTENSIONS

def is_symlink(path: Path) -> bool:
    return path.is_symlink()
""",
    "app/models/base.py": """from datetime import datetime, timezone
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.dialects.postgresql import UUID
from app.core.database import Base

class BaseModel(Base):
    __abstract__ = True
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    created_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc))
    updated_at: Mapped[datetime] = mapped_column(default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))
""",
    "app/models/repository.py": """from sqlalchemy.orm import Mapped, mapped_column
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
""",
    "app/models/analysis_job.py": """from datetime import datetime
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, ForeignKey, DateTime
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class AnalysisJob(BaseModel):
    __tablename__ = "analysis_jobs"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"))
    status: Mapped[str] = mapped_column(String, default="queued")
    progress_detail: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
""",
    "app/models/repository_file.py": """import uuid
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
""",
    "app/models/repository_stats.py": """import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import ForeignKey, Integer, String, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class RepositoryStats(BaseModel):
    __tablename__ = "repository_stats"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), unique=True)
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
""",
    "app/schemas/common.py": """from pydantic import BaseModel
from typing import Generic, TypeVar

T = TypeVar('T')

class StatusResponse(BaseModel):
    status: str
    message: str | None = None

class ErrorResponse(BaseModel):
    detail: str

class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    size: int
""",
    "app/schemas/repository.py": """from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class RepositoryCreateFromURL(BaseModel):
    url: str

class RepositoryResponse(BaseModel):
    id: uuid.UUID
    name: str
    url: str | None
    source: str
    description: str | None
    status: str
    error_message: str | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class RepositoryFileResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    path: str
    language: str | None
    size: int
    line_count: int
    is_test: bool
    is_config: bool
    is_entry_point: bool
    model_config = ConfigDict(from_attributes=True)

class RepositoryStatsResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    total_files: int
    total_directories: int
    total_lines: int
    total_size: int
    languages: dict
    primary_language: str | None
    frameworks: list[str]
    package_managers: list[str]
    entry_points: list[str]
    config_files: list[str]
    test_files_count: int
    model_config = ConfigDict(from_attributes=True)
""",
    "app/schemas/analysis.py": """from pydantic import BaseModel, ConfigDict
import uuid
from datetime import datetime

class AnalysisJobResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    status: str
    progress_detail: str | None
    error_message: str | None
    started_at: datetime | None
    completed_at: datetime | None
    created_at: datetime
    updated_at: datetime
    model_config = ConfigDict(from_attributes=True)

class AnalysisStatusResponse(BaseModel):
    repository_id: uuid.UUID
    status: str
    progress_detail: str | None
    model_config = ConfigDict(from_attributes=True)
""",
    "app/schemas/health.py": """from pydantic import BaseModel

class HealthResponse(BaseModel):
    status: str
    version: str
    timestamp: str
""",
    "app/api/router.py": """from fastapi import APIRouter
from app.api.endpoints import health, repositories, analyses

api_router = APIRouter()
api_router.include_router(health.router, tags=["health"])
api_router.include_router(repositories.router, prefix="/repositories", tags=["repositories"])
api_router.include_router(analyses.router, prefix="/analyses", tags=["analyses"])
""",
    "app/api/endpoints/health.py": """from fastapi import APIRouter
from datetime import datetime, timezone
from app.schemas.health import HealthResponse
from app.core.config import get_settings

router = APIRouter()

@router.get("/health", response_model=HealthResponse)
def get_health():
    settings = get_settings()
    return HealthResponse(
        status="ok",
        version=settings.APP_VERSION,
        timestamp=datetime.now(timezone.utc).isoformat()
    )
""",
    "app/api/endpoints/repositories.py": """from fastapi import APIRouter, Depends, BackgroundTasks, UploadFile, File, Form, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func
import uuid
from app.core.database import get_db
from app.schemas.repository import RepositoryCreateFromURL, RepositoryResponse, RepositoryFileResponse, RepositoryStatsResponse
from app.schemas.common import PaginatedResponse
from app.models.repository import Repository
from app.models.analysis_job import AnalysisJob
from app.models.repository_file import RepositoryFile
from app.models.repository_stats import RepositoryStats
from app.services.repository.analyzer import RepositoryAnalyzer
from app.core.config import get_settings

router = APIRouter()

@router.post("/", response_model=dict)
async def create_repository(
    background_tasks: BackgroundTasks,
    url_data: RepositoryCreateFromURL = None,
    file: UploadFile = File(None),
    db: AsyncSession = Depends(get_db)
):
    if not url_data and not file:
        raise HTTPException(status_code=400, detail="Must provide either URL or zip file")
        
    repo = Repository(
        name="pending",
        source="github" if url_data else "zip",
        url=url_data.url if url_data else None,
        status="pending"
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)

    job = AnalysisJob(repository_id=repo.id, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)

    analyzer = RepositoryAnalyzer(get_settings(), db)
    background_tasks.add_task(analyzer.analyze, job.id, repo.id, url_data.url if url_data else None, file)
    
    return {"repository_id": repo.id, "job_id": job.id}

@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo

@router.get("/{repo_id}/files", response_model=PaginatedResponse[RepositoryFileResponse])
async def get_repository_files(
    repo_id: uuid.UUID,
    page: int = 1,
    size: int = 50,
    language: str | None = None,
    db: AsyncSession = Depends(get_db)
):
    query = select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    if language:
        query = query.where(RepositoryFile.language == language)
        
    total_query = select(func.count()).select_from(query.subquery())
    total_result = await db.execute(total_query)
    total = total_result.scalar_one()

    query = query.offset((page - 1) * size).limit(size)
    result = await db.execute(query)
    items = result.scalars().all()
    
    return PaginatedResponse(items=items, total=total, page=page, size=size)

@router.get("/{repo_id}/stats", response_model=RepositoryStatsResponse)
async def get_repository_stats(repo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
    stats = result.scalar_one_or_none()
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found")
    return stats
""",
    "app/api/endpoints/analyses.py": """from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
import uuid
from app.core.database import get_db
from app.schemas.analysis import AnalysisJobResponse, AnalysisStatusResponse
from app.models.analysis_job import AnalysisJob

router = APIRouter()

@router.get("/{job_id}", response_model=AnalysisJobResponse)
async def get_analysis_job(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job

@router.get("/{job_id}/status", response_model=AnalysisStatusResponse)
async def get_analysis_status(job_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    result = await db.execute(select(AnalysisJob).where(AnalysisJob.id == job_id))
    job = result.scalar_one_or_none()
    if not job:
        raise HTTPException(status_code=404, detail="Job not found")
    return job
""",
    "app/services/repository/file_filter.py": """from pathlib import Path
from app.core.security import is_binary_extension

class FileFilter:
    IGNORED_DIRECTORIES = {".git", "node_modules", "venv", ".venv", "__pycache__", "dist", "build", "target"}
    
    def should_ignore_directory(self, name: str) -> bool:
        return name in self.IGNORED_DIRECTORIES or name.startswith(".")
        
    def should_ignore_file(self, path: Path, max_size: int) -> bool:
        if path.stat().st_size > max_size:
            return True
        if is_binary_extension(path.suffix):
            return True
        return False
        
    def is_minified(self, path: Path) -> bool:
        if path.suffix not in {".js", ".css"}:
            return False
        try:
            with open(path, "r", encoding="utf-8") as f:
                lines = f.readlines()
                if not lines: return False
                avg_len = sum(len(l) for l in lines) / len(lines)
                return avg_len > 200
        except Exception:
            return True
            
    def is_generated(self, path: Path) -> bool:
        try:
            with open(path, "r", encoding="utf-8") as f:
                for i in range(5):
                    line = f.readline().lower()
                    if "generated by" in line or "do not edit" in line:
                        return True
            return False
        except Exception:
            return False
""",
    "app/services/repository/github_service.py": """import re
from pathlib import Path
import httpx
from git import Repo

class GitHubService:
    def validate_url(self, url: str) -> bool:
        return bool(re.match(r"^https?://(www\.)?github\.com/[\w.-]+/[\w.-]+/?$", url))
        
    def parse_url(self, url: str) -> tuple[str, str]:
        parts = url.rstrip("/").split("/")
        return parts[-2], parts[-1]
        
    async def check_repository_exists(self, url: str, token: str | None = None) -> dict:
        if not self.validate_url(url):
            raise ValueError("Invalid GitHub URL")
        owner, repo = self.parse_url(url)
        headers = {"Accept": "application/vnd.github.v3+json"}
        if token:
            headers["Authorization"] = f"token {token}"
        async with httpx.AsyncClient() as client:
            resp = await client.get(f"https://api.github.com/repos/{owner}/{repo}", headers=headers)
            if resp.status_code == 404:
                raise ValueError("Repository not found")
            resp.raise_for_status()
            return resp.json()
            
    def clone_repository(self, url: str, target_dir: Path) -> Path:
        Repo.clone_from(url, target_dir, depth=1)
        return target_dir
""",
    "app/services/repository/zip_service.py": """import zipfile
from pathlib import Path
from fastapi import UploadFile
from app.core.security import is_path_traversal, is_symlink

class ZipService:
    def validate_zip(self, file_path: Path) -> None:
        if not zipfile.is_zipfile(file_path):
            raise ValueError("Invalid ZIP file")
            
    def extract_zip(self, file_path: Path, target_dir: Path, max_size: int, max_files: int) -> Path:
        self.validate_zip(file_path)
        extracted_size = 0
        file_count = 0
        
        with zipfile.ZipFile(file_path, "r") as zf:
            for info in zf.infolist():
                if is_path_traversal(info.filename):
                    raise ValueError("Path traversal detected in ZIP")
                if info.is_dir():
                    continue
                    
                file_count += 1
                if file_count > max_files:
                    raise ValueError(f"Exceeded max file count: {max_files}")
                    
                extracted_size += info.file_size
                if extracted_size > max_size * 1024 * 1024:
                    raise ValueError(f"Exceeded max size: {max_size}MB")
                    
                zf.extract(info, target_dir)
                # Note: Symlink protection would normally go here depending on OS capabilities
        return target_dir
        
    async def save_upload(self, upload_file: UploadFile, target_dir: Path) -> Path:
        file_path = target_dir / upload_file.filename
        with open(file_path, "wb") as f:
            content = await upload_file.read()
            f.write(content)
        return file_path
""",
    "app/services/repository/file_scanner.py": """from pathlib import Path
from dataclasses import dataclass
from app.services.repository.file_filter import FileFilter

@dataclass
class ScanResult:
    files: list[dict]
    stats: dict

class FileScanner:
    LANGUAGE_MAP = {
        ".py": "Python", ".js": "JavaScript", ".ts": "TypeScript", ".tsx": "TypeScript", 
        ".jsx": "JavaScript", ".java": "Java", ".cpp": "C++", ".cc": "C++", ".cxx": "C++",
        ".c": "C", ".h": "C/C++ Header", ".hpp": "C/C++ Header", ".go": "Go", ".rs": "Rust",
        ".rb": "Ruby", ".php": "PHP", ".swift": "Swift", ".kt": "Kotlin", ".scala": "Scala",
        ".cs": "C#", ".html": "HTML", ".css": "CSS", ".scss": "SCSS", ".less": "Less",
        ".json": "JSON", ".yaml": "YAML", ".yml": "YAML", ".toml": "TOML", ".xml": "XML",
        ".md": "Markdown", ".sql": "SQL", ".sh": "Shell", ".bash": "Shell", ".dockerfile": "Dockerfile"
    }
    CONFIG_FILES = {"package.json", "requirements.txt", "pyproject.toml", "pom.xml", "Cargo.toml", "go.mod", "docker-compose.yml"}
    ENTRY_POINT_PATTERNS = {"main.py", "index.js", "main.go", "App.java"}
    
    def scan_repository(self, repo_dir: Path, file_filter: FileFilter, max_file_size: int) -> ScanResult:
        files_data = []
        stats = {
            "total_files": 0, "total_directories": 0, "total_lines": 0, "total_size": 0,
            "languages": {}, "test_files_count": 0, "config_files": [], "entry_points": []
        }
        
        for p in repo_dir.rglob("*"):
            if p.is_dir():
                if file_filter.should_ignore_directory(p.name):
                    continue
                stats["total_directories"] += 1
            elif p.is_file():
                if any(file_filter.should_ignore_directory(part) for part in p.parts):
                    continue
                if file_filter.should_ignore_file(p, max_file_size):
                    continue
                    
                lang = self.detect_language(p)
                size = p.stat().st_size
                lines = 0
                try:
                    with open(p, "r", encoding="utf-8") as f:
                        lines = sum(1 for _ in f)
                except Exception:
                    continue
                    
                is_test = "test" in p.name.lower() or "spec" in p.name.lower()
                is_config = p.name in self.CONFIG_FILES
                is_entry = p.name in self.ENTRY_POINT_PATTERNS
                
                stats["total_files"] += 1
                stats["total_lines"] += lines
                stats["total_size"] += size
                if is_test: stats["test_files_count"] += 1
                if is_config: stats["config_files"].append(p.name)
                if is_entry: stats["entry_points"].append(p.name)
                
                if lang:
                    if lang not in stats["languages"]:
                        stats["languages"][lang] = {"files": 0, "lines": 0, "bytes": 0}
                    stats["languages"][lang]["files"] += 1
                    stats["languages"][lang]["lines"] += lines
                    stats["languages"][lang]["bytes"] += size
                    
                files_data.append({
                    "path": str(p.relative_to(repo_dir).as_posix()),
                    "language": lang,
                    "size": size,
                    "line_count": lines,
                    "is_test": is_test,
                    "is_config": is_config,
                    "is_entry_point": is_entry
                })
                
        return ScanResult(files=files_data, stats=stats)
        
    def detect_language(self, path: Path) -> str | None:
        if path.name.lower() == "dockerfile":
            return "Dockerfile"
        return self.LANGUAGE_MAP.get(path.suffix.lower())
        
    def detect_frameworks(self, repo_dir: Path, files: list) -> list[str]:
        return []
        
    def detect_package_managers(self, repo_dir: Path) -> list[str]:
        return []
""",
    "app/services/repository/analyzer.py": """import uuid
import shutil
from pathlib import Path
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import update
from fastapi import UploadFile
from datetime import datetime, timezone
from app.models.analysis_job import AnalysisJob
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.repository_stats import RepositoryStats
from app.services.repository.file_scanner import FileScanner
from app.services.repository.file_filter import FileFilter
from app.services.repository.github_service import GitHubService
from app.services.repository.zip_service import ZipService

class RepositoryAnalyzer:
    def __init__(self, settings, db: AsyncSession):
        self.settings = settings
        self.db = db
        
    async def _update_job(self, job_id: uuid.UUID, status: str, progress: str = None, error: str = None):
        stmt = update(AnalysisJob).where(AnalysisJob.id == job_id).values(status=status, progress_detail=progress, error_message=error, updated_at=datetime.now(timezone.utc))
        if status == "completed" or status == "failed":
            stmt = stmt.values(completed_at=datetime.now(timezone.utc))
        if status == "cloning" or status == "extracting":
             stmt = stmt.values(started_at=datetime.now(timezone.utc))
        await self.db.execute(stmt)
        await self.db.commit()

    async def _update_repo(self, repo_id: uuid.UUID, status: str, error: str = None):
        stmt = update(Repository).where(Repository.id == repo_id).values(status=status, error_message=error, updated_at=datetime.now(timezone.utc))
        await self.db.execute(stmt)
        await self.db.commit()

    async def analyze(self, job_id: uuid.UUID, repo_id: uuid.UUID, url: str | None, file: UploadFile | None):
        target_dir = Path(self.settings.TEMP_REPOSITORY_PATH) / str(repo_id)
        target_dir.mkdir(parents=True, exist_ok=True)
        
        try:
            if url:
                await self._update_job(job_id, "cloning", "Cloning repository...")
                github = GitHubService()
                github.clone_repository(url, target_dir)
            elif file:
                await self._update_job(job_id, "extracting", "Extracting zip file...")
                zip_svc = ZipService()
                zip_path = await zip_svc.save_upload(file, target_dir)
                extract_dir = target_dir / "extracted"
                extract_dir.mkdir(exist_ok=True)
                zip_svc.extract_zip(zip_path, extract_dir, self.settings.MAX_REPOSITORY_SIZE_MB, self.settings.MAX_FILE_COUNT)
                target_dir = extract_dir
                
            await self._update_job(job_id, "scanning", "Scanning files...")
            scanner = FileScanner()
            filter_obj = FileFilter()
            scan_result = scanner.scan_repository(target_dir, filter_obj, self.settings.MAX_FILE_SIZE_MB * 1024 * 1024)
            
            await self._update_job(job_id, "analyzing", "Saving file data...")
            for f in scan_result.files:
                repo_file = RepositoryFile(repository_id=repo_id, **f)
                self.db.add(repo_file)
                
            stats = scan_result.stats
            primary_lang = max(stats["languages"].items(), key=lambda x: x[1]["bytes"])[0] if stats["languages"] else None
            
            repo_stats = RepositoryStats(
                repository_id=repo_id,
                total_files=stats["total_files"],
                total_directories=stats["total_directories"],
                total_lines=stats["total_lines"],
                total_size=stats["total_size"],
                languages=stats["languages"],
                primary_language=primary_lang,
                frameworks=scanner.detect_frameworks(target_dir, scan_result.files),
                package_managers=scanner.detect_package_managers(target_dir),
                entry_points=stats["entry_points"],
                config_files=stats["config_files"],
                test_files_count=stats["test_files_count"]
            )
            self.db.add(repo_stats)
            
            await self._update_job(job_id, "completed", "Analysis complete")
            await self._update_repo(repo_id, "completed")
            
        except Exception as e:
            await self._update_job(job_id, "failed", error=str(e))
            await self._update_repo(repo_id, "failed", error=str(e))
        finally:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
""",
    "app/main.py": """from fastapi import FastAPI
from app.api.router import api_router
from app.core.config import get_settings
from app.core.database import init_db
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield

settings = get_settings()
app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION, lifespan=lifespan)
app.include_router(api_router, prefix="/api")
""",
    "tests/__init__.py": "",
    "tests/conftest.py": """import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest_asyncio.fixture
async def client():
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        yield ac
""",
    "tests/test_config.py": """from app.core.config import get_settings

def test_settings():
    settings = get_settings()
    assert settings.APP_NAME == "AskRepo"
""",
    "tests/test_security.py": """from app.core.security import is_path_traversal, is_binary_extension, sanitize_filename

def test_path_traversal():
    assert is_path_traversal("../test") == True
    assert is_path_traversal("test/dir") == False

def test_binary_extension():
    assert is_binary_extension(".exe") == True
    assert is_binary_extension(".py") == False

def test_sanitize_filename():
    assert sanitize_filename("test file.txt") == "test_file.txt"
""",
    "tests/test_file_filter.py": """from app.services.repository.file_filter import FileFilter
from pathlib import Path

def test_file_filter():
    f = FileFilter()
    assert f.should_ignore_directory("node_modules") == True
    assert f.should_ignore_directory("src") == False
""",
    "tests/test_github_service.py": """from app.services.repository.github_service import GitHubService

def test_validate_url():
    gh = GitHubService()
    assert gh.validate_url("https://github.com/owner/repo") == True
    assert gh.validate_url("https://gitlab.com/owner/repo") == False

def test_parse_url():
    gh = GitHubService()
    assert gh.parse_url("https://github.com/owner/repo") == ("owner", "repo")
""",
    "tests/test_zip_service.py": """from app.services.repository.zip_service import ZipService
from pathlib import Path

def test_zip_service_instantiation():
    z = ZipService()
    assert z is not None
""",
    "tests/test_api_health.py": """import pytest

@pytest.mark.asyncio
async def test_health(client):
    resp = await client.get("/api/health")
    assert resp.status_code == 200
    assert resp.json()["status"] == "ok"
"""
}

for rel_path, content in files.items():
    p = base_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        f.write(content)

print("Backend files generated.")
