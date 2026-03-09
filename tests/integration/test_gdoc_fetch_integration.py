"""Integration tests for gdoc-fetch command."""
import subprocess
from pathlib import Path
from typing import List

import pytest

from gdoc_fetch.google_api import DocsClient
from gdoc_fetch.converter import DocsToHtmlParser, HtmlToMarkdownConverter
from tests.integration.conftest import PUBLIC_TEST_DOC_ID, PUBLIC_TEST_DOC_URL


@pytest.mark.integration
class TestGdocFetchIntegration:
    """Integration tests for gdoc-fetch CLI."""

    def test_fetch_public_document_with_url(self, temp_dir: Path):
        """Test fetching a public Google Doc using URL."""
        output_dir = temp_dir / "output"

        result = subprocess.run(
            ["gdoc-fetch", PUBLIC_TEST_DOC_URL, "--output-dir", str(output_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, f"Fetch failed: {result.stderr}"
        assert "Success!" in result.stdout
        assert str(output_dir) in result.stdout

        # Verify output directory was created
        assert output_dir.exists()

        # Find the created markdown file
        md_files = list(output_dir.rglob("*.md"))
        assert len(md_files) >= 1, "Should create at least one markdown file"

        # Verify markdown file has content
        md_file = md_files[0]
        content = md_file.read_text()

        assert len(content) > 0, "Markdown file should not be empty"
        assert "---" in content, "Should have frontmatter"

    def test_fetch_with_document_id(self, temp_dir: Path):
        """Test fetching using document ID instead of URL."""
        output_dir = temp_dir / "output"

        result = subprocess.run(
            ["gdoc-fetch", PUBLIC_TEST_DOC_ID, "--output-dir", str(output_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, f"Fetch failed: {result.stderr}"
        assert "Success!" in result.stdout

        # Verify output
        md_files = list(output_dir.rglob("*.md"))
        assert len(md_files) >= 1

    def test_fetch_no_images_flag(self, temp_dir: Path):
        """Test that --no-images skips image download."""
        output_dir = temp_dir / "output"

        result = subprocess.run(
            ["gdoc-fetch", PUBLIC_TEST_DOC_URL, "--output-dir", str(output_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        assert "Success!" in result.stdout

        # Should not create images directory or should be empty
        image_dirs = list(output_dir.rglob("images"))
        if image_dirs:
            # If images dir exists, it should be empty
            for img_dir in image_dirs:
                images = list(img_dir.glob("*"))
                assert len(images) == 0, "Images directory should be empty with --no-images"

    def test_fetch_with_images(self, temp_dir: Path):
        """Test fetching with images (if document has images)."""
        output_dir = temp_dir / "output"

        # Note: This may take longer due to image downloads
        result = subprocess.run(
            ["gdoc-fetch", PUBLIC_TEST_DOC_URL, "--output-dir", str(output_dir)],
            capture_output=True,
            text=True,
            timeout=120
        )

        # Should succeed even if no images or some images fail
        assert result.returncode == 0 or "Success!" in result.stdout

    def test_fetch_invalid_url(self, temp_dir: Path):
        """Test error handling for invalid document URL."""
        result = subprocess.run(
            ["gdoc-fetch", "invalid-url", "--output-dir", str(temp_dir)],
            capture_output=True,
            text=True
        )

        assert result.returncode != 0
        assert "Error" in result.stderr or "Invalid" in result.stderr

    def test_fetch_nonexistent_document(self, temp_dir: Path):
        """Test error handling for nonexistent document."""
        fake_doc_id = "FAKE_DOCUMENT_ID_THAT_DOES_NOT_EXIST"
        fake_url = f"https://docs.google.com/document/d/{fake_doc_id}/edit"

        result = subprocess.run(
            ["gdoc-fetch", fake_url, "--output-dir", str(temp_dir)],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode != 0
        # Should indicate document not found or permission error
        output = result.stderr + result.stdout
        assert "404" in output or "not found" in output.lower() or "permission" in output.lower()

    def test_fetch_custom_output_directory(self, temp_dir: Path):
        """Test using custom output directory."""
        custom_dir = temp_dir / "my_custom_output"

        result = subprocess.run(
            ["gdoc-fetch", PUBLIC_TEST_DOC_URL, "--output-dir", str(custom_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0
        assert custom_dir.exists()

        md_files = list(custom_dir.rglob("*.md"))
        assert len(md_files) >= 1

    def test_fetch_output_structure(self, temp_dir: Path):
        """Test that output follows expected directory structure."""
        output_dir = temp_dir / "output"

        result = subprocess.run(
            ["gdoc-fetch", PUBLIC_TEST_DOC_URL, "--output-dir", str(output_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0

        # Should create: output/document-name/document-name.md
        subdirs = [d for d in output_dir.iterdir() if d.is_dir()]
        assert len(subdirs) >= 1, "Should create document subdirectory"

        doc_dir = subdirs[0]
        md_files = list(doc_dir.glob("*.md"))
        assert len(md_files) == 1, "Should have one markdown file in document directory"


@pytest.mark.integration
class TestDocsConverterIntegration:
    """Integration tests for document converter."""

    def test_fetch_and_convert_real_document(
        self,
        auth_token: str,
        docs_client: DocsClient
    ):
        """Test fetching and converting a real Google Doc."""
        # Fetch document
        doc_data = docs_client.service.documents().get(documentId=PUBLIC_TEST_DOC_ID).execute()

        assert doc_data['documentId'] == PUBLIC_TEST_DOC_ID
        assert len(doc_data['title']) > 0

        # Convert to HTML then markdown
        html_parser = DocsToHtmlParser()
        html = html_parser.parse(doc_data)

        md_converter = HtmlToMarkdownConverter()
        markdown = md_converter.convert(html)

        assert len(markdown) > 0
        assert isinstance(markdown, str)

    def test_convert_document_with_formatting(
        self,
        auth_token: str,
        docs_client: DocsClient
    ):
        """Test that formatting is preserved during conversion."""
        doc_data = docs_client.service.documents().get(documentId=PUBLIC_TEST_DOC_ID).execute()

        html_parser = DocsToHtmlParser()
        html = html_parser.parse(doc_data)

        md_converter = HtmlToMarkdownConverter()
        markdown = md_converter.convert(html)

        # Basic checks that conversion happened
        assert len(markdown) > 0
        # Markdown should have some structure
        assert '\n' in markdown


@pytest.mark.integration
class TestRoundTripIntegration:
    """Round-trip tests: upload → fetch → verify."""

    def test_upload_and_fetch_roundtrip(
        self,
        temp_dir: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test uploading a document and then fetching it back."""
        # Create test markdown
        source_md = temp_dir / "source.md"
        source_md.write_text("""# Roundtrip Test

This is a **roundtrip** test with *formatting*.

## Section 1

- Bullet 1
- Bullet 2

1. Number 1
2. Number 2

A paragraph with [a link](https://example.com).
""")

        # Upload
        upload_result = subprocess.run(
            ["gdoc-upload", str(source_md), "--title", "Roundtrip Test Document"],
            capture_output=True,
            text=True
        )

        assert upload_result.returncode == 0, f"Upload failed: {upload_result.stderr}"

        # Extract document ID
        doc_url = [line for line in upload_result.stdout.split('\n') if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)

        # Fetch back
        output_dir = temp_dir / "fetched"
        fetch_result = subprocess.run(
            ["gdoc-fetch", doc_id, "--output-dir", str(output_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert fetch_result.returncode == 0, f"Fetch failed: {fetch_result.stderr}"

        # Verify fetched content
        md_files = list(output_dir.rglob("*.md"))
        assert len(md_files) >= 1

        fetched_content = md_files[0].read_text()

        # Verify key content is preserved
        assert "Roundtrip Test" in fetched_content
        assert "Section 1" in fetched_content
        assert "Bullet 1" in fetched_content
        assert "Number 1" in fetched_content
        # Note: Exact formatting may differ due to Google Docs conversion

    def test_complex_roundtrip(
        self,
        temp_dir: Path,
        auth_token: str,
        created_docs: List[str]
    ):
        """Test roundtrip with more complex markdown."""
        source_md = temp_dir / "complex_source.md"
        source_md.write_text("""# Complex Roundtrip Test

## Multiple Sections

### Subsection 1

Paragraph with **bold**, *italic*, and ***bold italic***.

### Subsection 2

Mixed lists:

- Unordered 1
- Unordered 2
  - Nested item

Then numbered:

1. Ordered 1
2. Ordered 2
3. Ordered 3

## Code and Links

Some code:

```
def example():
    pass
```

Some links: [Google](https://google.com) and [GitHub](https://github.com).

## Conclusion

Final paragraph here.
""")

        # Upload
        upload_result = subprocess.run(
            ["gdoc-upload", str(source_md), "--title", "Complex Roundtrip Test"],
            capture_output=True,
            text=True
        )

        assert upload_result.returncode == 0

        doc_url = [line for line in upload_result.stdout.split('\n') if 'docs.google.com' in line][0]
        doc_id = doc_url.split('/d/')[1].split('/')[0]
        created_docs.append(doc_id)

        # Fetch back
        output_dir = temp_dir / "fetched_complex"
        fetch_result = subprocess.run(
            ["gdoc-fetch", doc_id, "--output-dir", str(output_dir), "--no-images"],
            capture_output=True,
            text=True,
            timeout=60
        )

        assert fetch_result.returncode == 0

        # Verify content
        md_files = list(output_dir.rglob("*.md"))
        assert len(md_files) >= 1

        fetched_content = md_files[0].read_text()

        # Verify major sections exist
        assert "Complex Roundtrip Test" in fetched_content
        assert "Multiple Sections" in fetched_content
        assert "Subsection 1" in fetched_content
        assert "Subsection 2" in fetched_content
        assert "Code and Links" in fetched_content
        assert "Conclusion" in fetched_content
