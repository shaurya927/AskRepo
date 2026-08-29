"""Repository creation and querying API endpoints."""

import uuid
from typing import Optional

from fastapi import APIRouter, BackgroundTasks, Depends, File, Form, HTTPException, UploadFile, Header
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import get_settings
from app.core.database import get_db
from app.models.analysis_job import AnalysisJob
from app.models.chat_message import ChatMessage
from app.models.code_import import CodeImport
from app.models.code_symbol import CodeSymbol
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.repository_stats import RepositoryStats
from app.schemas.chat import (
    ChatRequest, ChatResponse, ChatHistoryResponse,
    ChatMessageResponse, SourceReference,
)
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
    x_byok_key: str | None = Header(None, alias="X-BYOK-Key"),
):
    """Create a repository analysis from a GitHub URL."""
    settings = get_settings()
    
    # Test API Key limit
    from app.services.embeddings.embedding_service import get_embedding_service
    import asyncio
    
    embed_svc = get_embedding_service(settings.EMBEDDING_MODEL, byok_key=x_byok_key)
    try:
        await asyncio.to_thread(embed_svc.embed_query, "test")
    except Exception as e:
        err_str = str(e)
        if "429" in err_str or "Resource has been exhausted" in err_str:
            raise HTTPException(
                status_code=429, 
                detail="Server AI API Key quota is fully exhausted. It will reset in approx 24 hours. Please click the Settings gear to add your own Gemini API Key."
            )
        elif "400" in err_str or "API_KEY_INVALID" in err_str:
            raise HTTPException(
                status_code=400,
                detail="The provided Gemini API Key is invalid."
            )
        else:
            raise HTTPException(
                status_code=500,
                detail=f"AI API Test Failed: {err_str}"
            )
            
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
    background_tasks.add_task(analyzer.analyze, job.id, repo.id, url, None, x_byok_key)
    return {"repository_id": str(repo.id), "job_id": str(job.id)}


@router.post("/from-zip", response_model=dict)
async def create_repository_from_zip(
    file: UploadFile = File(...),
    background_tasks: BackgroundTasks = BackgroundTasks(),
    db: AsyncSession = Depends(get_db),
    x_byok_key: str | None = Header(None, alias="X-BYOK-Key"),
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
    background_tasks.add_task(analyzer.analyze, job.id, repo.id, None, file, x_byok_key)
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


# ── Phase 3: AI Chat Endpoints ────────────────────────────────


@router.post("/{repo_id}/chat")
async def chat_with_repository(
    repo_id: uuid.UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Send a question about a repository and get a RAG-powered answer."""
    import logging
    logger = logging.getLogger(__name__)

    # Verify repo exists and is analyzed
    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "completed":
        raise HTTPException(status_code=400, detail="Repository analysis is not complete yet.")

    # Get repo stats for context
    stats_result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
    stats = stats_result.scalar_one_or_none()
    repo_stats = {}
    if stats:
        repo_stats = {
            "name": repo.name,
            "primary_language": stats.primary_language,
            "total_files": stats.total_files,
            "total_lines": stats.total_lines,
            "frameworks": stats.frameworks or [],
            "package_managers": stats.package_managers or [],
            "total_functions": stats.total_functions,
            "total_classes": stats.total_classes,
            "total_methods": stats.total_methods,
        }

    # Load FAISS index
    from pathlib import Path
    from app.services.embeddings.embedding_service import get_embedding_service
    from app.services.embeddings.vector_store import FAISSVectorStore
    from app.services.ai.gateway import AIGateway
    from app.services.rag.engine import RAGEngine

    settings = get_settings()
    index_dir = Path(settings.VECTOR_INDEX_PATH) / str(repo_id)
    store = FAISSVectorStore()
    if not store.load(index_dir):
        raise HTTPException(status_code=400, detail="Search index not found. Re-analyze the repository.")

    embed_svc = get_embedding_service(model_name=settings.EMBEDDING_MODEL)
    ai_gateway = AIGateway(settings)
    rag_engine = RAGEngine(ai_gateway, embed_svc, store, settings)

    try:
        response = await rag_engine.query(
            question=request.message,
            repo_stats=repo_stats,
            byok_key=request.api_key,
            repo_id=repo_id,
            db=db,
        )
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error("RAG query failed: %s", e)
        raise HTTPException(status_code=500, detail="AI query failed. Please try again.")

    # Persist messages
    user_msg = ChatMessage(
        repository_id=repo_id,
        role="user",
        content=request.message,
    )
    db.add(user_msg)

    sources_list = [
        {"file_path": s.file_path, "start_line": s.start_line, "end_line": s.end_line, "symbol_name": s.symbol_name}
        for s in response.sources
    ]
    assistant_msg = ChatMessage(
        repository_id=repo_id,
        role="assistant",
        content=response.answer,
        sources=sources_list,
        query_category=response.query_category,
        model_used=response.model_used,
    )
    db.add(assistant_msg)
    await db.commit()
    await db.refresh(assistant_msg)

    return ChatResponse(
        id=assistant_msg.id,
        message=response.answer,
        sources=[SourceReference(**s) for s in sources_list],
        query_category=response.query_category,
        model_used=response.model_used,
    )


@router.get("/{repo_id}/chat/history")
async def get_chat_history(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get chat conversation history for a repository."""
    result = await db.execute(
        select(ChatMessage)
        .where(ChatMessage.repository_id == repo_id)
        .order_by(ChatMessage.created_at.asc())
    )
    messages = result.scalars().all()
    return ChatHistoryResponse(
        messages=[
            ChatMessageResponse(
                id=m.id,
                role=m.role,
                content=m.content,
                sources=[SourceReference(**s) for s in (m.sources or [])],
                query_category=m.query_category,
                model_used=m.model_used,
                created_at=m.created_at,
            )
            for m in messages
        ]
    )


@router.post("/{repo_id}/chat/stream")
async def chat_stream_with_repository(
    repo_id: uuid.UUID,
    request: ChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """Stream a RAG-powered answer via Server-Sent Events."""
    import json
    from fastapi.responses import StreamingResponse

    # Verify repo
    repo_result = await db.execute(select(Repository).where(Repository.id == repo_id))
    repo = repo_result.scalar_one_or_none()
    if not repo:
        raise HTTPException(status_code=404, detail="Repository not found")
    if repo.status != "completed":
        raise HTTPException(status_code=400, detail="Repository analysis is not complete yet.")

    # Get stats
    stats_result = await db.execute(select(RepositoryStats).where(RepositoryStats.repository_id == repo_id))
    stats = stats_result.scalar_one_or_none()
    repo_stats = {}
    if stats:
        repo_stats = {
            "name": repo.name,
            "primary_language": stats.primary_language,
            "total_files": stats.total_files,
            "total_lines": stats.total_lines,
            "frameworks": stats.frameworks or [],
            "package_managers": stats.package_managers or [],
            "total_functions": stats.total_functions,
            "total_classes": stats.total_classes,
            "total_methods": stats.total_methods,
        }

    # Load index
    from pathlib import Path
    from app.services.embeddings.embedding_service import get_embedding_service
    from app.services.embeddings.vector_store import FAISSVectorStore
    from app.services.ai.gateway import AIGateway
    from app.services.rag.engine import RAGEngine

    settings = get_settings()
    index_dir = Path(settings.VECTOR_INDEX_PATH) / str(repo_id)
    store = FAISSVectorStore()
    if not store.load(index_dir):
        raise HTTPException(status_code=400, detail="Search index not found.")

    embed_svc = get_embedding_service(model_name=settings.EMBEDDING_MODEL)
    ai_gateway = AIGateway(settings)
    rag_engine = RAGEngine(ai_gateway, embed_svc, store, settings)

    async def generate():
        try:
            stream, category, sources = await rag_engine.query_stream(
                question=request.message,
                repo_stats=repo_stats,
                byok_key=request.api_key,
                repo_id=repo_id,
                db=db,
            )

            # Send category event
            yield f"data: {json.dumps({'type': 'category', 'data': category})}\n\n"

            # Stream text chunks
            full_answer = []
            async for chunk in stream:
                full_answer.append(chunk)
                yield f"data: {json.dumps({'type': 'text', 'data': chunk})}\n\n"

            # Send sources at the end
            sources_list = [
                {"file_path": s.file_path, "start_line": s.start_line, "end_line": s.end_line, "symbol_name": s.symbol_name}
                for s in sources
            ]
            yield f"data: {json.dumps({'type': 'sources', 'data': sources_list})}\n\n"
            yield f"data: {json.dumps({'type': 'done'})}\n\n"

        except Exception as e:
            yield f"data: {json.dumps({'type': 'error', 'data': str(e)})}\n\n"

    return StreamingResponse(generate(), media_type="text/event-stream")


# ── Phase 4: Graph & Architecture Endpoints ────────────────────


@router.get("/{repo_id}/graph")
async def get_repository_graph(
    repo_id: uuid.UUID,
    level: str = "file",
    language: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get the dependency graph in React Flow format.

    Args:
        level: 'file' or 'module'
        language: Optional language filter
    """
    from app.services.graph.graph_builder import GraphBuilder

    # Fetch symbols and imports
    sym_query = select(CodeSymbol).where(CodeSymbol.repository_id == repo_id)
    imp_query = select(CodeImport).where(CodeImport.repository_id == repo_id)
    if language:
        sym_query = sym_query.where(CodeSymbol.language == language)

    sym_result = await db.execute(sym_query)
    imp_result = await db.execute(imp_query)
    symbols = [
        {"file_path": s.file_path, "name": s.name, "symbol_type": s.symbol_type,
         "language": s.language, "start_line": s.start_line, "end_line": s.end_line,
         "complexity": s.complexity}
        for s in sym_result.scalars().all()
    ]
    imports = [
        {"file_path": i.file_path, "source": i.source, "resolved_path": i.resolved_path,
         "is_internal": i.is_internal}
        for i in imp_result.scalars().all()
    ]

    builder = GraphBuilder()
    file_graph = builder.build_file_graph(symbols, imports)

    if level == "module":
        graph = builder.build_module_graph(file_graph)
    else:
        graph = file_graph

    return builder.to_react_flow(graph)


@router.get("/{repo_id}/graph/node/{node_id:path}")
async def get_graph_node_detail(
    repo_id: uuid.UUID,
    node_id: str,
    db: AsyncSession = Depends(get_db),
):
    """Get detailed info about a specific graph node."""
    from app.services.graph.graph_builder import GraphBuilder
    from app.services.graph.architecture_detector import ArchitectureDetector

    sym_result = await db.execute(
        select(CodeSymbol).where(CodeSymbol.repository_id == repo_id)
    )
    imp_result = await db.execute(
        select(CodeImport).where(CodeImport.repository_id == repo_id)
    )
    file_result = await db.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    )

    symbols = [
        {"file_path": s.file_path, "name": s.name, "symbol_type": s.symbol_type,
         "language": s.language, "start_line": s.start_line, "end_line": s.end_line,
         "complexity": s.complexity}
        for s in sym_result.scalars().all()
    ]
    imports = [
        {"file_path": i.file_path, "source": i.source, "resolved_path": i.resolved_path,
         "is_internal": i.is_internal}
        for i in imp_result.scalars().all()
    ]
    files = [
        {"path": f.path, "language": f.language}
        for f in file_result.scalars().all()
    ]

    builder = GraphBuilder()
    file_graph = builder.build_file_graph(symbols, imports, files)

    detector = ArchitectureDetector()
    arch = detector.detect(files, symbols, imports)

    detail = builder.get_node_detail(file_graph, node_id, symbols, arch)
    return {
        "node_id": detail.node_id,
        "node_type": detail.node_type,
        "label": detail.label,
        "language": detail.language,
        "category": detail.category,
        "dependencies": detail.dependencies,
        "dependents": detail.dependents,
        "symbols": detail.symbols,
        "symbol_count": detail.symbol_count,
    }


@router.get("/{repo_id}/architecture")
async def get_repository_architecture(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get architecture detection results."""
    from app.services.graph.architecture_detector import ArchitectureDetector

    file_result = await db.execute(
        select(RepositoryFile).where(RepositoryFile.repository_id == repo_id)
    )
    sym_result = await db.execute(
        select(CodeSymbol).where(CodeSymbol.repository_id == repo_id)
    )
    imp_result = await db.execute(
        select(CodeImport).where(CodeImport.repository_id == repo_id)
    )

    files = [{"path": f.path, "language": f.language} for f in file_result.scalars().all()]
    symbols = [
        {"file_path": s.file_path, "name": s.name, "symbol_type": s.symbol_type, "language": s.language}
        for s in sym_result.scalars().all()
    ]
    imports = [
        {"file_path": i.file_path, "source": i.source, "is_internal": i.is_internal}
        for i in imp_result.scalars().all()
    ]

    detector = ArchitectureDetector()
    detection = detector.detect(files, symbols, imports)
    summary = detector.get_architecture_summary(detection)

    return {
        "categories": detection,
        "summary": summary,
    }


# ── Phase 5: Git History Endpoints ──────────────────────────


@router.get("/{repo_id}/commits")
async def get_repository_commits(
    repo_id: uuid.UUID,
    page: int = 1,
    per_page: int = 50,
    file_path: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    """Get paginated commit list for a repository."""
    from app.models.commit import Commit as CommitModel
    from app.models.file_change import FileChange as FileChangeModel

    offset = (page - 1) * per_page
    per_page = min(per_page, 200)

    if file_path:
        # Get commits that touched this file
        fc_query = select(FileChangeModel.commit_sha).where(
            FileChangeModel.repository_id == repo_id,
            FileChangeModel.file_path == file_path,
        ).distinct()
        fc_result = await db.execute(fc_query)
        shas = [r[0] for r in fc_result.fetchall()]

        if not shas:
            return {"commits": [], "total": 0, "page": page, "per_page": per_page}

        query = (
            select(CommitModel)
            .where(CommitModel.repository_id == repo_id, CommitModel.sha.in_(shas))
            .order_by(CommitModel.authored_date.desc())
            .offset(offset)
            .limit(per_page)
        )
        count_query = select(func.count()).select_from(CommitModel).where(
            CommitModel.repository_id == repo_id, CommitModel.sha.in_(shas)
        )
    else:
        query = (
            select(CommitModel)
            .where(CommitModel.repository_id == repo_id)
            .order_by(CommitModel.authored_date.desc())
            .offset(offset)
            .limit(per_page)
        )
        count_query = select(func.count()).select_from(CommitModel).where(
            CommitModel.repository_id == repo_id
        )

    result = await db.execute(query)
    commits = result.scalars().all()
    total_result = await db.execute(count_query)
    total = total_result.scalar() or 0

    return {
        "commits": [
            {
                "id": str(c.id),
                "sha": c.sha,
                "message": c.message,
                "author_name": c.author_name,
                "author_email": c.author_email,
                "authored_date": c.authored_date.isoformat(),
                "committed_date": c.committed_date.isoformat(),
                "files_changed": c.files_changed,
                "insertions": c.insertions,
                "deletions": c.deletions,
            }
            for c in commits
        ],
        "total": total,
        "page": page,
        "per_page": per_page,
    }


@router.get("/{repo_id}/commits/{sha}")
async def get_commit_detail(
    repo_id: uuid.UUID,
    sha: str,
    db: AsyncSession = Depends(get_db),
):
    """Get a single commit with its file changes."""
    from app.models.commit import Commit as CommitModel
    from app.models.file_change import FileChange as FileChangeModel

    result = await db.execute(
        select(CommitModel).where(
            CommitModel.repository_id == repo_id, CommitModel.sha == sha
        )
    )
    commit = result.scalars().first()
    if not commit:
        raise HTTPException(status_code=404, detail="Commit not found")

    fc_result = await db.execute(
        select(FileChangeModel).where(
            FileChangeModel.repository_id == repo_id,
            FileChangeModel.commit_sha == sha,
        )
    )
    file_changes = fc_result.scalars().all()

    return {
        "id": str(commit.id),
        "sha": commit.sha,
        "message": commit.message,
        "author_name": commit.author_name,
        "author_email": commit.author_email,
        "authored_date": commit.authored_date.isoformat(),
        "committed_date": commit.committed_date.isoformat(),
        "files_changed": commit.files_changed,
        "insertions": commit.insertions,
        "deletions": commit.deletions,
        "file_changes": [
            {
                "file_path": fc.file_path,
                "change_type": fc.change_type,
                "insertions": fc.insertions,
                "deletions": fc.deletions,
                "patch": fc.patch,
            }
            for fc in file_changes
        ],
    }


@router.get("/{repo_id}/history/hotspots")
async def get_history_hotspots(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get files ranked by change frequency."""
    from app.models.file_change import FileChange as FileChangeModel
    from app.services.git.git_analyzer import GitAnalyzer

    result = await db.execute(
        select(FileChangeModel).where(FileChangeModel.repository_id == repo_id)
    )
    file_changes = [
        {"file_path": fc.file_path, "insertions": fc.insertions, "deletions": fc.deletions}
        for fc in result.scalars().all()
    ]

    hotspots = GitAnalyzer.get_change_frequency(file_changes)
    return {"hotspots": hotspots[:50]}


@router.get("/{repo_id}/history/timeline")
async def get_history_timeline(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get commit activity grouped by week."""
    from app.models.commit import Commit as CommitModel
    from app.services.git.git_analyzer import GitAnalyzer

    result = await db.execute(
        select(CommitModel).where(CommitModel.repository_id == repo_id)
    )
    commits = [
        {
            "authored_date": c.authored_date,
            "insertions": c.insertions,
            "deletions": c.deletions,
        }
        for c in result.scalars().all()
    ]

    timeline = GitAnalyzer.get_commit_timeline(commits)
    return {"timeline": timeline}


@router.get("/{repo_id}/history/co-changes")
async def get_history_co_changes(
    repo_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
):
    """Get files that frequently change together."""
    from app.models.file_change import FileChange as FileChangeModel
    from app.services.git.git_analyzer import GitAnalyzer

    result = await db.execute(
        select(FileChangeModel).where(FileChangeModel.repository_id == repo_id)
    )
    file_changes = [
        {"commit_sha": fc.commit_sha, "file_path": fc.file_path}
        for fc in result.scalars().all()
    ]

    co_changes = GitAnalyzer.get_co_change_pairs(file_changes)
    return {"co_changes": co_changes}
