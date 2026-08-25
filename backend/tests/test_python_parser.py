"""Tests for the Python parser."""

from app.services.parser.python_parser import PythonParser


SAMPLE = '''
import os
from pathlib import Path

def simple_function(x, y):
    """Add two numbers."""
    return x + y

class Calculator:
    """A simple calculator."""

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
'''


class TestPythonParser:
    def setup_method(self):
        self.parser = PythonParser()

    def test_extracts_functions(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        func_names = [s.name for s in result.symbols if s.symbol_type == "function"]
        assert "simple_function" in func_names
        assert "decorated_function" in func_names

    def test_extracts_classes(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        class_names = [s.name for s in result.symbols if s.symbol_type == "class"]
        assert "Calculator" in class_names

    def test_extracts_methods(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = [m.name for m in methods]
        assert "add" in method_names
        assert "complex_method" in method_names
        for m in methods:
            assert m.class_name == "Calculator"

    def test_extracts_imports(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        sources = [imp.source for imp in result.imports]
        assert "os" in sources
        assert "pathlib" in sources

    def test_complexity_simple(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        simple = next(s for s in result.symbols if s.name == "simple_function")
        assert simple.complexity == 1

    def test_complexity_complex(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        cmplx = next(s for s in result.symbols if s.name == "complex_method")
        # for + if + if + else (via elif) = at least 4 branches
        assert cmplx.complexity > 1

    def test_docstrings(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        simple = next(s for s in result.symbols if s.name == "simple_function")
        assert simple.docstring is not None
        assert "Add two numbers" in simple.docstring

    def test_signatures(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        simple = next(s for s in result.symbols if s.name == "simple_function")
        assert simple.signature is not None
        assert "x" in simple.signature
        assert "y" in simple.signature

    def test_decorators(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        decorated = next(s for s in result.symbols if s.name == "decorated_function")
        assert "decorator" in decorated.decorators

    def test_language_is_python(self):
        result = self.parser.parse_file(SAMPLE, "test.py")
        for sym in result.symbols:
            assert sym.language == "Python"

    def test_supported_extensions(self):
        assert ".py" in self.parser.supported_extensions()
