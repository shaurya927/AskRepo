"""Tests for the semantic code chunker."""

import pytest
from pathlib import Path
from unittest.mock import MagicMock

from app.services.embeddings.chunker import CodeChunker, CodeChunk
from app.services.parser.base import ParsedSymbol, ParsedImport


class TestCodeChunker:

    def setup_method(self):
        self.chunker = CodeChunker()

    def test_chunks_symbol(self, tmp_path):
        # Create a temp file
        src = tmp_path / "main.py"
        src.write_text("def hello():\n    return 'world'\n")

        symbols = [ParsedSymbol(
            name="hello", symbol_type="function", language="Python",
            file_path="main.py", start_line=1, end_line=2,
            signature="def hello()", complexity=1,
        )]
        imports = []

        chunks = self.chunker.chunk_symbols(symbols, imports, tmp_path, "repo-1")
        assert len(chunks) == 1
        assert chunks[0].symbol_name == "hello"
        assert chunks[0].chunk_type == "function"
        assert "def hello()" in chunks[0].text
        assert chunks[0].file_path == "main.py"

    def test_chunk_includes_imports(self, tmp_path):
        src = tmp_path / "app.py"
        src.write_text("import os\ndef run():\n    pass\n")

        symbols = [ParsedSymbol(
            name="run", symbol_type="function", language="Python",
            file_path="app.py", start_line=2, end_line=3, complexity=1,
        )]
        imports = [ParsedImport(source="os", names=["os"], is_relative=False, file_path="app.py", line=1)]

        chunks = self.chunker.chunk_symbols(symbols, imports, tmp_path, "repo-1")
        assert "File imports: os" in chunks[0].text

    def test_truncates_long_chunks(self, tmp_path):
        src = tmp_path / "big.py"
        src.write_text("x = 1\n" * 1000)

        symbols = [ParsedSymbol(
            name="big", symbol_type="function", language="Python",
            file_path="big.py", start_line=1, end_line=1000, complexity=1,
        )]

        chunks = self.chunker.chunk_symbols(symbols, [], tmp_path, "repo-1")
        assert len(chunks[0].text) <= CodeChunker.MAX_CHUNK_CHARS

    def test_chunk_documentation(self, tmp_path):
        readme = tmp_path / "README.md"
        readme.write_text("# My Project\nThis is a test.")

        files = [{"path": "README.md"}]
        chunks = self.chunker.chunk_documentation(tmp_path, "repo-1", files)
        assert len(chunks) == 1
        assert chunks[0].chunk_type == "documentation"
        assert "My Project" in chunks[0].text

    def test_no_doc_chunks_without_matching_files(self, tmp_path):
        files = [{"path": "src/main.py"}]
        chunks = self.chunker.chunk_documentation(tmp_path, "repo-1", files)
        assert len(chunks) == 0

    def test_chunk_metadata(self, tmp_path):
        src = tmp_path / "util.py"
        src.write_text("class Helper:\n    pass\n")

        symbols = [ParsedSymbol(
            name="Helper", symbol_type="class", language="Python",
            file_path="util.py", start_line=1, end_line=2,
            complexity=1, decorators=["@dataclass"],
        )]

        chunks = self.chunker.chunk_symbols(symbols, [], tmp_path, "repo-1")
        assert chunks[0].metadata["decorators"] == ["@dataclass"]
        assert chunks[0].metadata["complexity"] == 1
