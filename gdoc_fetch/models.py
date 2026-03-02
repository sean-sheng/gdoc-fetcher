"""Data models for Google Docs structures."""
from dataclasses import dataclass
from typing import List, Dict, Any


@dataclass
class InlineObject:
    """Represents an inline object (typically an image) in a Google Doc."""
    object_id: str
    image_url: str
    content_type: str


@dataclass
class Tab:
    """Represents a tab in a Google Doc."""
    tab_id: str
    title: str
    content: List[Any]  # List of structural elements


@dataclass
class Document:
    """Represents a Google Doc with all its content."""
    doc_id: str
    title: str
    tabs: List[Tab]
    inline_objects: Dict[str, InlineObject]
