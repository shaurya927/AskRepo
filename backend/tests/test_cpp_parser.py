"""Tests for the C++ parser."""

from app.services.parser.cpp_parser import CppParser


CPP_SAMPLE = '''
#include <iostream>
#include "utils.h"

namespace math {

class Calculator {
public:
    int add(int a, int b) {
        return a + b;
    }

    int process(int data[], int size) {
        int result = 0;
        for (int i = 0; i < size; i++) {
            if (data[i] > 0) {
                result += data[i];
            }
        }
        return result;
    }
};

int freeFunction(int x) {
    return x * 2;
}

} // namespace math
'''


class TestCppParser:
    def setup_method(self):
        self.parser = CppParser()

    def test_extracts_classes(self):
        result = self.parser.parse_file(CPP_SAMPLE, "calc.cpp")
        class_names = [s.name for s in result.symbols if s.symbol_type == "class"]
        assert "Calculator" in class_names

    def test_extracts_functions(self):
        result = self.parser.parse_file(CPP_SAMPLE, "calc.cpp")
        func_names = [s.name for s in result.symbols if s.symbol_type == "function"]
        assert "freeFunction" in func_names

    def test_extracts_includes(self):
        result = self.parser.parse_file(CPP_SAMPLE, "calc.cpp")
        sources = [imp.source for imp in result.imports]
        assert any("iostream" in s for s in sources)
        assert any("utils.h" in s for s in sources)

    def test_supported_extensions(self):
        exts = self.parser.supported_extensions()
        assert ".cpp" in exts
        assert ".h" in exts
        assert ".hpp" in exts
