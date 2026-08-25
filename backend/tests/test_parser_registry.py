"""Tests for parser registry."""

from app.services.parser.registry import ParserRegistry


class TestParserRegistry:
    def setup_method(self):
        self.registry = ParserRegistry()

    def test_gets_python_parser(self):
        parser = self.registry.get_parser_for_file("main.py")
        assert parser is not None

    def test_gets_js_parser(self):
        parser = self.registry.get_parser_for_file("app.js")
        assert parser is not None

    def test_gets_ts_parser(self):
        parser = self.registry.get_parser_for_file("app.ts")
        assert parser is not None

    def test_gets_tsx_parser(self):
        parser = self.registry.get_parser_for_file("App.tsx")
        assert parser is not None

    def test_gets_java_parser(self):
        parser = self.registry.get_parser_for_file("Main.java")
        assert parser is not None

    def test_gets_cpp_parser(self):
        parser = self.registry.get_parser_for_file("main.cpp")
        assert parser is not None

    def test_gets_header_parser(self):
        parser = self.registry.get_parser_for_file("utils.h")
        assert parser is not None

    def test_returns_none_for_unknown(self):
        parser = self.registry.get_parser_for_file("README.md")
        assert parser is None

    def test_returns_none_for_no_extension(self):
        parser = self.registry.get_parser_for_file("Makefile")
        assert parser is None

    def test_supported_languages(self):
        langs = self.registry.supported_languages()
        assert "Python" in langs
        assert "JavaScript" in langs
        assert "Java" in langs
        assert "C++" in langs
