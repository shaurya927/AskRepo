import os
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
            
            if candidate1.replace('\\', '/') in file_paths:
                resolved_path = candidate1.replace('\\', '/')
                is_internal = True
            elif candidate2.replace('\\', '/') in file_paths:
                resolved_path = candidate2.replace('\\', '/')
                is_internal = True
                
        elif any(imp.file_path.endswith(ext) for ext in ['.js', '.jsx', '.ts', '.tsx']):
            if imp.is_relative:
                base_dir = Path(imp.file_path).parent
                target = base_dir / imp.source
                target_str = str(target).replace('\\', '/')
                
                candidates = [
                    f"{target_str}.js", f"{target_str}.ts",
                    f"{target_str}.jsx", f"{target_str}.tsx",
                    f"{target_str}/index.js", f"{target_str}/index.ts"
                ]
                
                for c in candidates:
                    # Clean up paths like a/b/../c -> a/c
                    clean_c = os.path.normpath(c).replace('\\', '/')
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
