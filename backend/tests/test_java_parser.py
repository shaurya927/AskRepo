"""Tests for the Java parser."""

from app.services.parser.java_parser import JavaParser


JAVA_SAMPLE = '''
import java.util.List;
import java.util.Map;

public class UserService {

    @Override
    public User getUser(String id) {
        if (id == null) {
            throw new IllegalArgumentException("ID required");
        }
        return repository.findById(id);
    }

    public List<User> searchUsers(String query) {
        return repository.search(query);
    }
}

interface Repository {
    User findById(String id);
    List<User> search(String query);
}
'''


class TestJavaParser:
    def setup_method(self):
        self.parser = JavaParser()

    def test_extracts_classes(self):
        result = self.parser.parse_file(JAVA_SAMPLE, "UserService.java")
        class_names = [s.name for s in result.symbols if s.symbol_type == "class"]
        assert "UserService" in class_names

    def test_extracts_methods(self):
        result = self.parser.parse_file(JAVA_SAMPLE, "UserService.java")
        methods = [s for s in result.symbols if s.symbol_type == "method"]
        method_names = [m.name for m in methods]
        assert "getUser" in method_names
        assert "searchUsers" in method_names

    def test_extracts_interfaces(self):
        result = self.parser.parse_file(JAVA_SAMPLE, "UserService.java")
        interfaces = [s for s in result.symbols if s.symbol_type == "interface"]
        interface_names = [i.name for i in interfaces]
        assert "Repository" in interface_names

    def test_extracts_imports(self):
        result = self.parser.parse_file(JAVA_SAMPLE, "UserService.java")
        sources = [imp.source for imp in result.imports]
        assert any("java.util.List" in s for s in sources)
        assert any("java.util.Map" in s for s in sources)

    def test_complexity(self):
        result = self.parser.parse_file(JAVA_SAMPLE, "UserService.java")
        get_user = next((s for s in result.symbols if s.name == "getUser"), None)
        if get_user:
            assert get_user.complexity > 1  # has an if

    def test_supported_extensions(self):
        assert ".java" in self.parser.supported_extensions()
