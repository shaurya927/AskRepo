"""Graph builder — constructs NetworkX dependency graphs from parsed code data."""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import PurePosixPath

import networkx as nx


# Language → color mapping for visualization
LANGUAGE_COLORS = {
    "Python": "#3572A5",
    "JavaScript": "#f1e05a",
    "TypeScript": "#3178c6",
    "Java": "#b07219",
    "C++": "#f34b7d",
    "C": "#555555",
    "Go": "#00ADD8",
    "Rust": "#dea584",
    "Ruby": "#701516",
    "PHP": "#4F5D95",
}


@dataclass
class NodeDetail:
    """Detail info for a single graph node."""
    node_id: str
    node_type: str  # file, module
    label: str
    language: str | None
    category: str | None
    dependencies: list[str]
    dependents: list[str]
    symbols: list[dict]
    symbol_count: int


class GraphBuilder:
    """Builds NetworkX directed graphs from code symbols and imports."""

    def build_file_graph(
        self,
        symbols: list[dict],
        imports: list[dict],
        files: list[dict] | None = None,
    ) -> nx.DiGraph:
        """Build a file-level dependency graph.

        Args:
            symbols: List of symbol dicts with file_path, name, symbol_type, language, etc.
            imports: List of import dicts with file_path, resolved_path, is_internal, source.
            files: Optional list of file dicts with path, language.
        """
        g = nx.DiGraph()

        # Collect all file paths and their languages
        file_languages: dict[str, str] = {}
        file_symbol_counts: dict[str, int] = {}

        for sym in symbols:
            fp = sym["file_path"]
            file_languages.setdefault(fp, sym.get("language", ""))
            file_symbol_counts[fp] = file_symbol_counts.get(fp, 0) + 1

        if files:
            for f in files:
                fp = f["path"]
                if fp not in file_languages:
                    file_languages[fp] = f.get("language", "")

        # Add file nodes
        for fp, lang in file_languages.items():
            g.add_node(fp, **{
                "node_type": "file",
                "label": PurePosixPath(fp).name,
                "language": lang,
                "symbol_count": file_symbol_counts.get(fp, 0),
                "color": LANGUAGE_COLORS.get(lang, "#8b949e"),
            })

        # Add edges from internal imports
        for imp in imports:
            if not imp.get("is_internal") or not imp.get("resolved_path"):
                continue
            src = imp["file_path"]
            dst = imp["resolved_path"]
            if src in g and dst in g and src != dst:
                g.add_edge(src, dst, edge_type="imports", source_module=imp.get("source", ""))

        return g

    def build_module_graph(self, file_graph: nx.DiGraph) -> nx.DiGraph:
        """Aggregate file graph into module-level (top directory) graph."""
        g = nx.DiGraph()

        def get_module(path: str) -> str:
            parts = PurePosixPath(path).parts
            if len(parts) <= 1:
                return "(root)"
            return str(PurePosixPath(*parts[:2]))  # e.g., "src/services"

        # Map files to modules
        file_to_module: dict[str, str] = {}
        module_files: dict[str, list[str]] = {}
        module_languages: dict[str, dict[str, int]] = {}

        for node in file_graph.nodes:
            mod = get_module(node)
            file_to_module[node] = mod
            module_files.setdefault(mod, []).append(node)
            lang = file_graph.nodes[node].get("language", "")
            if lang:
                counts = module_languages.setdefault(mod, {})
                counts[lang] = counts.get(lang, 0) + 1

        # Add module nodes
        for mod, files in module_files.items():
            primary_lang = ""
            lang_counts = module_languages.get(mod, {})
            if lang_counts:
                primary_lang = max(lang_counts, key=lang_counts.get)  # type: ignore
            g.add_node(mod, **{
                "node_type": "module",
                "label": mod,
                "language": primary_lang,
                "file_count": len(files),
                "color": LANGUAGE_COLORS.get(primary_lang, "#8b949e"),
            })

        # Add module-level edges (deduplicated)
        seen_edges: set[tuple[str, str]] = set()
        for src, dst in file_graph.edges:
            src_mod = file_to_module[src]
            dst_mod = file_to_module[dst]
            if src_mod != dst_mod and (src_mod, dst_mod) not in seen_edges:
                seen_edges.add((src_mod, dst_mod))
                g.add_edge(src_mod, dst_mod, edge_type="depends_on")

        return g

    def get_node_detail(
        self,
        graph: nx.DiGraph,
        node_id: str,
        symbols: list[dict],
        architecture: dict[str, list[str]] | None = None,
    ) -> NodeDetail:
        """Get detailed info about a specific node."""
        if node_id not in graph:
            return NodeDetail(
                node_id=node_id, node_type="unknown", label=node_id,
                language=None, category=None,
                dependencies=[], dependents=[], symbols=[], symbol_count=0,
            )

        node_data = graph.nodes[node_id]
        deps = list(graph.successors(node_id))
        dependents = list(graph.predecessors(node_id))

        # Find symbols in this file
        file_symbols = [
            {"name": s["name"], "symbol_type": s["symbol_type"],
             "start_line": s.get("start_line", 0), "end_line": s.get("end_line", 0),
             "complexity": s.get("complexity", 1)}
            for s in symbols if s["file_path"] == node_id
        ]

        # Find architecture category
        category = None
        if architecture:
            for cat, files in architecture.items():
                if node_id in files:
                    category = cat
                    break

        return NodeDetail(
            node_id=node_id,
            node_type=node_data.get("node_type", "file"),
            label=node_data.get("label", node_id),
            language=node_data.get("language"),
            category=category,
            dependencies=deps,
            dependents=dependents,
            symbols=file_symbols,
            symbol_count=len(file_symbols),
        )

    def to_react_flow(self, graph: nx.DiGraph) -> dict:
        """Convert NetworkX graph to React Flow format with layout positions."""
        if len(graph.nodes) == 0:
            return {"nodes": [], "edges": []}

        # Calculate layout positions
        try:
            pos = nx.spring_layout(graph, k=2.0, iterations=50, seed=42)
        except Exception:
            pos = {n: (i * 200, (i % 5) * 150) for i, n in enumerate(graph.nodes)}

        # Scale positions for React Flow (pixels)
        scale_x, scale_y = 400, 300
        nodes = []
        for node_id in graph.nodes:
            data = graph.nodes[node_id]
            x, y = pos.get(node_id, (0, 0))
            nodes.append({
                "id": node_id,
                "type": "custom",
                "position": {"x": float(x * scale_x), "y": float(y * scale_y)},
                "data": {
                    "label": data.get("label", node_id),
                    "language": data.get("language", ""),
                    "color": data.get("color", "#8b949e"),
                    "symbolCount": data.get("symbol_count", data.get("file_count", 0)),
                    "nodeType": data.get("node_type", "file"),
                },
            })

        edges = []
        for i, (src, dst) in enumerate(graph.edges):
            edge_data = graph.edges[src, dst]
            edges.append({
                "id": f"e-{i}",
                "source": src,
                "target": dst,
                "type": "smoothstep",
                "animated": False,
                "data": {"edgeType": edge_data.get("edge_type", "imports")},
            })

        return {"nodes": nodes, "edges": edges}
