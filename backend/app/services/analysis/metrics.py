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
