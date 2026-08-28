import logging
from pathlib import Path
from app.services.repository.file_scanner import FileScanner
from app.services.repository.file_filter import FileFilter

logging.basicConfig(level=logging.INFO)

scanner = FileScanner()
filter = FileFilter()
result = scanner.scan_repository(Path('../tmp/test_repo'), filter, max_file_size=1 * 1024 * 1024)
print(f'Done! Found {len(result.files)} files')
print(f'Total size: {result.stats["total_size"]}')
for file in result.files:
    if file['size'] > 1 * 1024 * 1024:
        print('Found large file included!', file['path'])
