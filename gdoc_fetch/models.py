"""Data models for Google Docs structures."""
from dataclasses import dataclass
from typing import List, Dict, Any, Optional, Union


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


# Markdown upload models

@dataclass
class TextRun:
    """Represents a run of text with inline formatting."""
    text: str
    bold: bool = False
    italic: bool = False
    link_url: Optional[str] = None


@dataclass
class Paragraph:
    """Represents a paragraph in markdown."""
    text_runs: List[TextRun]


@dataclass
class Heading:
    """Represents a heading in markdown."""
    level: int  # 1-6
    text_runs: List[TextRun]


@dataclass
class ListItem:
    """Represents a list item in markdown."""
    text_runs: List[TextRun]
    ordered: bool


@dataclass
class CodeBlock:
    """Represents a code block in markdown."""
    code: str
    language: Optional[str] = None


@dataclass
class Image:
    """Represents an image reference in markdown."""
    alt_text: str
    local_path: str


@dataclass
class MarkdownDocument:
    """Represents a parsed markdown document."""
    title: str
    elements: List[Union[Paragraph, Heading, ListItem, CodeBlock, Image]]
