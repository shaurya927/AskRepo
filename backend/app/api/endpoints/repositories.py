"""Repository creation and querying API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.analysis_job import AnalysisJob
from app.models.code_import import CodeImport
from app.models.code_symbol import CodeSymbol
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.repository_stats import RepositoryStats
from app.schemas.common import PaginatedResponse
from app.schemas.repository import RepositoryFileResponse, RepositoryStatsResponse, RepositoryResponse
from app.schemas.symbols import CodeSymbolResponse, CodeImportResponse, RepositoryMetricsResponse
from app.services.repository.analyzer import RepositoryAnalyzer
from app.services.repository.github_service import GitHubService

router = APIRouter()


@router.post("/from-url", response_model=dict)
async def create_repository_from_url(
    url: str = Form(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    """Create a repository analysis from a GitHub URL."""
    settings = get_settings()
    github_svc = GitHubService()
    if not github_svc.validate_url(url):
        raise HTTPException(status_code=400, detail="Invalid GitHub URL. Must be https://github.com/{owner}/{repo}")
    try:
        repo_info = await github_svc.check_repository_exists(url, settings.GITHUB_TOKEN)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    repo_size_kb = repo_info.get("size", 0)
    if repo_size_kb > settings.MAX_REPOSITORY_SIZE_MB * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"Repository is too large ({repo_size_kb // 1024}MB). Maximum is {settings.MAX_REPOSITORY_SIZE_MB}MB.",
        )
    repo = Repository(
        name=repo_info.get("name", url.rstrip("/").split("/")[-1]),
        source="github", url=url,
        description=repo_info.get("description"), status="pending",
    )
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    job = AnalysisJob(repository_id=repo.id, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    analyzer = RepositoryAnalyzer(settings, db)
    background_tasks.add_task(analyzer.analyze, job.id, repo.id, url, None)
    return {"repository_id": str(repo.id), "job_id": str(job.id)}


@router.post("/from-zip", response_model=dict)
async def create_repository_from_zip(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
):
    """Create a repository analysis from an uploaded ZIP file."""
    settings = get_settings()
    if not file.filename or not file.filename.endswith(".zip"):
        raise HTTPException(status_code=400, detail="Only .zip files are accepted")
    if file.size and file.size > settings.MAX_REPOSITORY_SIZE_MB * 1024 * 1024:
        raise HTTPException(
            status_code=400,
            detail=f"File too large. Maximum is {settings.MAX_REPOSITORY_SIZE_MB}MB.",
        )
    repo_name = file.filename.rsplit(".", 1)[0] if file.filename else "uploaded-repo"
    repo = Repository(name=repo_name, source="zip", status="pending")
    db.add(repo)
    await db.commit()
    await db.refresh(repo)
    job = AnalysisJob(repository_id=repo.id, status="queued")
    db.add(job)
    await db.commit()
    await db.refresh(job)
    analyzer = RepositoryAnalyzer(settings, db)
    background_tasks.add_task(analyzer.analyze, job.id, repo.id, None, file)
    return {"repository_id": str(repo.id), "job_id": str(job.id)}


@router.get("/{repo_id}", response_model=RepositoryResponse)
async def get_repository(repo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get repository metadata by ID."""
    result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    return repo


@router.get("/{repo_id}/files", response_model=PaginatedResponse[RepositoryFileResponse])
async def get_repository_files(
    repo_id: uuid.UUID, page: int = 1, size: int = 50,
    language: Optional[str] = None, db: AsyncSession = Depends(get_db),
):
    """List repository files with optional language filtering and pagination."""
    query = select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    if language:
        query = query.where(RepositoryFile.language == language)
    total_query = select(func.count()).select_from(query.subquery())
    total = (await db.execute(total_query)).scalar_one()
    query = query.order_by(RepositoryFile.path).offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/{repo_id}/stats", response_model=RepositoryStatsResponse)
async def get_repository_stats(repo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get repository statistics."""
    result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
    stats = result.scalar_one_or_none()
    if not stats:
        raise HTTPException(status_code=404, detail="Stats not found. Analysis may still be in progress.")
    return stats


# ── Phase 2: Code Intelligence Endpoints ──────────────────────


@router.get("/{repo_id}/symbols", response_model=PaginatedResponse[CodeSymbolResponse])
async def get_repository_symbols(
    repo_id: uuid.UUID,
    page: int = 1,
    size: int = 50,
    symbol_type: Optional[str] = None,
    language: Optional[str] = None,
    search: Optional[str] = None,
    file_path: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """List code symbols with filtering and search."""
    query = select(CodeSymbol).where(CodeSymbol.repository_id == repo_id)
    if symbol_type:
        query = query.where(CodeSymbol.symbol_type == symbol_type)
    if language:
        query = query.where(CodeSymbol.language == language)
    if search:
        query = query.where(CodeSymbol.name.ilike(f"%{search}%"))
    if file_path:
        query = query.where(CodeSymbol.file_path == file_path)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    query = query.order_by(CodeSymbol.file_path, CodeSymbol.start_line).offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/{repo_id}/imports", response_model=PaginatedResponse[CodeImportResponse])
async def get_repository_imports(
    repo_id: uuid.UUID,
    page: int = 1,
    size: int = 100,
    is_internal: Optional[bool] = None,
    db: AsyncSession = Depends(get_db),
):
    """List code imports with optional internal/external filter."""
    query = select(CodeImport).where(CodeImport.repository_id == repo_id)
    if is_internal is not None:
        query = query.where(CodeImport.is_internal == is_internal)

    total = (await db.execute(select(func.count()).select_from(query.subquery()))).scalar_one()
    query = query.order_by(CodeImport.file_path, CodeImport.line).offset((page - 1) * size).limit(size)
    items = (await db.execute(query)).scalars().all()
    return PaginatedResponse(items=items, total=total, page=page, size=size)


@router.get("/{repo_id}/metrics", response_model=RepositoryMetricsResponse)
async def get_repository_metrics(repo_id: uuid.UUID, db: AsyncSession = Depends(get_db)):
    """Get code intelligence metrics."""
    result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
    stats = result.scalar_one_or_none()
    if not stats:
        raise HTTPException(status_code=404, detail="Metrics not found. Analysis may still be in progress.")
    return RepositoryMetricsResponse(
        total_functions=stats.total_functions,
        total_classes=stats.total_classes,
        total_methods=stats.total_methods,
        avg_complexity=stats.avg_complexity,
        max_complexity=stats.max_complexity,
        complexity_distribution=stats.complexity_distribution or {},
        internal_dependencies=stats.internal_dependencies,
        external_dependencies=stats.external_dependencies,
    )
