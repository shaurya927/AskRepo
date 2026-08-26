"""Architecture detector — classifies files into architectural categories using deterministic heuristics."""

from __future__ import annotations

import re
from pathlib import PurePosixPath


# Path patterns → category mapping
_PATH_RULES: list[tuple[str, list[str]]] = [
    ("frontend", [
        r"(^|\/)src\/(components|pages|views|layouts|screens)\b",
        r"\.(tsx|jsx)$",
        r"(^|\/)public\/",
    ]),
    ("api", [
        r"(^|\/)api\/(endpoints|routes|views)\b",
        r"(^|\/)routes\/",
        r"(^|\/)controllers\/",
        r"(^|\/)endpoints\/",
    ]),
    ("services", [
        r"(^|\/)services?\/",
    ]),
    ("models", [
        r"(^|\/)models?\/",
        r"(^|\/)entities\/",
        r"(^|\/)schemas?\/",
    ]),
    ("database", [
        r"(^|\/)migrations?\/",
        r"(^|\/)database\/",
        r"(^|\/)db\/",
    ]),
    ("authentication", [
        r"(^|\/)(auth|login|oauth|jwt|session)\b",
    ]),
    ("tests", [
        r"(^|\/)tests?\/",
        r"(^|\/)__tests__\/",
        r"\.test\.(ts|tsx|js|jsx|py)$",
        r"\.spec\.(ts|tsx|js|jsx)$",
        r"test_\w+\.py$",
    ]),
    ("utilities", [
        r"(^|\/)utils?\/",
        r"(^|\/)helpers?\/",
        r"(^|\/)lib\/",
        r"(^|\/)common\/",
        r"(^|\/)shared\/",
    ]),
    ("infrastructure", [
        r"Dockerfile",
        r"docker-compose",
        r"(^|\/)\.github\/",
        r"(^|\/)\.gitlab-ci",
        r"(^|\/)k8s\/",
        r"(^|\/)terraform\/",
        r"(^|\/)helm\/",
        r"Jenkinsfile",
    ]),
    ("config", [
        r"(^|\/)config\/",
        r"(^|\/)core\/config",
        r"\.(env|ini|cfg|conf|yaml|yml|toml)$",
        r"(^|\/)(settings|config)\.(py|ts|js)$",
        r"tsconfig\.json$",
        r"package\.json$",
        r"pyproject\.toml$",
    ]),
]

# Import patterns → category mapping (supplements path rules)
_IMPORT_RULES: dict[str, list[str]] = {
    "frontend": ["react", "vue", "angular", "svelte", "next"],
    "backend": ["fastapi", "flask", "django", "express", "spring", "gin"],
    "database": ["sqlalchemy", "mongoose", "prisma", "typeorm", "sequelize", "knex"],
    "authentication": ["passport", "jwt", "oauth", "bcrypt"],
}


class ArchitectureDetector:
    """Classifies files into architectural categories using deterministic heuristics."""

    def detect(
        self,
        files: list[dict],
        symbols: list[dict] | None = None,
        imports: list[dict] | None = None,
    ) -> dict[str, list[str]]:
        """Classify files into architecture categories.

        Args:
            files: List of file dicts with 'path' key.
            symbols: Optional symbols for enrichment.
            imports: Optional imports for import-based classification.

        Returns:
            Dict mapping category → list of file paths.
        """
        result: dict[str, list[str]] = {}
        classified: set[str] = set()

        # Build per-file import set for import-based detection
        file_imports: dict[str, set[str]] = {}
        if imports:
            for imp in imports:
                fp = imp.get("file_path", "")
                src = imp.get("source", "").lower()
                file_imports.setdefault(fp, set()).add(src)

        for f in files:
            fp = f.get("path", "")
            if not fp:
                continue

            category = self._classify_by_path(fp)

            # If path didn't match, try import-based classification
            if not category and fp in file_imports:
                category = self._classify_by_imports(file_imports[fp])

            # Backend catch-all for Python/Java server files not caught by path rules
            if not category:
                lang = f.get("language", "")
                if lang in ("Python", "Java", "Go", "Rust", "C#"):
                    category = "backend"

            if category:
                result.setdefault(category, []).append(fp)
                classified.add(fp)

        return result

    def get_architecture_summary(self, detection: dict[str, list[str]]) -> dict:
        """Generate a summary of the architecture detection."""
        total_files = sum(len(files) for files in detection.values())
        categories = []
        for cat, files in sorted(detection.items(), key=lambda x: -len(x[1])):
            categories.append({
                "name": cat,
                "file_count": len(files),
                "percentage": round(len(files) / total_files * 100, 1) if total_files > 0 else 0,
                "sample_files": files[:5],
            })
        return {
            "total_classified": total_files,
            "categories": categories,
        }

    def _classify_by_path(self, file_path: str) -> str | None:
        """Classify a file based on its path."""
        # Normalize to forward slashes
        fp = file_path.replace("\\", "/")
        for category, patterns in _PATH_RULES:
            for pattern in patterns:
                if re.search(pattern, fp, re.IGNORECASE):
                    return category
        return None

    def _classify_by_imports(self, imports: set[str]) -> str | None:
        """Classify a file based on its imports."""
        for category, keywords in _IMPORT_RULES.items():
            for kw in keywords:
                if any(kw in imp for imp in imports):
                    return category
        return None
