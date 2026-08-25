from pathlib import Path
from dataclasses import dataclass
from app.services.parser.base import ParsedSymbol, ParsedImport
from app.services.parser.registry import ParserRegistry

@dataclass
class RepositoryParseResult:
    symbols: list[ParsedSymbol]
    imports: list[ParsedImport]
    exports: dict[str, list[str]]

class CodeParserService:
    def __init__(self):
        self.registry = ParserRegistry()
    
    def parse_repository(self, repo_dir: Path, files: list[dict]) -> RepositoryParseResult:
        all_symbols = []
        all_imports = []
        all_exports = {}
        
        for file_info in files:
            file_path = file_info['path']
            parser = self.registry.get_parser_for_file(file_path)
            if not parser:
                continue
            
            full_path = repo_dir / file_path
            try:
                content = full_path.read_text(encoding='utf-8', errors='replace')
                result = parser.parse_file(content, file_path)
                all_symbols.extend(result.symbols)
                all_imports.extend(result.imports)
                if result.exports:
                    all_exports[file_path] = result.exports
            except Exception:
                continue
        
        return RepositoryParseResult(symbols=all_symbols, imports=all_imports, exports=all_exports)
