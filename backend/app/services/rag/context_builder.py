"""Context builder — assembles LLM prompt from retrieved contexts."""

from __future__ import annotations

from app.services.rag.retriever import RetrievedContext


SYSTEM_PROMPT = """You are AskRepo, an expert AI code analyst. You analyze software repositories and answer questions grounded in the actual source code.

Rules:
1. ONLY use information from the provided source context. Never invent file names, function names, or line numbers.
2. When referencing code, cite the source file and line numbers in this exact format: `file_path:start_line-end_line`
3. Be precise and technical. Developers are your audience.
4. If the context doesn't contain enough information to answer, say so clearly.
5. Structure your answers with markdown for readability.
6. When explaining code, include relevant snippets from the context.
"""


def build_context(
    query: str,
    contexts: list[RetrievedContext],
    repo_summary: str,
    max_chars: int = 12000,
) -> tuple[str, str]:
    """Build the system prompt and user prompt for the LLM.

    Returns (system_prompt, user_prompt).
    """
    # Build context block
    context_parts: list[str] = []
    total_chars = 0

    # Always include repo summary first
    if repo_summary:
        header = f"=== Repository Summary ===\n{repo_summary}\n"
        context_parts.append(header)
        total_chars += len(header)

    # Add retrieved contexts, ordered by relevance
    for ctx in contexts:
        location = f"{ctx.file_path}"
        if ctx.start_line and ctx.end_line:
            location += f" (lines {ctx.start_line}-{ctx.end_line})"
        if ctx.symbol_name:
            location += f" [{ctx.symbol_type}: {ctx.symbol_name}]"

        block = f"=== Source: {location} ===\n{ctx.text}\n"

        if total_chars + len(block) > max_chars:
            break
        context_parts.append(block)
        total_chars += len(block)

    context_text = "\n".join(context_parts)

    user_prompt = f"""Here is the relevant source code and documentation from the repository:

{context_text}

---

User question: {query}

Please answer the question based on the source code above. Cite specific files and line numbers."""

    return SYSTEM_PROMPT, user_prompt


def extract_sources(contexts: list[RetrievedContext]) -> list[dict]:
    """Extract source citations from retrieved contexts."""
    seen = set()
    sources = []
    for ctx in contexts:
        key = (ctx.file_path, ctx.start_line, ctx.end_line)
        if key in seen:
            continue
        seen.add(key)
        sources.append({
            "file_path": ctx.file_path,
            "start_line": ctx.start_line,
            "end_line": ctx.end_line,
            "symbol_name": ctx.symbol_name,
        })
    return sources


def build_repo_summary(stats: dict) -> str:
    """Build a concise repository summary for LLM context."""
    parts = []
    if stats.get("name"):
        parts.append(f"Repository: {stats['name']}")
    if stats.get("primary_language"):
        parts.append(f"Primary language: {stats['primary_language']}")
    if stats.get("total_files"):
        parts.append(f"Files: {stats['total_files']}")
    if stats.get("total_lines"):
        parts.append(f"Lines of code: {stats['total_lines']}")
    if stats.get("frameworks"):
        parts.append(f"Frameworks: {', '.join(stats['frameworks'])}")
    if stats.get("package_managers"):
        parts.append(f"Package managers: {', '.join(stats['package_managers'])}")
    if stats.get("total_functions"):
        parts.append(f"Functions: {stats['total_functions']}, Classes: {stats.get('total_classes', 0)}, Methods: {stats.get('total_methods', 0)}")
    return "\n".join(parts)
