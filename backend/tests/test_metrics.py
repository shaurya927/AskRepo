"""Tests for metrics calculator."""

from app.services.analysis.metrics import MetricsCalculator, CodeMetrics
from app.services.parser.base import ParsedSymbol, ParsedImport
from app.services.analysis.dependency_resolver import ResolvedImport


class TestMetricsCalculator:
    def setup_method(self):
        self.calc = MetricsCalculator()

    def _make_symbol(self, name, sym_type, complexity=1, start=1, end=5):
        return ParsedSymbol(
            name=name, symbol_type=sym_type, language="Python",
            file_path="test.py", start_line=start, end_line=end,
            complexity=complexity,
        )

    def _make_resolved(self, is_internal=False):
        return ResolvedImport(
            file_path="test.py", source="os", names=["path"],
            is_relative=False, resolved_path="os.py" if is_internal else None,
            is_internal=is_internal, line=1,
        )

    def test_counts_functions(self):
        symbols = [self._make_symbol("f1", "function"), self._make_symbol("f2", "function")]
        metrics = self.calc.compute(symbols, [], [])
        assert metrics.total_functions == 2

    def test_counts_classes(self):
        symbols = [self._make_symbol("C1", "class"), self._make_symbol("C2", "class")]
        metrics = self.calc.compute(symbols, [], [])
        assert metrics.total_classes == 2

    def test_counts_methods(self):
        symbols = [self._make_symbol("m1", "method"), self._make_symbol("m2", "method")]
        metrics = self.calc.compute(symbols, [], [])
        assert metrics.total_methods == 2

    def test_avg_complexity(self):
        symbols = [
            self._make_symbol("f1", "function", complexity=2),
            self._make_symbol("f2", "function", complexity=8),
        ]
        metrics = self.calc.compute(symbols, [], [])
        assert metrics.avg_complexity == 5.0

    def test_max_complexity(self):
        symbols = [
            self._make_symbol("f1", "function", complexity=3),
            self._make_symbol("f2", "function", complexity=15),
        ]
        metrics = self.calc.compute(symbols, [], [])
        assert metrics.max_complexity == 15

    def test_complexity_distribution(self):
        symbols = [
            self._make_symbol("f1", "function", complexity=2),   # low
            self._make_symbol("f2", "function", complexity=7),   # medium
            self._make_symbol("f3", "function", complexity=15),  # high
            self._make_symbol("f4", "function", complexity=25),  # very_high
        ]
        metrics = self.calc.compute(symbols, [], [])
        assert metrics.complexity_distribution["low"] == 1
        assert metrics.complexity_distribution["medium"] == 1
        assert metrics.complexity_distribution["high"] == 1
        assert metrics.complexity_distribution["very_high"] == 1

    def test_internal_vs_external_deps(self):
        resolved = [
            self._make_resolved(is_internal=True),
            self._make_resolved(is_internal=True),
            self._make_resolved(is_internal=False),
        ]
        metrics = self.calc.compute([], [], resolved)
        assert metrics.internal_dependencies == 2
        assert metrics.external_dependencies == 1

    def test_empty_symbols(self):
        metrics = self.calc.compute([], [], [])
        assert metrics.total_functions == 0
        assert metrics.avg_complexity == 0.0
