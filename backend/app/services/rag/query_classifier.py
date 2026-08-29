"""Query classifier — routes questions to the right retrieval strategy."""

from __future__ import annotations

import re

# Keyword patterns for each category
_CODE_PATTERNS = [
    r"\bfunction\b", r"\bmethod\b", r"\bclass\b", r"\binterface\b",
    r"\bdef\b", r"\bconstructor\b", r"\bimport\b", r"\breturn\b",
    r"what does [\w_.()]+\s+do", r"explain [\w_.]+",
    r"show me [\w_.]+",
]

_ARCHITECTURE_PATTERNS = [
    r"\barchitecture\b", r"\bhow does .+ work\b", r"\bdata flow\b",
    r"\bflow\b", r"\binteract\b", r"\bwork together\b",
    r"\bcomponent\b", r"\bmodule\b", r"\bservice\b", r"\blayer\b",
    r"\brouting\b", r"\bmiddleware\b", r"\bpipeline\b",
    r"\bhow is .+ organized\b", r"\bstructure\b",
    r"\bhow does .+ work\b",  # extra weight — ask twice
]

_REPOSITORY_PATTERNS = [
    r"\bwhat is this\b", r"\bproject\b", r"\boverview\b",
    r"\btechnolog", r"\bstack\b", r"\bframework\b",
    r"\bwhat does this .+ do\b", r"\bpurpose\b",
    r"\breadme\b", r"\bdescri", r"\bexplain.+project\b",
    r"\bworking of this project\b", r"\bonboard\b", r"\bsimple words\b",
]

_HISTORICAL_PATTERNS = [
    r"\bwhy was\b", r"\bwhen did\b", r"\bhistory\b",
    r"\bchanged\b", r"\bintroduced\b", r"\bevolved\b",
    r"\bcommit\b", r"\bgit\b", r"\bblame\b",
    r"\bwho wrote\b", r"\bwho added\b",
]


def classify_query(query: str) -> str:
    """Classify a user query into a retrieval category.

    Returns one of: 'code', 'architecture', 'repository', 'historical', 'general'.
    """
    q = query.lower().strip()

    # Score each category
    scores = {
        "code": _score(q, _CODE_PATTERNS),
        "architecture": _score(q, _ARCHITECTURE_PATTERNS),
        "repository": _score(q, _REPOSITORY_PATTERNS),
        "historical": _score(q, _HISTORICAL_PATTERNS),
    }

    best = max(scores, key=scores.get)  # type: ignore[arg-type]
    if scores[best] > 0:
        return best
    return "general"


def _score(text: str, patterns: list[str]) -> int:
    """Count how many patterns match the text."""
    return sum(1 for p in patterns if re.search(p, text, re.IGNORECASE))
