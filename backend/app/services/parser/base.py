from abc import ABC, abstractmethod
from dataclasses import dataclass, field

@dataclass
class ParsedSymbol:
    name: str
    symbol_type: str
    language: str
    file_path: str
    start_line: int
    end_line: int
    class_name: str | None = None
    docstring: str | None = None
    signature: str | None = None
    decorators: list[str] = field(default_factory=list)
    imports: list[str] = field(default_factory=list)
    complexity: int = 1

@dataclass
class ParsedImport:
    source: str
    names: list[str]
    is_relative: bool
    file_path: str
    line: int

@dataclass 
class FileParseResult:
    symbols: list[ParsedSymbol] = field(default_factory=list)
    imports: list[ParsedImport] = field(default_factory=list)
    exports: list[str] = field(default_factory=list)

class LanguageParser(ABC):
    @abstractmethod
    def parse_file(self, content: str, file_path: str) -> FileParseResult:
        ...
    
    @abstractmethod
    def supported_extensions(self) -> list[str]:
        ...
