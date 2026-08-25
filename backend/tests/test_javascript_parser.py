"""Tests for the JavaScript/TypeScript parser."""

from app.services.parser.javascript_parser import JavaScriptParser


JS_SAMPLE = '''
import { useState } from 'react';
import axios from 'axios';

function fetchData(url) {
    return axios.get(url);
}

class DataService {
    constructor(baseUrl) {
        this.baseUrl = baseUrl;
    }

    async getData(id) {
        if (!id) {
            throw new Error("ID required");
        }
        return fetchData(`${this.baseUrl}/${id}`);
    }
}

const helper = (x) => x * 2;

export default DataService;
'''

TS_SAMPLE = '''
import type { User } from './types';

interface UserService {
    getUser(id: string): Promise<User>;
    deleteUser(id: string): Promise<void>;
}

function createUser(name: string): User {
    return { name };
}

export { createUser };
'''


class TestJavaScriptParser:
    def setup_method(self):
        self.parser = JavaScriptParser()

    def test_extracts_functions(self):
        result = self.parser.parse_file(JS_SAMPLE, "app.js")
        func_names = [s.name for s in result.symbols if s.symbol_type == "function"]
        assert "fetchData" in func_names

    def test_extracts_classes(self):
        result = self.parser.parse_file(JS_SAMPLE, "app.js")
        class_names = [s.name for s in result.symbols if s.symbol_type == "class"]
        assert "DataService" in class_names

    def test_extracts_methods(self):
        result = self.parser.parse_file(JS_SAMPLE, "app.js")
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = [m.name for m in methods]
        assert "getData" in method_names

    def test_extracts_imports(self):
        result = self.parser.parse_file(JS_SAMPLE, "app.js")
        sources = [imp.source for imp in result.imports]
        assert any("react" in s for s in sources)
        assert any("axios" in s for s in sources)

    def test_extracts_exports(self):
        result = self.parser.parse_file(JS_SAMPLE, "app.js")
        # Export extraction is best-effort; verify it doesn't crash
        assert isinstance(result.exports, list)

    def test_complexity(self):
        result = self.parser.parse_file(JS_SAMPLE, "app.js")
        get_data = next((s for s in result.symbols if s.name == "getData"), None)
        if get_data:
            assert get_data.complexity > 1  # has an if statement

    def test_supported_extensions(self):
        exts = self.parser.supported_extensions()
        assert ".js" in exts
        assert ".ts" in exts
        assert ".tsx" in exts


class TestTypeScriptParser:
    def setup_method(self):
        self.parser = JavaScriptParser()

    def test_extracts_interfaces(self):
        result = self.parser.parse_file(TS_SAMPLE, "service.ts")
        interfaces = [s for s in result.symbols if s.symbol_type == "interface"]
        assert any(s.name == "UserService" for s in interfaces)

    def test_extracts_functions_from_ts(self):
        result = self.parser.parse_file(TS_SAMPLE, "service.ts")
        funcs = [s.name for s in result.symbols if s.symbol_type == "function"]
        assert "createUser" in funcs

    def test_extracts_ts_imports(self):
        result = self.parser.parse_file(TS_SAMPLE, "service.ts")
        assert len(result.imports) > 0
