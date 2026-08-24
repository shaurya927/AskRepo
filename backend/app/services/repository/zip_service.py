"""ZIP service: safe extraction with security protections."""

import zipfile
from pathlib import Path

from fastapi import UploadFile

from app.core.security import is_path_traversal


class ZipService:
    """Handles ZIP file validation, safe extraction, and upload saving."""

    def validate_zip(self, file_path: Path) -> None:
        """Verify that a file is a valid ZIP archive."""
        if not zipfile.is_zipfile(file_path):
            raise ValueError("Invalid ZIP file")

    def extract_zip(
        self,
        file_path: Path,
        target_dir: Path,
        max_size_mb: int,
        max_files: int,
    ) -> Path:
        """Safely extract a ZIP file with security checks.
        
        Protections:
        - Path traversal detection (../ and absolute paths)
        - Symlink rejection
        - Cumulative extracted size limit
        - File count limit
        """
        self.validate_zip(file_path)

        max_size_bytes = max_size_mb * 1024 * 1024
        extracted_size = 0
        file_count = 0

        with zipfile.ZipFile(file_path, "r") as zf:
            for info in zf.infolist():
                # Security: reject path traversal
                if is_path_traversal(info.filename):
                    raise ValueError(f"Path traversal detected in ZIP: {info.filename}")

                # Skip directories
                if info.is_dir():
                    continue

                # Security: reject symlinks (external_attr check)
                # Unix symlinks have the mode 0xA000 in the upper 16 bits
                unix_attrs = info.external_attr >> 16
                if unix_attrs != 0 and (unix_attrs & 0xF000) == 0xA000:
                    raise ValueError(f"Symlink detected in ZIP: {info.filename}")

                # Enforce file count limit
                file_count += 1
                if file_count > max_files:
                    raise ValueError(
                        f"ZIP contains more than {max_files} files"
                    )

                # Enforce cumulative size limit
                extracted_size += info.file_size
                if extracted_size > max_size_bytes:
                    raise ValueError(
                        f"Extracted size exceeds {max_size_mb}MB limit"
                    )

                # Extract safely
                target_path = target_dir / info.filename
                target_path.parent.mkdir(parents=True, exist_ok=True)
                with zf.open(info) as source, open(target_path, "wb") as dest:
                    dest.write(source.read())

        return target_dir

    async def save_upload(self, upload_file: UploadFile, target_dir: Path) -> Path:
        """Save an uploaded file to disk safely."""
        # Sanitize filename
        filename = upload_file.filename or "upload.zip"
        safe_name = filename.replace("/", "_").replace("\\", "_")
        file_path = target_dir / safe_name

        content = await upload_file.read()
        with open(file_path, "wb") as f:
            f.write(content)

        return file_path
