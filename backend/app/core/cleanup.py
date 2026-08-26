"""Startup cleanup service — removes orphaned temp directories."""

from __future__ import annotations

import logging
import shutil
import time
from pathlib import Path

logger = logging.getLogger(__name__)


def cleanup_stale_workspaces(temp_path: str, max_age_hours: int = 1) -> int:
    """Remove temp directories older than max_age_hours.

    Returns the number of directories cleaned up.
    """
    temp_dir = Path(temp_path)
    if not temp_dir.exists():
        return 0

    cutoff = time.time() - (max_age_hours * 3600)
    cleaned = 0

    for child in temp_dir.iterdir():
        if not child.is_dir():
            continue
        try:
            # Use modification time as proxy for activity
            mtime = child.stat().st_mtime
            if mtime < cutoff:
                shutil.rmtree(child, ignore_errors=True)
                cleaned += 1
                logger.info("Cleaned up stale workspace: %s", child.name)
        except Exception as e:
            logger.warning("Failed to clean %s: %s", child.name, e)

    if cleaned:
        logger.info("Cleaned %d stale workspace(s) from %s", cleaned, temp_path)
    return cleaned


def is_safe_cleanup_path(path: Path, base_path: str) -> bool:
    """Verify a path is safely inside the expected base directory.

    Prevents accidental deletion outside the temp workspace.
    """
    try:
        resolved = path.resolve()
        base_resolved = Path(base_path).resolve()
        return str(resolved).startswith(str(base_resolved))
    except (OSError, ValueError):
        return False
