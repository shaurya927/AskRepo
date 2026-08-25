"""Repository analysis orchestrator — coordinates cloning, scanning, parsing, and statistics."""

import shutil
import uuid
from datetime import datetime, timezone
from pathlib import Path

from fastapi import UploadFile
from sqlalchemy import update
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.analysis_job import AnalysisJob
from app.models.code_import import CodeImport
from app.models.code_symbol import CodeSymbol
from app.models.repository import Repository
from app.models.repository_file import RepositoryFile
from app.models.repository_stats import RepositoryStats
from app.services.repository.file_filter import FileFilter
from app.services.repository.file_scanner import FileScanner
from app.services.repository.github_service import GitHubService
from app.services.repository.zip_service import ZipService


class RepositoryAnalyzer:
    """Orchestrates the full analysis pipeline (Phase 1 + Phase 2).

    Steps:
      1. Clone (GitHub) or extract (ZIP) the repository
      2. Scan files
      3. Detect frameworks & package managers
      4. Parse code with Tree-sitter (Phase 2)
      5. Resolve dependencies (Phase 2)
      6. Compute metrics (Phase 2)
      7. Persist all records
      8. Clean up temp directory
    """

    def __init__(self, settings, db: AsyncSession):
        self.settings = settings
        self.db = db

    async def _update_job(
        self,
        job_id: uuid.UUID,
        status: str,
        progress: str | None = None,
        error: str | None = None,
    ):
        """Update an AnalysisJob's status and progress."""
        values: dict = {
            "status": status,
            "progress_detail": progress,
            "error_message": error,
            "updated_at": datetime.now(timezone.utc),
        }
        if status in ("cloning", "extracting"):
            values["started_at"] = datetime.now(timezone.utc)
        if status in ("completed", "failed"):
            values["completed_at"] = datetime.now(timezone.utc)

        stmt = update(AnalysisJob).where(AnalysisJob.id == job_id).values(**values)
        await self.db.execute(stmt)
        await self.db.commit()

    async def _update_repo(
        self,
        repo_id: uuid.UUID,
        status: str,
        error: str | None = None,
    ):
        """Update a Repository's status."""
        stmt = (
            update(Repository)
            .where(Repository.id == repo_id)
            .values(
                status=status,
                error_message=error,
                updated_at=datetime.now(timezone.utc),
            )
        )
        await self.db.execute(stmt)
        await self.db.commit()

    async def analyze(
        self,
        job_id: uuid.UUID,
        repo_id: uuid.UUID,
        url: str | None,
        file: UploadFile | None,
    ):
        """Run the full analysis pipeline."""
        target_dir = Path(self.settings.TEMP_REPOSITORY_PATH) / str(job_id)
        repo_dir = target_dir

        try:
            target_dir.mkdir(parents=True, exist_ok=True)

            # ── Step 1: Clone or extract ─────────────────────────
            if url:
                await self._update_job(job_id, "cloning", "Cloning repository from GitHub...")
                await self._update_repo(repo_id, "analyzing")
                github_svc = GitHubService()
                clone_dir = target_dir / "repo"
                github_svc.clone_repository(url, clone_dir)
                repo_dir = clone_dir
            elif file:
                await self._update_job(job_id, "extracting", "Extracting ZIP archive...")
                await self._update_repo(repo_id, "analyzing")
                zip_svc = ZipService()
                zip_path = await zip_svc.save_upload(file, target_dir)
                extract_dir = target_dir / "extracted"
                extract_dir.mkdir(exist_ok=True)
                zip_svc.extract_zip(
                    zip_path, extract_dir,
                    self.settings.MAX_REPOSITORY_SIZE_MB,
                    self.settings.MAX_FILE_COUNT,
                )
                repo_dir = extract_dir
                contents = list(extract_dir.iterdir())
                if len(contents) == 1 and contents[0].is_dir():
                    repo_dir = contents[0]
            else:
                raise ValueError("No URL or file provided for analysis")

            # ── Step 2: Scan files ───────────────────────────────
            await self._update_job(job_id, "scanning", "Scanning repository files...")
            scanner = FileScanner()
            file_filter = FileFilter()
            max_file_bytes = self.settings.MAX_FILE_SIZE_MB * 1024 * 1024
            scan_result = scanner.scan_repository(repo_dir, file_filter, max_file_bytes)

            # ── Step 3: Detect frameworks & package managers ─────
            await self._update_job(job_id, "analyzing", "Detecting frameworks...")
            frameworks = scanner.detect_frameworks(repo_dir, scan_result.files)
            package_managers = scanner.detect_package_managers(repo_dir)

            # ── Step 4: Parse code with Tree-sitter (Phase 2) ────
            await self._update_job(job_id, "parsing", "Parsing code symbols...")
            from app.services.analysis.code_parser import CodeParserService
            from app.services.analysis.dependency_resolver import DependencyResolver
            from app.services.analysis.metrics import MetricsCalculator

            code_parser = CodeParserService()
            parse_result = code_parser.parse_repository(repo_dir, scan_result.files)

            # ── Step 5: Resolve dependencies ─────────────────────
            await self._update_job(job_id, "parsing", "Resolving dependencies...")
            file_paths = {f["path"] for f in scan_result.files}
            dep_resolver = DependencyResolver()
            resolved_imports = dep_resolver.resolve(parse_result.imports, file_paths, repo_dir)

            # ── Step 6: Compute metrics ──────────────────────────
            metrics_calc = MetricsCalculator()
            metrics = metrics_calc.compute(parse_result.symbols, parse_result.imports, resolved_imports)

            # ── Step 7: Persist file records ─────────────────────
            await self._update_job(job_id, "analyzing", "Saving file metadata...")
            for f in scan_result.files:
                repo_file = RepositoryFile(repository_id=repo_id, **f)
                self.db.add(repo_file)
            await self.db.flush()

            # ── Step 8: Persist code symbols ─────────────────────
            await self._update_job(job_id, "analyzing", "Saving code symbols...")
            for sym in parse_result.symbols:
                db_symbol = CodeSymbol(
                    repository_id=repo_id,
                    file_path=sym.file_path,
                    name=sym.name,
                    symbol_type=sym.symbol_type,
                    language=sym.language,
                    start_line=sym.start_line,
                    end_line=sym.end_line,
                    class_name=sym.class_name,
                    signature=sym.signature,
                    docstring=(sym.docstring[:500] if sym.docstring else None),
                    decorators=sym.decorators,
                    complexity=sym.complexity,
                )
                self.db.add(db_symbol)

            # ── Step 9: Persist resolved imports ─────────────────
            for imp in resolved_imports:
                db_import = CodeImport(
                    repository_id=repo_id,
                    file_path=imp.file_path,
                    source=imp.source,
                    names=imp.names,
                    is_relative=imp.is_relative,
                    resolved_path=imp.resolved_path,
                    is_internal=imp.is_internal,
                    line=imp.line,
                )
                self.db.add(db_import)
            await self.db.flush()

            # ── Step 10: Persist stats record ────────────────────
            languages = scan_result.stats.get("languages", {})
            primary_lang = None
            if languages:
                primary_lang = max(languages.items(), key=lambda x: x[1]["bytes"])[0]

            repo_stats = RepositoryStats(
                repository_id=repo_id,
                total_files=scan_result.stats["total_files"],
                total_directories=scan_result.stats["total_directories"],
                total_lines=scan_result.stats["total_lines"],
                total_size=scan_result.stats["total_size"],
                languages=languages,
                primary_language=primary_lang,
                frameworks=frameworks,
                package_managers=package_managers,
                entry_points=scan_result.stats.get("entry_points", []),
                config_files=scan_result.stats.get("config_files", []),
                test_files_count=scan_result.stats.get("test_files_count", 0),
                # Phase 2 metrics
                total_functions=metrics.total_functions,
                total_classes=metrics.total_classes,
                total_methods=metrics.total_methods,
                avg_complexity=round(metrics.avg_complexity, 2),
                max_complexity=metrics.max_complexity,
                complexity_distribution=metrics.complexity_distribution,
                internal_dependencies=metrics.internal_dependencies,
                external_dependencies=metrics.external_dependencies,
            )
            self.db.add(repo_stats)
            await self.db.commit()

            # ── Step 11: Mark as completed ───────────────────────
            await self._update_job(job_id, "completed", "Analysis complete")
            await self._update_repo(repo_id, "completed")

        except Exception as e:
            error_msg = str(e)[:500]
            await self._update_job(job_id, "failed", error=error_msg)
            await self._update_repo(repo_id, "failed", error=error_msg)

        finally:
            if target_dir.exists():
                shutil.rmtree(target_dir, ignore_errors=True)
