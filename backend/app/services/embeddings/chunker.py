"""Semantic code chunker — converts parsed symbols into text chunks for embedding."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from app.services.parser.base import ParsedSymbol, ParsedImport


@dataclass
class CodeChunk:
    """A semantic chunk of code with rich metadata for vector search."""
    chunk_id: str
    repo_id: str
    file_path: str
    chunk_type: str  # "function", "class", "method", "documentation", "config"
    symbol_name: str | None = None
    symbol_type: str | None = None
    language: str | None = None
    start_line: int = 0
    end_line: int = 0
    text: str = ""
    metadata: dict = field(default_factory=dict)


class CodeChunker:
    """Creates semantic chunks from parsed symbols and file content."""

    MAX_CHUNK_CHARS = 2000

    def chunk_symbols(
        self,
        symbols: list[ParsedSymbol],
        imports: list[ParsedImport],
        repo_dir: Path,
        repo_id: str,
    ) -> list[CodeChunk]:
        """Create one chunk per symbol, enriched with context."""
        chunks: list[CodeChunk] = []
        # Build per-file import map
        file_imports: dict[str, list[str]] = {}
        for imp in imports:
            file_imports.setdefault(imp.file_path, []).append(imp.source)

        for i, sym in enumerate(symbols):
            # Read the actual source lines for this symbol
            source_code = self._read_source(repo_dir, sym.file_path, sym.start_line, sym.end_line)

            parts: list[str] = []
            parts.append(f"[{sym.language}] {sym.symbol_type} in {sym.file_path}")
            parts.append(f"Name: {sym.name}")
            if sym.class_name:
                parts.append(f"Class: {sym.class_name}")
            if sym.signature:
                parts.append(f"Signature: {sym.signature}")
            if sym.docstring:
                parts.append(f"Docstring: {sym.docstring}")
            file_imps = file_imports.get(sym.file_path, [])
            if file_imps:
                parts.append(f"File imports: {', '.join(file_imps[:20])}")
            if source_code:
                parts.append(f"Code:\n{source_code}")

            text = "\n".join(parts)
            if len(text) > self.MAX_CHUNK_CHARS:
                text = text[: self.MAX_CHUNK_CHARS]

            chunks.append(CodeChunk(
                chunk_id=f"{repo_id}:sym:{i}",
                repo_id=repo_id,
                file_path=sym.file_path,
                chunk_type=sym.symbol_type,
                symbol_name=sym.name,
                symbol_type=sym.symbol_type,
                language=sym.language,
                start_line=sym.start_line,
                end_line=sym.end_line,
                text=text,
                metadata={
                    "class_name": sym.class_name,
                    "complexity": sym.complexity,
                    "decorators": sym.decorators,
                },
            ))
        return chunks

    def chunk_documentation(
        self,
        repo_dir: Path,
        repo_id: str,
        files: list[dict],
    ) -> list[CodeChunk]:
        """Create chunks for documentation and config files."""
        chunks: list[CodeChunk] = []
        doc_files = [
            "README.md", "README.rst", "README.txt", "README",
            "CONTRIBUTING.md", "CHANGELOG.md",
        ]
        config_files = [
            "package.json", "pyproject.toml", "setup.py", "setup.cfg",
            "Cargo.toml", "pom.xml", "build.gradle",
        ]

        all_targets = {f.lower(): ("documentation", f) for f in doc_files}
        all_targets.update({f.lower(): ("config", f) for f in config_files})

        # Also check actual repo files
        for file_info in files:
            fp = file_info["path"]
            basename = Path(fp).name.lower()
            if basename in all_targets:
                chunk_type, _ = all_targets[basename]
                full_path = repo_dir / fp
                try:
                    content = full_path.read_text(encoding="utf-8", errors="replace")
                    if len(content) > self.MAX_CHUNK_CHARS:
                        content = content[: self.MAX_CHUNK_CHARS]
                    chunks.append(CodeChunk(
                        chunk_id=f"{repo_id}:doc:{len(chunks)}",
                        repo_id=repo_id,
                        file_path=fp,
                        chunk_type=chunk_type,
                        text=f"[{chunk_type.upper()}] {fp}\n\n{content}",
                    ))
                except Exception:
                    continue
        return chunks

    def _read_source(self, repo_dir: Path, file_path: str, start: int, end: int) -> str:
        """Read specific lines from a file."""
        try:
            full_path = repo_dir / file_path
            lines = full_path.read_text(encoding="utf-8", errors="replace").splitlines()
            selected = lines[max(0, start - 1): end]
            return "\n".join(selected)
        except Exception:
            return ""
