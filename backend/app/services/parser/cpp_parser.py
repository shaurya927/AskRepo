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
                    source = path_node.text.decode('utf-8').strip('<>"')
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
