"""Integration tests for gdoc-upload command."""
import subprocess
import tempfile
from pathlib import Path
from typing import List

import pytest

from gdoc_fetch.google_api import DocsClient
from gdoc_fetch.markdown_parser import MarkdownParser
from gdoc_fetch.docs_builder import DocsRequestBuilder


@pytest.mark.integration
class TestGdocUploadIntegration:
    """Integration tests for gdoc-upload CLI."""

    def test_upload_simple_markdown(
        self,
        sample_markdown: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test uploading a simple markdown file."""
        # Run gdoc-upload command
        result = subprocess.run(
            ["gdoc-upload", str(sample_markdown), "--title", "Integration Test Simple"],
            capture_output=True,
            text=True
        )

        # Verify command succeeded
        assert result.returncode == 0, f"Upload failed: {result.stderr}"
        assert "Success!" in result.stdout
        assert "docs.google.com" in result.stdout

        # Extract document ID from output
        output_lines = result.stdout.split('\n')
        doc_url = [line for line in output_lines if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)

        # Verify document was created
        docs_client = DocsClient(token=auth_token)
        doc_data = docs_client.service.documents().get(documentId=doc_id).execute()

        assert doc_data['title'] == "Integration Test Simple"
        assert 'body' in doc_data

    def test_upload_with_no_images_flag(
        self,
        sample_markdown: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test uploading markdown with --no-images flag."""
        result = subprocess.run(
            ["gdoc-upload", str(sample_markdown), "--title", "Integration Test No Images", "--no-images"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Upload failed: {result.stderr}"
        assert "Success!" in result.stdout

        # Extract document ID
        doc_url = [line for line in result.stdout.split('\n') if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)

    def test_upload_complex_markdown(
        self,
        temp_dir: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test uploading markdown with various features."""
        # Create complex markdown file
        complex_md = temp_dir / "complex.md"
        complex_md.write_text("""# Complex Test Document

## Introduction

This document tests **various** markdown features including *italic* and ***bold italic***.

## Lists

### Bullet List

- First item
- Second item with **bold**
- Third item with *italic*
  - Nested item
  - Another nested

### Numbered List

1. First numbered
2. Second numbered
3. Third numbered

## Code Blocks

```python
def test_function():
    return "Hello, World!"
```

## Links

Check out [Google](https://www.google.com) for more information.

## Formatted Text

Regular text with **bold**, *italic*, and [links](https://example.com).

## Conclusion

This is the end of the test document.
""")

        # Upload the document
        result = subprocess.run(
            ["gdoc-upload", str(complex_md), "--title", "Integration Test Complex"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Upload failed: {result.stderr}"
        assert "Success!" in result.stdout

        # Extract and verify
        doc_url = [line for line in result.stdout.split('\n') if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)

        # Verify document structure
        docs_client = DocsClient(token=auth_token)
        doc_data = docs_client.service.documents().get(documentId=doc_id).execute()

        assert doc_data['title'] == "Integration Test Complex"

        # Check that content was inserted
        content = doc_data['body']['content']
        assert len(content) > 10  # Should have many content elements

    def test_upload_markdown_with_title_extraction(
        self,
        temp_dir: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test that title is extracted from H1 when not specified."""
        md_file = temp_dir / "auto_title.md"
        md_file.write_text("""# Auto Extracted Title

This document should use the H1 as its title.
""")

        result = subprocess.run(
            ["gdoc-upload", str(md_file)],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Upload failed: {result.stderr}"

        # Extract document ID
        doc_url = [line for line in result.stdout.split('\n') if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)

        # Verify title
        docs_client = DocsClient(token=auth_token)
        doc_data = docs_client.service.documents().get(documentId=doc_id).execute()

        assert doc_data['title'] == "Auto Extracted Title"

    def test_upload_nonexistent_file(self):
        """Test error handling for nonexistent file."""
        result = subprocess.run(
            ["gdoc-upload", "/nonexistent/file.md"],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "File not found" in result.stderr or "Error" in result.stderr

    def test_upload_markdown_special_characters(
        self,
        temp_dir: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test uploading markdown with special characters."""
        md_file = temp_dir / "special_chars.md"
        md_file.write_text("""# Special Characters Test

Testing special characters: & < > " '

Testing unicode: 你好 こんにちは مرحبا

Testing symbols: © ® ™ € £ ¥
""")

        result = subprocess.run(
            ["gdoc-upload", str(md_file), "--title", "Integration Test Special Chars"],
            capture_output=True,
            text=True
        )

        assert result.returncode == 0, f"Upload failed: {result.stderr}"

        doc_url = [line for line in result.stdout.split('\n') if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)


@pytest.mark.integration
class TestMarkdownParserIntegration:
    """Integration tests for MarkdownParser with real files."""

    def test_parse_all_features(self, sample_markdown: Path):
        """Test parsing markdown with all supported features."""
        parser = MarkdownParser()
        doc = parser.parse_file(str(sample_markdown))

        assert doc.title == "Test Document"
        assert len(doc.elements) > 0

        # Verify different element types exist
        from gdoc_fetch.models import Heading, Paragraph, ListItem, CodeBlock, Image

        has_heading = any(isinstance(e, Heading) for e in doc.elements)
        has_paragraph = any(isinstance(e, Paragraph) for e in doc.elements)
        has_list = any(isinstance(e, ListItem) for e in doc.elements)
        has_code = any(isinstance(e, CodeBlock) for e in doc.elements)
        has_image = any(isinstance(e, Image) for e in doc.elements)

        assert has_heading, "Should have headings"
        assert has_paragraph, "Should have paragraphs"
        assert has_list, "Should have list items"
        assert has_code, "Should have code blocks"
        assert has_image, "Should have images"


@pytest.mark.integration
class TestDocsBuilderIntegration:
    """Integration tests for DocsRequestBuilder."""

    def test_build_and_upload_requests(
        self,
        sample_markdown: Path,
        auth_token: str,
        docs_client: DocsClient,
        created_docs: List[str]
    ):
        """Test building requests from markdown and uploading."""
        # Parse markdown
        parser = MarkdownParser()
        doc = parser.parse_file(str(sample_markdown))

        # Build requests
        builder = DocsRequestBuilder()
        requests = builder.build_content_requests(doc.elements)

        assert len(requests) > 0

        # Create document
        doc_id = docs_client.create_document("Integration Test Builder")
        created_docs.append(doc_id)

        # Upload requests
        docs_client.update_document_content(doc_id, requests)

        # Verify document has content
        doc_data = docs_client.service.documents().get(documentId=doc_id).execute()
        content = doc_data['body']['content']

        assert len(content) > 1  # More than just the initial paragraph
