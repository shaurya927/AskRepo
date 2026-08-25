import os
from pathlib import Path

backend_dir = Path(r"d:\Users\imsha\Documents\Projects\AskRepo\backend")

def create_file(rel_path, content):
    p = backend_dir / rel_path
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(content.strip() + "\n", encoding="utf-8")

# __init__.py files
create_file("app/services/parser/__init__.py", "")
create_file("app/services/analysis/__init__.py", "")

# base.py
create_file("app/services/parser/base.py", """
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
""")

create_file("app/services/parser/python_parser.py", """
from tree_sitter_language_pack import get_parser
from app.services.parser.base import LanguageParser, FileParseResult, ParsedSymbol, ParsedImport

class PythonParser(LanguageParser):
    def __init__(self):
        self.parser = get_parser('python')

    def supported_extensions(self) -> list[str]:
        return [".py"]

    def parse_file(self, content: str, file_path: str) -> FileParseResult:
        result = FileParseResult()
        tree = self.parser.parse(content.encode('utf-8'))
        
        def walk(node, parent_class=None):
            if node.type == 'function_definition' or node.type == 'decorated_definition':
                is_decorated = node.type == 'decorated_definition'
                target_node = node
                decorators = []
                
                if is_decorated:
                    for child in node.children:
                        if child.type == 'decorator':
                            decorators.append(child.text.decode('utf-8').lstrip('@'))
                        elif child.type == 'function_definition' or child.type == 'class_definition':
                            target_node = child
                            break
                            
                if target_node.type == 'function_definition':
                    name_node = target_node.child_by_field_name('name')
                    params_node = target_node.child_by_field_name('parameters')
                    return_type_node = target_node.child_by_field_name('return_type')
                    
                    if name_node:
                        name = name_node.text.decode('utf-8')
                        params = params_node.text.decode('utf-8') if params_node else "()"
                        ret = f" -> {return_type_node.text.decode('utf-8')}" if return_type_node else ""
                        sig = f"def {name}{params}{ret}"
                        
                        body_node = target_node.child_by_field_name('body')
                        docstring = None
                        complexity = 1
                        
                        if body_node:
                            # docstring
                            if len(body_node.children) > 0:
                                first_stmt = body_node.children[0]
                                if first_stmt.type == 'expression_statement':
                                    expr = first_stmt.children[0]
                                    if expr.type == 'string':
                                        docstring = expr.text.decode('utf-8').strip('\"\\'')
                            
                            # complexity
                            def count_complexity(n):
                                c = 0
                                if n.type in ['if_statement', 'elif_clause', 'for_statement', 'while_statement', 'except_clause', 'with_statement', 'boolean_operator', 'conditional_expression', 'assert_statement']:
                                    c += 1
                                for child in n.children:
                                    c += count_complexity(child)
                                return c
                            complexity = 1 + count_complexity(body_node)
                        
                        sym_type = "method" if parent_class else "function"
                        
                        result.symbols.append(ParsedSymbol(
                            name=name,
                            symbol_type=sym_type,
                            language="Python",
                            file_path=file_path,
                            start_line=target_node.start_point[0] + 1,
                            end_line=target_node.end_point[0] + 1,
                            class_name=parent_class,
                            docstring=docstring[:500] if docstring else None,
                            signature=sig,
                            decorators=decorators,
                            complexity=complexity
                        ))
                
                elif target_node.type == 'class_definition':
                    name_node = target_node.child_by_field_name('name')
                    if name_node:
                        name = name_node.text.decode('utf-8')
                        
                        body_node = target_node.child_by_field_name('body')
                        docstring = None
                        if body_node and len(body_node.children) > 0:
                            first_stmt = body_node.children[0]
                            if first_stmt.type == 'expression_statement':
                                expr = first_stmt.children[0]
                                if expr.type == 'string':
                                    docstring = expr.text.decode('utf-8').strip('\"\\'')
                        
                        result.symbols.append(ParsedSymbol(
                            name=name,
                            symbol_type="class",
                            language="Python",
                            file_path=file_path,
                            start_line=target_node.start_point[0] + 1,
                            end_line=target_node.end_point[0] + 1,
                            docstring=docstring[:500] if docstring else None,
                            decorators=decorators
                        ))
                        
                        if body_node:
                            for child in body_node.children:
                                walk(child, parent_class=name)

            elif node.type == 'class_definition':
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8')
                    body_node = node.child_by_field_name('body')
                    docstring = None
                    if body_node and len(body_node.children) > 0:
                        first_stmt = body_node.children[0]
                        if first_stmt.type == 'expression_statement':
                            expr = first_stmt.children[0]
                            if expr.type == 'string':
                                docstring = expr.text.decode('utf-8').strip('\"\\'')
                    
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type="class",
                        language="Python",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        docstring=docstring[:500] if docstring else None
                    ))
                    
                    if body_node:
                        for child in body_node.children:
                            walk(child, parent_class=name)
                            
            elif node.type == 'import_statement':
                for child in node.children:
                    if child.type == 'dotted_name' or child.type == 'aliased_import':
                        name = child.text.decode('utf-8')
                        source = name.split(' ')[0] if child.type == 'aliased_import' else name
                        result.imports.append(ParsedImport(
                            source=source,
                            names=[source],
                            is_relative=False,
                            file_path=file_path,
                            line=node.start_point[0] + 1
                        ))
                        
            elif node.type == 'import_from_statement':
                module_name = node.child_by_field_name('module_name')
                source = module_name.text.decode('utf-8') if module_name else ""
                
                is_relative = False
                for c in node.children:
                    if c.type == 'relative_import' or c.text.decode('utf-8') == '.':
                        is_relative = True
                        break
                        
                names = []
                for child in node.children:
                    if child.type == 'dotted_name' or child.type == 'aliased_import':
                        names.append(child.text.decode('utf-8').split(' ')[0])
                
                if not source and is_relative:
                    source = "."
                
                result.imports.append(ParsedImport(
                    source=source,
                    names=names,
                    is_relative=is_relative,
                    file_path=file_path,
                    line=node.start_point[0] + 1
                ))
            
            else:
                for child in node.children:
                    walk(child, parent_class)
                    
        walk(tree.root_node)
        return result
""")

create_file("app/services/parser/javascript_parser.py", """
from tree_sitter_language_pack import get_parser
from app.services.parser.base import LanguageParser, FileParseResult, ParsedSymbol, ParsedImport

class JavaScriptParser(LanguageParser):
    def __init__(self):
        pass

    def supported_extensions(self) -> list[str]:
        return [".js", ".jsx", ".ts", ".tsx", ".mjs", ".cjs"]

    def parse_file(self, content: str, file_path: str) -> FileParseResult:
        ext = file_path.split('.')[-1].lower()
        if ext in ['ts', 'mts', 'cts']:
            parser = get_parser('typescript')
        elif ext == 'tsx':
            parser = get_parser('tsx')
        else:
            parser = get_parser('javascript')
            
        result = FileParseResult()
        tree = parser.parse(content.encode('utf-8'))
        
        def walk(node, parent_class=None):
            if node.type in ['function_declaration', 'method_definition']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8')
                    sym_type = "method" if node.type == 'method_definition' else "function"
                    
                    complexity = 1
                    body_node = node.child_by_field_name('body')
                    if body_node:
                        def count_complexity(n):
                            c = 0
                            if n.type in ['if_statement', 'for_statement', 'for_in_statement', 'while_statement', 'do_statement', 'switch_case', 'catch_clause', 'ternary_expression', 'binary_expression']:
                                if n.type == 'binary_expression':
                                    op = n.child_by_field_name('operator')
                                    if op and op.text.decode('utf-8') in ['&&', '||']:
                                        c += 1
                                else:
                                    if n.type == 'switch_case' and n.text.decode('utf-8').startswith('default'):
                                        pass
                                    else:
                                        c += 1
                            for child in n.children:
                                c += count_complexity(child)
                            return c
                        complexity = 1 + count_complexity(body_node)
                        
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type=sym_type,
                        language="JavaScript" if ext not in ['ts', 'tsx'] else "TypeScript",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        class_name=parent_class,
                        complexity=complexity
                    ))
            
            elif node.type == 'variable_declarator':
                name_node = node.child_by_field_name('name')
                value_node = node.child_by_field_name('value')
                if name_node and value_node and value_node.type == 'arrow_function':
                    name = name_node.text.decode('utf-8')
                    complexity = 1
                    body_node = value_node.child_by_field_name('body')
                    if body_node:
                        def count_complexity(n):
                            c = 0
                            if n.type in ['if_statement', 'for_statement', 'for_in_statement', 'while_statement', 'do_statement', 'switch_case', 'catch_clause', 'ternary_expression', 'binary_expression']:
                                if n.type == 'binary_expression':
                                    op = n.child_by_field_name('operator')
                                    if op and op.text.decode('utf-8') in ['&&', '||']:
                                        c += 1
                                else:
                                    if n.type == 'switch_case' and n.text.decode('utf-8').startswith('default'):
                                        pass
                                    else:
                                        c += 1
                            for child in n.children:
                                c += count_complexity(child)
                            return c
                        complexity = 1 + count_complexity(body_node)
                        
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type="function",
                        language="JavaScript" if ext not in ['ts', 'tsx'] else "TypeScript",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        class_name=parent_class,
                        complexity=complexity
                    ))
            
            elif node.type in ['class_declaration', 'interface_declaration']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8')
                    sym_type = "class" if node.type == 'class_declaration' else "interface"
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type=sym_type,
                        language="JavaScript" if ext not in ['ts', 'tsx'] else "TypeScript",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1
                    ))
                    
                    body_node = node.child_by_field_name('body')
                    if body_node:
                        for child in body_node.children:
                            walk(child, parent_class=name)
                            
            elif node.type == 'import_statement':
                source_node = node.child_by_field_name('source')
                if source_node:
                    source = source_node.text.decode('utf-8').strip('\"\\'')
                    is_relative = source.startswith('.')
                    names = []
                    
                    import_clause = node.children[1] if len(node.children) > 1 else None
                    if import_clause:
                        for child in import_clause.children:
                            if child.type == 'named_imports':
                                for spec in child.children:
                                    if spec.type == 'import_specifier':
                                        n = spec.child_by_field_name('name')
                                        if n:
                                            names.append(n.text.decode('utf-8'))
                            elif child.type == 'identifier':
                                names.append(child.text.decode('utf-8'))
                                
                    result.imports.append(ParsedImport(
                        source=source,
                        names=names,
                        is_relative=is_relative,
                        file_path=file_path,
                        line=node.start_point[0] + 1
                    ))
            
            elif node.type == 'export_statement':
                # Simplified export gathering
                pass
            
            else:
                for child in node.children:
                    walk(child, parent_class)
                    
        walk(tree.root_node)
        return result
""")

create_file("app/services/parser/java_parser.py", """
from tree_sitter_language_pack import get_parser
from app.services.parser.base import LanguageParser, FileParseResult, ParsedSymbol, ParsedImport

class JavaParser(LanguageParser):
    def __init__(self):
        self.parser = get_parser('java')

    def supported_extensions(self) -> list[str]:
        return [".java"]

    def parse_file(self, content: str, file_path: str) -> FileParseResult:
        result = FileParseResult()
        tree = self.parser.parse(content.encode('utf-8'))
        
        def walk(node, parent_class=None):
            if node.type in ['method_declaration', 'constructor_declaration']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8')
                    
                    complexity = 1
                    body_node = node.child_by_field_name('body')
                    if body_node:
                        def count_complexity(n):
                            c = 0
                            if n.type in ['if_statement', 'for_statement', 'enhanced_for_statement', 'while_statement', 'do_statement', 'catch_clause', 'ternary_expression', 'binary_expression']:
                                if n.type == 'binary_expression':
                                    op = n.child_by_field_name('operator')
                                    if op and op.text.decode('utf-8') in ['&&', '||']:
                                        c += 1
                                else:
                                    c += 1
                            elif n.type == 'switch_label' and n.text.decode('utf-8').startswith('case'):
                                c += 1
                            for child in n.children:
                                c += count_complexity(child)
                            return c
                        complexity = 1 + count_complexity(body_node)
                        
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type="method",
                        language="Java",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1,
                        class_name=parent_class,
                        complexity=complexity
                    ))
            
            elif node.type in ['class_declaration', 'interface_declaration']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8')
                    sym_type = "class" if node.type == 'class_declaration' else "interface"
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type=sym_type,
                        language="Java",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1
                    ))
                    
                    body_node = node.child_by_field_name('body')
                    if body_node:
                        for child in body_node.children:
                            walk(child, parent_class=name)
                            
            elif node.type == 'import_declaration':
                # children usually include the scoped_identifier
                for child in node.children:
                    if child.type == 'scoped_identifier' or child.type == 'identifier':
                        source = child.text.decode('utf-8')
                        result.imports.append(ParsedImport(
                            source=source,
                            names=[source.split('.')[-1]],
                            is_relative=False,
                            file_path=file_path,
                            line=node.start_point[0] + 1
                        ))
            
            else:
                for child in node.children:
                    walk(child, parent_class)
                    
        walk(tree.root_node)
        return result
""")

create_file("app/services/parser/cpp_parser.py", """
from tree_sitter_language_pack import get_parser
from app.services.parser.base import LanguageParser, FileParseResult, ParsedSymbol, ParsedImport

class CppParser(LanguageParser):
    def __init__(self):
        self.parser = get_parser('cpp')

    def supported_extensions(self) -> list[str]:
        return [".cpp", ".cc", ".cxx", ".c", ".h", ".hpp"]

    def parse_file(self, content: str, file_path: str) -> FileParseResult:
        result = FileParseResult()
        tree = self.parser.parse(content.encode('utf-8'))
        
        def walk(node, parent_class=None):
            if node.type == 'function_definition':
                declarator = node.child_by_field_name('declarator')
                name = "unknown"
                if declarator:
                    def get_name(n):
                        if n.type == 'identifier':
                            return n.text.decode('utf-8')
                        elif n.type == 'field_identifier':
                            return n.text.decode('utf-8')
                        elif n.type == 'scoped_identifier':
                            id_node = n.child_by_field_name('name')
                            if id_node:
                                return id_node.text.decode('utf-8')
                            else:
                                # Fallback
                                return n.text.decode('utf-8').split('::')[-1]
                        for c in n.children:
                            res = get_name(c)
                            if res: return res
                        return None
                    n = get_name(declarator)
                    if n:
                        name = n
                        
                complexity = 1
                body_node = node.child_by_field_name('body')
                if body_node:
                    def count_complexity(n):
                        c = 0
                        if n.type in ['if_statement', 'for_statement', 'while_statement', 'do_statement', 'catch_clause', 'conditional_expression', 'binary_expression', 'case_statement']:
                            if n.type == 'binary_expression':
                                op = n.child_by_field_name('operator')
                                if op and op.text.decode('utf-8') in ['&&', '||']:
                                    c += 1
                            else:
                                c += 1
                        for child in n.children:
                            c += count_complexity(child)
                        return c
                    complexity = 1 + count_complexity(body_node)
                    
                result.symbols.append(ParsedSymbol(
                    name=name,
                    symbol_type="function",
                    language="C++",
                    file_path=file_path,
                    start_line=node.start_point[0] + 1,
                    end_line=node.end_point[0] + 1,
                    class_name=parent_class,
                    complexity=complexity
                ))
            
            elif node.type in ['class_specifier', 'struct_specifier']:
                name_node = node.child_by_field_name('name')
                if name_node:
                    name = name_node.text.decode('utf-8')
                    sym_type = "class" if node.type == 'class_specifier' else "struct"
                    result.symbols.append(ParsedSymbol(
                        name=name,
                        symbol_type=sym_type,
                        language="C++",
                        file_path=file_path,
                        start_line=node.start_point[0] + 1,
                        end_line=node.end_point[0] + 1
                    ))
                    
                    body_node = node.child_by_field_name('body')
                    if body_node:
                        for child in body_node.children:
                            walk(child, parent_class=name)
                            
            elif node.type == 'preproc_include':
                path_node = node.child_by_field_name('path')
                if path_node:
                    source = path_node.text.decode('utf-8').strip('<>\"')
                    result.imports.append(ParsedImport(
                        source=source,
                        names=[],
                        is_relative=path_node.type == 'string_literal',
                        file_path=file_path,
                        line=node.start_point[0] + 1
                    ))
            
            else:
                for child in node.children:
                    walk(child, parent_class)
                    
        walk(tree.root_node)
        return result
""")

create_file("app/services/parser/registry.py", """
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
""")

create_file("app/services/analysis/code_parser.py", """
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
""")

create_file("app/services/analysis/metrics.py", """
from dataclasses import dataclass, field
from app.services.parser.base import ParsedSymbol, ParsedImport

@dataclass
class CodeMetrics:
    total_functions: int = 0
    total_classes: int = 0
    total_methods: int = 0
    avg_complexity: float = 0.0
    max_complexity: int = 0
    complexity_distribution: dict = field(default_factory=lambda: {"low": 0, "medium": 0, "high": 0, "very_high": 0})
    avg_function_length: float = 0.0
    internal_dependencies: int = 0
    external_dependencies: int = 0

class MetricsCalculator:
    COMPLEXITY_THRESHOLDS = {"low": 5, "medium": 10, "high": 20}
    
    def compute(self, symbols: list[ParsedSymbol], imports: list[ParsedImport], resolved_imports: list) -> CodeMetrics:
        metrics = CodeMetrics()
        
        function_symbols = []
        for sym in symbols:
            if sym.symbol_type == "function":
                metrics.total_functions += 1
                function_symbols.append(sym)
            elif sym.symbol_type == "method":
                metrics.total_methods += 1
                function_symbols.append(sym)
            elif sym.symbol_type == "class":
                metrics.total_classes += 1
                
        if function_symbols:
            total_complexity = 0
            total_length = 0
            for sym in function_symbols:
                c = sym.complexity
                total_complexity += c
                metrics.max_complexity = max(metrics.max_complexity, c)
                
                if c <= self.COMPLEXITY_THRESHOLDS["low"]:
                    metrics.complexity_distribution["low"] += 1
                elif c <= self.COMPLEXITY_THRESHOLDS["medium"]:
                    metrics.complexity_distribution["medium"] += 1
                elif c <= self.COMPLEXITY_THRESHOLDS["high"]:
                    metrics.complexity_distribution["high"] += 1
                else:
                    metrics.complexity_distribution["very_high"] += 1
                    
                total_length += (sym.end_line - sym.start_line + 1)
                
            metrics.avg_complexity = total_complexity / len(function_symbols)
            metrics.avg_function_length = total_length / len(function_symbols)
            
        for imp in resolved_imports:
            if getattr(imp, "is_internal", False):
                metrics.internal_dependencies += 1
            else:
                metrics.external_dependencies += 1
                
        return metrics
""")

create_file("app/services/analysis/dependency_resolver.py", """
from pathlib import Path
from dataclasses import dataclass
from app.services.parser.base import ParsedImport

@dataclass
class ResolvedImport:
    file_path: str
    source: str
    names: list[str]
    is_relative: bool
    resolved_path: str | None
    is_internal: bool
    line: int

class DependencyResolver:
    def resolve(self, imports: list[ParsedImport], file_paths: set[str], repo_dir: Path) -> list[ResolvedImport]:
        results = []
        for imp in imports:
            resolved = self._resolve_import(imp, file_paths, repo_dir)
            results.append(resolved)
        return results
    
    def _resolve_import(self, imp: ParsedImport, file_paths: set[str], repo_dir: Path) -> ResolvedImport:
        resolved_path = None
        is_internal = False
        
        if imp.file_path.endswith('.py'):
            if imp.is_relative:
                parts = imp.source.lstrip('.').split('.')
                base_dir = Path(imp.file_path).parent
                # Rough approximation for relative python imports
                target = base_dir / '/'.join(parts)
            else:
                target = Path(imp.source.replace('.', '/'))
                
            candidate1 = f"{target}.py"
            candidate2 = f"{target}/__init__.py"
            
            if candidate1.replace('\\\\', '/') in file_paths:
                resolved_path = candidate1.replace('\\\\', '/')
                is_internal = True
            elif candidate2.replace('\\\\', '/') in file_paths:
                resolved_path = candidate2.replace('\\\\', '/')
                is_internal = True
                
        elif any(imp.file_path.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx']):
            if imp.is_relative:
                base_dir = Path(imp.file_path).parent
                target = base_dir / imp.source
                target_str = str(target).replace('\\\\', '/')
                
                candidates = [
                    f"{target_str}.js", f"{target_str}.ts",
                    f"{target_str}.jsx", f"{target_str}.tsx",
                    f"{target_str}/index.js", f"{target_str}/index.ts"
                ]
                
                for c in candidates:
                    # Clean up paths like a/b/../c -> a/c
                    clean_c = os.path.normpath(c).replace('\\\\', '/')
                    if clean_c in file_paths:
                        resolved_path = clean_c
                        is_internal = True
                        break
        
        return ResolvedImport(
            file_path=imp.file_path,
            source=imp.source,
            names=imp.names,
            is_relative=imp.is_relative,
            resolved_path=resolved_path,
            is_internal=is_internal,
            line=imp.line
        )
""")

create_file("app/models/code_symbol.py", """
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, ForeignKey, Text, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class CodeSymbol(BaseModel):
    __tablename__ = "code_symbols"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String, index=True)
    name: Mapped[str] = mapped_column(String, index=True)
    symbol_type: Mapped[str] = mapped_column(String, index=True)  # function, class, method, interface
    language: Mapped[str] = mapped_column(String)
    start_line: Mapped[int] = mapped_column(Integer)
    end_line: Mapped[int] = mapped_column(Integer)
    class_name: Mapped[str | None] = mapped_column(String, nullable=True)
    signature: Mapped[str | None] = mapped_column(Text, nullable=True)
    docstring: Mapped[str | None] = mapped_column(Text, nullable=True)
    decorators: Mapped[list] = mapped_column(JSON, default=list)
    complexity: Mapped[int] = mapped_column(Integer, default=1)
""")

create_file("app/models/code_import.py", """
import uuid
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy import String, Integer, Boolean, ForeignKey, JSON
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import BaseModel

class CodeImport(BaseModel):
    __tablename__ = "code_imports"
    repository_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("repositories.id", ondelete="CASCADE"), index=True)
    file_path: Mapped[str] = mapped_column(String, index=True)
    source: Mapped[str] = mapped_column(String)
    names: Mapped[list] = mapped_column(JSON, default=list)
    is_relative: Mapped[bool] = mapped_column(Boolean, default=False)
    resolved_path: Mapped[str | None] = mapped_column(String, nullable=True)
    is_internal: Mapped[bool] = mapped_column(Boolean, default=False)
    line: Mapped[int] = mapped_column(Integer)
""")

create_file("app/schemas/symbols.py", """
from pydantic import BaseModel, ConfigDict
import uuid

class CodeSymbolResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str
    name: str
    symbol_type: str
    language: str
    start_line: int
    end_line: int
    class_name: str | None
    signature: str | None
    docstring: str | None
    decorators: list[str]
    complexity: int
    model_config = ConfigDict(from_attributes=True)

class CodeImportResponse(BaseModel):
    id: uuid.UUID
    repository_id: uuid.UUID
    file_path: str
    source: str
    names: list[str]
    is_relative: bool
    resolved_path: str | None
    is_internal: bool
    line: int
    model_config = ConfigDict(from_attributes=True)

class RepositoryMetricsResponse(BaseModel):
    total_functions: int
    total_classes: int
    total_methods: int
    avg_complexity: float
    max_complexity: int
    complexity_distribution: dict
    internal_dependencies: int
    external_dependencies: int
    model_config = ConfigDict(from_attributes=True)
""")

create_file("tests/test_python_parser.py", '''
import pytest
from app.services.parser.python_parser import PythonParser

SAMPLE = """
import os
from pathlib import Path

def simple_function(x, y):
    \\"\\"\\"Add two numbers.\\"\\"\\"
    return x + y

class Calculator:
    \\"\\"\\"A simple calculator.\\"\\"\\"
    
    def add(self, a, b):
        return a + b
    
    def complex_method(self, data):
        result = 0
        for item in data:
            if item > 0:
                if item % 2 == 0:
                    result += item
                else:
                    result -= item
            elif item == 0:
                continue
        return result

@decorator
def decorated_function():
    pass
"""

def test_extracts_functions():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    funcs = [s.name for s in res.symbols if s.symbol_type == "function"]
    assert "simple_function" in funcs
    assert "decorated_function" in funcs

def test_extracts_classes():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    classes = [s.name for s in res.symbols if s.symbol_type == "class"]
    assert "Calculator" in classes

def test_extracts_methods():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    methods = [s for s in res.symbols if s.symbol_type == "method"]
    method_names = [m.name for m in methods]
    assert "add" in method_names
    assert "complex_method" in method_names
    assert all(m.class_name == "Calculator" for m in methods)

def test_extracts_imports():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    sources = [i.source for i in res.imports]
    assert "os" in sources
    assert "pathlib" in sources

def test_complexity():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    simple = next(s for s in res.symbols if s.name == "simple_function")
    complex_m = next(s for s in res.symbols if s.name == "complex_method")
    assert simple.complexity == 1
    assert complex_m.complexity > 1

def test_docstrings():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    simple = next(s for s in res.symbols if s.name == "simple_function")
    assert simple.docstring == "Add two numbers."

def test_signatures():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    simple = next(s for s in res.symbols if s.name == "simple_function")
    assert simple.signature == "def simple_function(x, y)"

def test_decorators():
    parser = PythonParser()
    res = parser.parse_file(SAMPLE, "test.py")
    deco = next(s for s in res.symbols if s.name == "decorated_function")
    assert "decorator" in deco.decorators
''')

create_file("tests/test_javascript_parser.py", '''
from app.services.parser.javascript_parser import JavaScriptParser

def test_extracts_js():
    parser = JavaScriptParser()
    SAMPLE = """
    function test() {}
    class MyClass { method() {} }
    const arrow = () => {};
    import { x } from './module';
    """
    res = parser.parse_file(SAMPLE, "test.js")
    names = [s.name for s in res.symbols]
    assert "test" in names
    assert "MyClass" in names
    assert "method" in names
    assert "arrow" in names
    assert res.imports[0].source == "./module"
''')

create_file("tests/test_java_parser.py", '''
from app.services.parser.java_parser import JavaParser

def test_extracts_java():
    parser = JavaParser()
    SAMPLE = """
    import java.util.List;
    class Main {
        public static void main(String[] args) {}
    }
    """
    res = parser.parse_file(SAMPLE, "test.java")
    names = [s.name for s in res.symbols]
    assert "Main" in names
    assert "main" in names
    assert len(res.imports) == 1
    assert res.imports[0].source == "java.util.List"
''')

create_file("tests/test_cpp_parser.py", '''
from app.services.parser.cpp_parser import CppParser

def test_extracts_cpp():
    parser = CppParser()
    SAMPLE = """
    #include <iostream>
    class MyClass {};
    void test() {}
    """
    res = parser.parse_file(SAMPLE, "test.cpp")
    names = [s.name for s in res.symbols]
    assert "MyClass" in names
    assert "test" in names
    assert len(res.imports) == 1
    assert res.imports[0].source == "iostream"
''')

create_file("tests/test_parser_registry.py", '''
from app.services.parser.registry import ParserRegistry
from app.services.parser.python_parser import PythonParser
from app.services.parser.javascript_parser import JavaScriptParser
from app.services.parser.java_parser import JavaParser
from app.services.parser.cpp_parser import CppParser

def test_gets_python_parser():
    reg = ParserRegistry()
    assert isinstance(reg.get_parser_for_file("test.py"), PythonParser)

def test_gets_js_parser():
    reg = ParserRegistry()
    assert isinstance(reg.get_parser_for_file("test.js"), JavaScriptParser)

def test_gets_java_parser():
    reg = ParserRegistry()
    assert isinstance(reg.get_parser_for_file("test.java"), JavaParser)

def test_gets_cpp_parser():
    reg = ParserRegistry()
    assert isinstance(reg.get_parser_for_file("test.cpp"), CppParser)

def test_returns_none_for_unknown():
    reg = ParserRegistry()
    assert reg.get_parser_for_file("test.unknown") is None

def test_supported_languages():
    reg = ParserRegistry()
    assert "Python" in reg.supported_languages()
''')

create_file("tests/test_metrics.py", '''
from app.services.analysis.metrics import MetricsCalculator, CodeMetrics
from app.services.parser.base import ParsedSymbol, ParsedImport
from app.services.analysis.dependency_resolver import ResolvedImport

def test_metrics_calculator():
    syms = [
        ParsedSymbol(name="f1", symbol_type="function", language="Python", file_path="t.py", start_line=1, end_line=10, complexity=2, decorators=[]),
        ParsedSymbol(name="C1", symbol_type="class", language="Python", file_path="t.py", start_line=11, end_line=20, complexity=1, decorators=[]),
        ParsedSymbol(name="m1", symbol_type="method", language="Python", file_path="t.py", start_line=12, end_line=15, complexity=3, decorators=[]),
    ]
    deps = [
        ResolvedImport(file_path="t.py", source="os", names=[], is_relative=False, resolved_path=None, is_internal=False, line=1),
        ResolvedImport(file_path="t.py", source="t2", names=[], is_relative=True, resolved_path="t2.py", is_internal=True, line=2)
    ]
    calc = MetricsCalculator()
    m = calc.compute(syms, [], deps)
    assert m.total_functions == 1
    assert m.total_classes == 1
    assert m.total_methods == 1
    assert m.avg_complexity == 2.5
    assert m.max_complexity == 3
    assert m.internal_dependencies == 1
    assert m.external_dependencies == 1
''')

create_file("tests/test_dependency_resolver.py", '''
from pathlib import Path
from app.services.analysis.dependency_resolver import DependencyResolver
from app.services.parser.base import ParsedImport

def test_resolves_python_import():
    r = DependencyResolver()
    imports = [ParsedImport(source="my_module", names=[], is_relative=False, file_path="main.py", line=1)]
    res = r.resolve(imports, {"my_module.py"}, Path("."))
    assert res[0].is_internal
    assert res[0].resolved_path == "my_module.py"

def test_resolves_js_relative_import():
    r = DependencyResolver()
    imports = [ParsedImport(source="./my_module", names=[], is_relative=True, file_path="src/main.js", line=1)]
    res = r.resolve(imports, {"src/my_module.js"}, Path("."))
    assert res[0].is_internal
    assert res[0].resolved_path == "src/my_module.js"

def test_marks_external_imports():
    r = DependencyResolver()
    imports = [ParsedImport(source="react", names=[], is_relative=False, file_path="src/main.js", line=1)]
    res = r.resolve(imports, {"src/my_module.js"}, Path("."))
    assert not res[0].is_internal
    assert res[0].resolved_path is None
''')

print("Files created successfully.")
