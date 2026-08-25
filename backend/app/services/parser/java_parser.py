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
