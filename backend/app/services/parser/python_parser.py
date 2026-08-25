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
                            # docstring — can be direct `string` child or inside `expression_statement`
                            if len(body_node.children) > 0:
                                first_stmt = body_node.children[0]
                                doc_node = None
                                if first_stmt.type == 'string':
                                    doc_node = first_stmt
                                elif first_stmt.type == 'expression_statement' and len(first_stmt.children) > 0:
                                    expr = first_stmt.children[0]
                                    if expr.type == 'string':
                                        doc_node = expr
                                if doc_node:
                                    raw = doc_node.text.decode('utf-8')
                                    for q in ('"""', "'''", '"', "'"):
                                        if raw.startswith(q) and raw.endswith(q):
                                            raw = raw[len(q):-len(q)]
                                            break
                                    docstring = raw.strip()
                            
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
                            doc_node = None
                            if first_stmt.type == 'string':
                                doc_node = first_stmt
                            elif first_stmt.type == 'expression_statement' and len(first_stmt.children) > 0:
                                expr = first_stmt.children[0]
                                if expr.type == 'string':
                                    doc_node = expr
                            if doc_node:
                                raw = doc_node.text.decode('utf-8')
                                for q in ('"""', "'''", '"', "'"):
                                    if raw.startswith(q) and raw.endswith(q):
                                        raw = raw[len(q):-len(q)]
                                        break
                                docstring = raw.strip()
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
                        doc_node = None
                        if first_stmt.type == 'string':
                            doc_node = first_stmt
                        elif first_stmt.type == 'expression_statement' and len(first_stmt.children) > 0:
                            expr = first_stmt.children[0]
                            if expr.type == 'string':
                                doc_node = expr
                        if doc_node:
                            raw = doc_node.text.decode('utf-8')
                            for q in ('"""', "'''", '"', "'"):
                                if raw.startswith(q) and raw.endswith(q):
                                    raw = raw[len(q):-len(q)]
                                    break
                            docstring = raw.strip()                    
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
