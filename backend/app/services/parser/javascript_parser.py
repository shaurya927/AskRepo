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
                    source = source_node.text.decode('utf-8').strip('"\'')
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
