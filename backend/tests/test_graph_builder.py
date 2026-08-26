"""Tests for the dependency graph builder."""

from app.services.graph.graph_builder import GraphBuilder


class TestBuildFileGraph:

    def setup_method(self):
        self.builder = GraphBuilder()

    def test_creates_nodes_from_symbols(self):
        symbols = [
            {"file_path": "app/main.py", "name": "main", "symbol_type": "function", "language": "Python"},
            {"file_path": "app/utils.py", "name": "helper", "symbol_type": "function", "language": "Python"},
        ]
        g = self.builder.build_file_graph(symbols, [])
        assert len(g.nodes) == 2
        assert "app/main.py" in g.nodes
        assert g.nodes["app/main.py"]["language"] == "Python"

    def test_creates_edges_from_internal_imports(self):
        symbols = [
            {"file_path": "app/main.py", "name": "main", "symbol_type": "function", "language": "Python"},
            {"file_path": "app/utils.py", "name": "helper", "symbol_type": "function", "language": "Python"},
        ]
        imports = [
            {"file_path": "app/main.py", "source": "app.utils", "resolved_path": "app/utils.py", "is_internal": True},
        ]
        g = self.builder.build_file_graph(symbols, imports)
        assert g.has_edge("app/main.py", "app/utils.py")

    def test_ignores_external_imports(self):
        symbols = [
            {"file_path": "app/main.py", "name": "main", "symbol_type": "function", "language": "Python"},
        ]
        imports = [
            {"file_path": "app/main.py", "source": "flask", "resolved_path": None, "is_internal": False},
        ]
        g = self.builder.build_file_graph(symbols, imports)
        assert len(g.edges) == 0

    def test_tracks_symbol_counts(self):
        symbols = [
            {"file_path": "app/main.py", "name": "func1", "symbol_type": "function", "language": "Python"},
            {"file_path": "app/main.py", "name": "func2", "symbol_type": "function", "language": "Python"},
            {"file_path": "app/main.py", "name": "MyClass", "symbol_type": "class", "language": "Python"},
        ]
        g = self.builder.build_file_graph(symbols, [])
        assert g.nodes["app/main.py"]["symbol_count"] == 3

    def test_empty_graph(self):
        g = self.builder.build_file_graph([], [])
        assert len(g.nodes) == 0
        assert len(g.edges) == 0


class TestBuildModuleGraph:

    def setup_method(self):
        self.builder = GraphBuilder()

    def test_aggregates_files_into_modules(self):
        symbols = [
            {"file_path": "src/services/auth.py", "name": "login", "symbol_type": "function", "language": "Python"},
            {"file_path": "src/services/user.py", "name": "get_user", "symbol_type": "function", "language": "Python"},
            {"file_path": "src/models/user.py", "name": "User", "symbol_type": "class", "language": "Python"},
        ]
        file_graph = self.builder.build_file_graph(symbols, [])
        mod_graph = self.builder.build_module_graph(file_graph)
        assert "src/services" in mod_graph.nodes
        assert "src/models" in mod_graph.nodes

    def test_module_edges_deduplicated(self):
        symbols = [
            {"file_path": "src/api/routes.py", "name": "route", "symbol_type": "function", "language": "Python"},
            {"file_path": "src/api/views.py", "name": "view", "symbol_type": "function", "language": "Python"},
            {"file_path": "src/services/svc.py", "name": "svc", "symbol_type": "function", "language": "Python"},
        ]
        imports = [
            {"file_path": "src/api/routes.py", "source": "services", "resolved_path": "src/services/svc.py", "is_internal": True},
            {"file_path": "src/api/views.py", "source": "services", "resolved_path": "src/services/svc.py", "is_internal": True},
        ]
        file_graph = self.builder.build_file_graph(symbols, imports)
        mod_graph = self.builder.build_module_graph(file_graph)
        # Only one edge between api and services modules
        edges = list(mod_graph.edges)
        api_to_svc = [e for e in edges if "api" in e[0] and "services" in e[1]]
        assert len(api_to_svc) == 1


class TestNodeDetail:

    def setup_method(self):
        self.builder = GraphBuilder()

    def test_returns_deps_and_dependents(self):
        symbols = [
            {"file_path": "a.py", "name": "fa", "symbol_type": "function", "language": "Python", "start_line": 1, "end_line": 5, "complexity": 1},
            {"file_path": "b.py", "name": "fb", "symbol_type": "function", "language": "Python", "start_line": 1, "end_line": 5, "complexity": 1},
            {"file_path": "c.py", "name": "fc", "symbol_type": "function", "language": "Python", "start_line": 1, "end_line": 5, "complexity": 1},
        ]
        imports = [
            {"file_path": "a.py", "source": "b", "resolved_path": "b.py", "is_internal": True},
            {"file_path": "c.py", "source": "a", "resolved_path": "a.py", "is_internal": True},
        ]
        g = self.builder.build_file_graph(symbols, imports)
        detail = self.builder.get_node_detail(g, "a.py", symbols)
        assert "b.py" in detail.dependencies
        assert "c.py" in detail.dependents

    def test_unknown_node(self):
        g = self.builder.build_file_graph([], [])
        detail = self.builder.get_node_detail(g, "nonexistent.py", [])
        assert detail.node_type == "unknown"


class TestReactFlowSerialization:

    def setup_method(self):
        self.builder = GraphBuilder()

    def test_serializes_nodes_and_edges(self):
        symbols = [
            {"file_path": "a.py", "name": "fa", "symbol_type": "function", "language": "Python"},
            {"file_path": "b.py", "name": "fb", "symbol_type": "function", "language": "Python"},
        ]
        imports = [
            {"file_path": "a.py", "source": "b", "resolved_path": "b.py", "is_internal": True},
        ]
        g = self.builder.build_file_graph(symbols, imports)
        rf = self.builder.to_react_flow(g)
        assert "nodes" in rf
        assert "edges" in rf
        assert len(rf["nodes"]) == 2
        assert len(rf["edges"]) == 1
        # Check node structure
        node = rf["nodes"][0]
        assert "id" in node
        assert "position" in node
        assert "data" in node

    def test_empty_graph_serialization(self):
        g = self.builder.build_file_graph([], [])
        rf = self.builder.to_react_flow(g)
        assert rf == {"nodes": [], "edges": []}
