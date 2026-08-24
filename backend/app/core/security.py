import os
from pathlib import Path
import re

BINARY_EXTENSIONS = {
    ".png", ".jpg", ".jpeg", ".gif", ".webp", ".mp4", ".mp3", ".zip", ".tar", ".gz",
    ".exe", ".dll", ".so", ".o", ".pyc", ".class", ".woff", ".woff2", ".ttf", ".eot",
    ".ico", ".svg", ".pdf", ".doc", ".docx", ".xls", ".xlsx"
}

def is_path_traversal(path: str) -> bool:
    if os.path.isabs(path) or ".." in path.split(os.sep) or ".." in path.split("/"):
        return True
    return False

def sanitize_filename(name: str) -> str:
    return re.sub(r'[^a-zA-Z0-9_.-]', '_', name)

def is_binary_extension(ext: str) -> bool:
    return ext.lower() in BINARY_EXTENSIONS

def is_symlink(path: Path) -> bool:
    return path.is_symlink()
