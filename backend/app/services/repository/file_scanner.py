"""File scanner: walks repository directories, detects languages, identifies file types."""

import json
from dataclasses import dataclass, field
from pathlib import Path

from app.services.repository.file_filter import FileFilter


@dataclass
class ScanResult:
    """Result of scanning a repository directory."""
    files: list[dict] = field(default_factory=list)
    stats: dict = field(default_factory=dict)


class FileScanner:
    """Scans a repository directory and extracts file metadata."""

    # Comprehensive extension → language mapping
    LANGUAGE_MAP = {
        ".py": "Python",
        ".js": "JavaScript",
        ".mjs": "JavaScript",
        ".cjs": "JavaScript",
        ".ts": "TypeScript",
        ".tsx": "TypeScript",
        ".jsx": "JavaScript",
        ".java": "Java",
        ".cpp": "C++",
        ".cc": "C++",
        ".cxx": "C++",
        ".c": "C",
        ".h": "C/C++ Header",
        ".hpp": "C/C++ Header",
        ".go": "Go",
        ".rs": "Rust",
        ".rb": "Ruby",
        ".php": "PHP",
        ".swift": "Swift",
        ".kt": "Kotlin",
        ".kts": "Kotlin",
        ".scala": "Scala",
        ".cs": "C#",
        ".html": "HTML",
        ".htm": "HTML",
        ".css": "CSS",
        ".scss": "SCSS",
        ".sass": "SCSS",
        ".less": "Less",
        ".json": "JSON",
        ".yaml": "YAML",
        ".yml": "YAML",
        ".toml": "TOML",
        ".xml": "XML",
        ".md": "Markdown",
        ".rst": "reStructuredText",
        ".sql": "SQL",
        ".sh": "Shell",
        ".bash": "Shell",
        ".zsh": "Shell",
        ".fish": "Shell",
        ".ps1": "PowerShell",
        ".r": "R",
        ".R": "R",
        ".lua": "Lua",
        ".dart": "Dart",
        ".ex": "Elixir",
        ".exs": "Elixir",
        ".erl": "Erlang",
        ".hs": "Haskell",
        ".ml": "OCaml",
        ".clj": "Clojure",
        ".vue": "Vue",
        ".svelte": "Svelte",
        ".tf": "Terraform",
        ".proto": "Protocol Buffers",
        ".graphql": "GraphQL",
        ".gql": "GraphQL",
    }

    # Known configuration file names
    CONFIG_FILES = {
        "package.json",
        "package-lock.json",
        "yarn.lock",
        "pnpm-lock.yaml",
        "requirements.txt",
        "pyproject.toml",
        "setup.py",
        "setup.cfg",
        "Pipfile",
        "Pipfile.lock",
        "poetry.lock",
        "pom.xml",
        "build.gradle",
        "build.gradle.kts",
        "Cargo.toml",
        "Cargo.lock",
        "go.mod",
        "go.sum",
        "Gemfile",
        "Gemfile.lock",
        "composer.json",
        "composer.lock",
        "Dockerfile",
        "docker-compose.yml",
        "docker-compose.yaml",
        ".dockerignore",
        ".gitignore",
        ".eslintrc.json",
        ".eslintrc.js",
        ".prettierrc",
        "tsconfig.json",
        "vite.config.ts",
        "vite.config.js",
        "webpack.config.js",
        "next.config.js",
        "next.config.mjs",
        ".env.example",
        "Makefile",
        "CMakeLists.txt",
        "Procfile",
        "vercel.json",
        "netlify.toml",
        "fly.toml",
        "render.yaml",
    }

    # Known entry point patterns
    ENTRY_POINT_PATTERNS = {
        "main.py",
        "app.py",
        "manage.py",
        "wsgi.py",
        "asgi.py",
        "index.js",
        "index.ts",
        "index.tsx",
        "main.js",
        "main.ts",
        "main.tsx",
        "App.tsx",
        "App.jsx",
        "App.js",
        "server.js",
        "server.ts",
        "main.go",
        "main.rs",
        "Main.java",
        "App.java",
        "Program.cs",
    }

    def scan_repository(self, repo_dir: Path, file_filter: FileFilter, max_file_size: int) -> ScanResult:
        """Walk the repository and extract metadata for all relevant files."""
        files_data: list[dict] = []
        directories: set[str] = set()
        stats = {
            "total_files": 0,
            "total_directories": 0,
            "total_lines": 0,
            "total_size": 0,
            "languages": {},
            "test_files_count": 0,
            "config_files": [],
            "entry_points": [],
        }

        for p in repo_dir.rglob("*"):
            # Skip ignored directories entirely
            rel_parts = p.relative_to(repo_dir).parts
            if any(file_filter.should_ignore_directory(part) for part in rel_parts):
                continue

            if p.is_dir():
                directories.add(str(p.relative_to(repo_dir).as_posix()))
                continue

            if not p.is_file():
                continue

            if file_filter.should_ignore_file(p, max_file_size):
                continue

            lang = self.detect_language(p)
            try:
                size = p.stat().st_size
            except OSError:
                continue

            lines = 0
            try:
                with open(p, "r", encoding="utf-8", errors="replace") as f:
                    lines = sum(1 for _ in f)
            except Exception:
                continue

            rel_path = str(p.relative_to(repo_dir).as_posix())
            is_test = self._is_test_file(p, rel_path)
            is_config = p.name in self.CONFIG_FILES
            is_entry = p.name in self.ENTRY_POINT_PATTERNS

            stats["total_files"] += 1
            stats["total_lines"] += lines
            stats["total_size"] += size
            if is_test:
                stats["test_files_count"] += 1
            if is_config:
                stats["config_files"].append(rel_path)
            if is_entry:
                stats["entry_points"].append(rel_path)

            if lang:
                if lang not in stats["languages"]:
                    stats["languages"][lang] = {"files": 0, "lines": 0, "bytes": 0}
                stats["languages"][lang]["files"] += 1
                stats["languages"][lang]["lines"] += lines
                stats["languages"][lang]["bytes"] += size

            files_data.append({
                "path": rel_path,
                "language": lang,
                "size": size,
                "line_count": lines,
                "is_test": is_test,
                "is_config": is_config,
                "is_entry_point": is_entry,
            })

        stats["total_directories"] = len(directories)
        return ScanResult(files=files_data, stats=stats)

    def detect_language(self, path: Path) -> str | None:
        """Detect programming language from file extension."""
        name = path.name.lower()
        if name == "dockerfile":
            return "Dockerfile"
        if name == "makefile":
            return "Makefile"
        if name == "cmakelists.txt":
            return "CMake"
        return self.LANGUAGE_MAP.get(path.suffix.lower())

    def _is_test_file(self, path: Path, rel_path: str) -> bool:
        """Check if a file is a test file based on name and path patterns."""
        name = path.stem.lower()
        rel_lower = rel_path.lower()
        return (
            name.startswith("test_")
            or name.endswith("_test")
            or name.endswith(".test")
            or name.endswith(".spec")
            or name.startswith("spec_")
            or "__tests__" in rel_lower
            or "/tests/" in rel_lower
            or "/test/" in rel_lower
            or "/spec/" in rel_lower
            or rel_lower.startswith("tests/")
            or rel_lower.startswith("test/")
        )

    def detect_frameworks(self, repo_dir: Path, files: list[dict]) -> list[str]:
        """Detect frameworks from package manifests and config files."""
        frameworks: list[str] = []

        # Python frameworks
        for pyfile in ["requirements.txt", "pyproject.toml", "Pipfile", "setup.py", "setup.cfg"]:
            p = repo_dir / pyfile
            if p.exists():
                try:
                    content = p.read_text(encoding="utf-8", errors="replace").lower()
                    if "fastapi" in content:
                        frameworks.append("FastAPI")
                    if "django" in content:
                        frameworks.append("Django")
                    if "flask" in content:
                        frameworks.append("Flask")
                    if "starlette" in content:
                        frameworks.append("Starlette")
                    if "pytorch" in content or "torch" in content:
                        frameworks.append("PyTorch")
                    if "tensorflow" in content:
                        frameworks.append("TensorFlow")
                    if "sqlalchemy" in content:
                        frameworks.append("SQLAlchemy")
                    if "celery" in content:
                        frameworks.append("Celery")
                except Exception:
                    pass

        # JavaScript/TypeScript frameworks
        pkg_json = repo_dir / "package.json"
        if pkg_json.exists():
            try:
                pkg = json.loads(pkg_json.read_text(encoding="utf-8"))
                all_deps = {
                    **pkg.get("dependencies", {}),
                    **pkg.get("devDependencies", {}),
                }
                dep_names = set(all_deps.keys())
                framework_map = {
                    "react": "React",
                    "next": "Next.js",
                    "vue": "Vue.js",
                    "nuxt": "Nuxt.js",
                    "@angular/core": "Angular",
                    "svelte": "Svelte",
                    "express": "Express",
                    "fastify": "Fastify",
                    "nestjs": "NestJS",
                    "@nestjs/core": "NestJS",
                    "tailwindcss": "Tailwind CSS",
                    "vite": "Vite",
                    "webpack": "Webpack",
                    "jest": "Jest",
                    "mocha": "Mocha",
                    "electron": "Electron",
                    "react-native": "React Native",
                }
                for dep, name in framework_map.items():
                    if dep in dep_names:
                        frameworks.append(name)
            except Exception:
                pass

        # Java/Kotlin frameworks
        pom = repo_dir / "pom.xml"
        if pom.exists():
            try:
                content = pom.read_text(encoding="utf-8", errors="replace").lower()
                if "spring-boot" in content:
                    frameworks.append("Spring Boot")
                elif "spring" in content:
                    frameworks.append("Spring")
            except Exception:
                pass

        for gradle in ["build.gradle", "build.gradle.kts"]:
            g = repo_dir / gradle
            if g.exists():
                try:
                    content = g.read_text(encoding="utf-8", errors="replace").lower()
                    if "spring-boot" in content:
                        frameworks.append("Spring Boot")
                    if "ktor" in content:
                        frameworks.append("Ktor")
                except Exception:
                    pass

        # Rust frameworks
        cargo = repo_dir / "Cargo.toml"
        if cargo.exists():
            try:
                content = cargo.read_text(encoding="utf-8", errors="replace").lower()
                if "actix" in content:
                    frameworks.append("Actix")
                if "tokio" in content:
                    frameworks.append("Tokio")
                if "axum" in content:
                    frameworks.append("Axum")
            except Exception:
                pass

        # Go frameworks
        gomod = repo_dir / "go.mod"
        if gomod.exists():
            try:
                content = gomod.read_text(encoding="utf-8", errors="replace").lower()
                if "gin-gonic" in content:
                    frameworks.append("Gin")
                if "gorilla/mux" in content:
                    frameworks.append("Gorilla")
                if "fiber" in content:
                    frameworks.append("Fiber")
            except Exception:
                pass

        # Deduplicate while preserving order
        seen = set()
        result = []
        for f in frameworks:
            if f not in seen:
                seen.add(f)
                result.append(f)
        return result

    def detect_package_managers(self, repo_dir: Path) -> list[str]:
        """Detect package managers from lockfiles and config files."""
        managers: list[str] = []

        checks = [
            ("package-lock.json", "npm"),
            ("yarn.lock", "Yarn"),
            ("pnpm-lock.yaml", "pnpm"),
            ("bun.lockb", "Bun"),
            ("requirements.txt", "pip"),
            ("Pipfile", "Pipenv"),
            ("poetry.lock", "Poetry"),
            ("pyproject.toml", "pip/Poetry"),  # Could be either
            ("Cargo.toml", "Cargo"),
            ("go.mod", "Go Modules"),
            ("Gemfile", "Bundler"),
            ("composer.json", "Composer"),
            ("pom.xml", "Maven"),
            ("build.gradle", "Gradle"),
            ("build.gradle.kts", "Gradle"),
            ("Package.swift", "Swift PM"),
            ("pubspec.yaml", "pub (Dart)"),
            ("mix.exs", "Mix (Elixir)"),
        ]

        for filename, manager in checks:
            if (repo_dir / filename).exists():
                if manager not in managers:
                    managers.append(manager)

        # If both pyproject.toml and poetry.lock exist, it's Poetry
        if "pip/Poetry" in managers:
            if (repo_dir / "poetry.lock").exists():
                managers = [m if m != "pip/Poetry" else "Poetry" for m in managers]
            else:
                managers = [m if m != "pip/Poetry" else "pip" for m in managers]

        return managers
