from pathlib import Path
from app.services.parser.base import LanguageParser
from app.services.parser.python_parser import PythonParser
from app.services.parser.javascript_parser import JavaScriptParser
from app.services.parser.java_parser import JavaParser
from app.services.parser.cpp_parser import CppParser

class ParserRegistry:
    def __init__(self):
        self._parsers: dict[str, LanguageParser] = {}
        self._extension_map: dict[str, str] = {}
        self._register_defaults()
    
    def _register_defaults(self):
        parsers = {
            "Python": PythonParser(),
            "JavaScript": JavaScriptParser(),
            "Java": JavaParser(),
            "C++": CppParser()
        }
        
        for name, parser in parsers.items():
            self._parsers[name] = parser
            for ext in parser.supported_extensions():
                self._extension_map[ext] = name
                
    def get_parser_for_file(self, file_path: str) -> LanguageParser | None:
        ext = Path(file_path).suffix.lower()
        lang = self._extension_map.get(ext)
        if lang:
            return self._parsers.get(lang)
        return None
        
    def supported_languages(self) -> list[str]:
        return list(self._parsers.keys())
