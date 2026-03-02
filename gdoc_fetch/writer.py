"""File writing utilities."""
import re
from pathlib import Path
from datetime import datetime
from typing import Dict


def sanitize_filename(name: str) -> str:
    """
    Sanitize a string to be a valid filename.

    Args:
        name: Raw filename string

    Returns:
        Sanitized filename safe for filesystem
    """
    # Strip and normalize all whitespace (including tabs, newlines, etc)
    name = ' '.join(name.split())

    # Return default if empty or only whitespace
    if not name:
        return 'untitled'

    # Reject path traversal patterns
    if name in ('.', '..'):
        return 'untitled'

    # Remove invalid filesystem characters
    name = re.sub(r'[/\\:*?"<>|]', '', name)

    # Replace spaces with hyphens
    name = name.replace(' ', '-')

    # Convert to lowercase
    name = name.lower()

    # Remove multiple consecutive hyphens
    name = re.sub(r'-+', '-', name)

    # Trim hyphens from start/end
    name = name.strip('-')

    # Remove leading and trailing dots (hidden files and Windows compatibility)
    name = name.strip('.')

    # Limit length
    name = name[:200]

    # Re-strip hyphens and dots after length limiting
    name = name.strip('-.')


    # Check for Windows reserved names
    windows_reserved = {
        'con', 'prn', 'aux', 'nul',
        'com1', 'com2', 'com3', 'com4', 'com5', 'com6', 'com7', 'com8', 'com9',
        'lpt1', 'lpt2', 'lpt3', 'lpt4', 'lpt5', 'lpt6', 'lpt7', 'lpt8', 'lpt9'
    }
    base_name = name.split('.')[0].lower()
    if base_name in windows_reserved:
        name = f'_{name}'

    # Return default if empty after all sanitization
    return name if name else 'untitled'


def create_frontmatter(title: str, source_url: str) -> str:
    """
    Create YAML frontmatter for markdown file.

    Args:
        title: Document title
        source_url: Original Google Doc URL

    Returns:
        YAML frontmatter string
    """
    date = datetime.now().strftime('%Y-%m-%d')

    # Escape YAML special characters to prevent injection
    def escape_yaml_value(value: str) -> str:
        """Escape YAML value by using double quotes and escaping special chars."""
        # Escape backslashes first, then double quotes
        value = value.replace('\\', '\\\\').replace('"', '\\"')
        # Replace newlines and other control characters
        value = value.replace('\n', '\\n').replace('\r', '\\r').replace('\t', '\\t')
        return f'"{value}"'

    title_escaped = escape_yaml_value(title)
    source_escaped = escape_yaml_value(source_url)

    return f"""---
title: {title_escaped}
source: {source_escaped}
fetched: {date}
---

"""


def replace_image_placeholders(markdown: str, image_map: Dict[str, str]) -> str:
    """
    Replace image placeholder IDs with local paths.

    Args:
        markdown: Markdown content with placeholders like INLINE_OBJECT_kix.abc123
        image_map: Mapping of object_id -> local filename

    Returns:
        Markdown with local image paths
    """
    result = markdown

    for object_id, filename in image_map.items():
        placeholder = f"INLINE_OBJECT_{object_id}"
        local_path = f"./images/{filename}"
        result = result.replace(f"![]({placeholder})", f"![]({local_path})")

    return result


def write_document(
    title: str,
    source_url: str,
    markdown: str,
    output_dir: str = "./output"
) -> str:
    """
    Write document to markdown file with frontmatter.

    Args:
        title: Document title
        source_url: Original Google Doc URL
        markdown: Markdown content
        output_dir: Base output directory

    Returns:
        Path to written file
    """
    # Create document directory
    safe_name = sanitize_filename(title)
    doc_dir = Path(output_dir) / safe_name
    doc_dir.mkdir(parents=True, exist_ok=True)

    # Prepare content with frontmatter
    frontmatter = create_frontmatter(title, source_url)
    full_content = frontmatter + markdown

    # Write file
    output_path = doc_dir / f"{safe_name}.md"
    output_path.write_text(full_content, encoding='utf-8')

    return str(output_path)
