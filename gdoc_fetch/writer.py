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

    # Limit length
    name = name[:200]

    # Return default if empty
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
    return f"""---
title: {title}
source: {source_url}
fetched: {date}
---

"""
