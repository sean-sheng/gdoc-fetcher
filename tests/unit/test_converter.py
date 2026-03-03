"""Tests for conversion module."""
import json
from pathlib import Path

from gdoc_fetch.converter import HtmlToMarkdownConverter


def test_html_to_markdown_basic():
    """Test basic HTML to Markdown conversion."""
    converter = HtmlToMarkdownConverter()
    html = "<h1>Title</h1><p>Paragraph text.</p>"

    result = converter.convert(html)

    assert "# Title" in result
    assert "Paragraph text." in result


def test_html_to_markdown_formatting():
    """Test text formatting conversion."""
    converter = HtmlToMarkdownConverter()
    html = "<p>Text with <strong>bold</strong> and <em>italic</em>.</p>"

    result = converter.convert(html)

    assert "**bold**" in result
    assert "*italic*" in result


def test_html_to_markdown_links():
    """Test link conversion."""
    converter = HtmlToMarkdownConverter()
    html = '<p>Check <a href="https://example.com">this link</a>.</p>'

    result = converter.convert(html)

    assert "[this link](https://example.com)" in result


def test_html_to_markdown_lists():
    """Test list conversion."""
    converter = HtmlToMarkdownConverter()
    html = "<ul><li>Item 1</li><li>Item 2</li></ul>"

    result = converter.convert(html)

    assert "- Item 1" in result
    assert "- Item 2" in result


def test_html_to_markdown_images():
    """Test that image placeholders are preserved."""
    converter = HtmlToMarkdownConverter()
    html = '<img src="INLINE_OBJECT_kix.abc123" />'

    result = converter.convert(html)

    assert "INLINE_OBJECT_kix.abc123" in result


def test_docs_to_html_paragraph():
    """Test converting Google Docs paragraph to HTML."""
    from gdoc_fetch.converter import DocsToHtmlParser

    doc_structure = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {"textRun": {"content": "Simple paragraph.\n"}}
                        ]
                    }
                }
            ]
        }
    }

    parser = DocsToHtmlParser()
    result = parser.parse(doc_structure)

    assert "<p>Simple paragraph.</p>" in result


def test_docs_to_html_bold_text():
    """Test converting bold text."""
    from gdoc_fetch.converter import DocsToHtmlParser

    doc_structure = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "textRun": {
                                    "content": "Bold text",
                                    "textStyle": {"bold": True}
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    parser = DocsToHtmlParser()
    result = parser.parse(doc_structure)

    assert "<strong>Bold text</strong>" in result


def test_docs_to_html_bullet_list():
    """Test converting bulleted list."""
    from gdoc_fetch.converter import DocsToHtmlParser

    doc_structure = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [{"textRun": {"content": "Item 1\n"}}],
                        "bullet": {"listId": "list1", "nestingLevel": 0}
                    }
                },
                {
                    "paragraph": {
                        "elements": [{"textRun": {"content": "Item 2\n"}}],
                        "bullet": {"listId": "list1", "nestingLevel": 0}
                    }
                }
            ]
        },
        "lists": {
            "list1": {
                "listProperties": {
                    "nestingLevels": [
                        {"glyphType": "BULLET"}
                    ]
                }
            }
        }
    }

    parser = DocsToHtmlParser()
    result = parser.parse(doc_structure)

    assert "<ul>" in result
    assert "<li>Item 1</li>" in result
    assert "<li>Item 2</li>" in result
    assert "</ul>" in result


def test_docs_to_html_inline_image():
    """Test converting inline image to placeholder."""
    from gdoc_fetch.converter import DocsToHtmlParser

    doc_structure = {
        "body": {
            "content": [
                {
                    "paragraph": {
                        "elements": [
                            {
                                "inlineObjectElement": {
                                    "inlineObjectId": "kix.abc123"
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    parser = DocsToHtmlParser()
    result = parser.parse(doc_structure)

    assert '<img src="INLINE_OBJECT_kix.abc123" />' in result
