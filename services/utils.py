# services/utils.py
import re

def normalize_custom_id(custom_id: str) -> str:
    """Normalize a custom ID to the format groupindex-author-rowindex."""
    custom_id = str(custom_id).strip().lower()
    match = re.match(r"(\d+)-(.+)", custom_id)
    if match:
        return f"{int(match.group(1))}-{match.group(2)}"
    return custom_id

def sanitize_filename(filename: str) -> str:
    return re.sub(r'[\/*?"<>|]', "_", filename).strip()
