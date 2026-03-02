"""Tests for file writer module."""
import pytest
from pathlib import Path
from gdoc_fetch.writer import sanitize_filename, create_frontmatter
import tempfile
import shutil


def test_sanitize_filename_basic():
    """Test basic filename sanitization."""
    assert sanitize_filename("My Document") == "my-document"


def test_sanitize_filename_special_chars():
    """Test removal of invalid filesystem characters."""
    assert sanitize_filename("Doc/with\\:invalid*chars?") == "docwithinvalidchars"


def test_sanitize_filename_multiple_spaces():
    """Test space normalization."""
    assert sanitize_filename("Document   with    spaces") == "document-with-spaces"


def test_sanitize_filename_long_name():
    """Test length limiting."""
    long_name = "a" * 250
    result = sanitize_filename(long_name)
    assert len(result) <= 200


def test_sanitize_filename_empty():
    """Test empty input returns default."""
    assert sanitize_filename("") == "untitled"
    assert sanitize_filename("   ") == "untitled"


def test_sanitize_filename_only_special_chars():
    """Test input with only special characters."""
    assert sanitize_filename("///:::***") == "untitled"


def test_sanitize_filename_leading_trailing_hyphens():
    """Test removal of leading/trailing hyphens."""
    assert sanitize_filename("-document-") == "document"


def test_sanitize_filename_whitespace_only():
    """Test that whitespace-only strings return default."""
    assert sanitize_filename("\n\t\r") == "untitled"
    assert sanitize_filename("\n") == "untitled"
    assert sanitize_filename("\t") == "untitled"


def test_sanitize_filename_whitespace_normalization():
    """Test normalization of various whitespace characters."""
    assert sanitize_filename("Doc\twith\ttabs") == "doc-with-tabs"
    assert sanitize_filename("Doc\nwith\nnewlines") == "doc-with-newlines"
    assert sanitize_filename("Doc\r\nwith\r\nCRLF") == "doc-with-crlf"
    assert sanitize_filename("Doc  \t\n  mixed   whitespace") == "doc-mixed-whitespace"


def test_sanitize_filename_path_traversal():
    """Test prevention of path traversal patterns."""
    assert sanitize_filename("..") == "untitled"
    assert sanitize_filename(".") == "untitled"


def test_sanitize_filename_hidden_files():
    """Test removal of leading dots to prevent hidden files."""
    assert sanitize_filename(".hidden") == "hidden"
    assert sanitize_filename("..hidden") == "hidden"
    assert sanitize_filename("...multiple") == "multiple"


def test_sanitize_filename_windows_reserved_names():
    """Test handling of Windows reserved names."""
    # Device names
    assert sanitize_filename("CON") == "_con"
    assert sanitize_filename("PRN") == "_prn"
    assert sanitize_filename("AUX") == "_aux"
    assert sanitize_filename("NUL") == "_nul"

    # COM ports
    assert sanitize_filename("COM1") == "_com1"
    assert sanitize_filename("com5") == "_com5"
    assert sanitize_filename("COM9") == "_com9"

    # LPT ports
    assert sanitize_filename("LPT1") == "_lpt1"
    assert sanitize_filename("lpt5") == "_lpt5"
    assert sanitize_filename("LPT9") == "_lpt9"

    # With extensions
    assert sanitize_filename("CON.txt") == "_con.txt"
    assert sanitize_filename("PRN.md") == "_prn.md"


def test_sanitize_filename_hyphen_after_length_limit():
    """Test that hyphens are stripped after length limiting."""
    # Create a name that will have a hyphen at position 200
    long_name = "a" * 199 + "-" + "b" * 50
    result = sanitize_filename(long_name)
    assert len(result) <= 200
    assert not result.endswith("-")


def test_sanitize_filename_combination_edge_cases():
    """Test combination of multiple edge cases."""
    # Whitespace + special chars + path traversal
    assert sanitize_filename("  ..  ") == "untitled"

    # Hidden file + special chars
    assert sanitize_filename(".my/doc:name") == "mydocname"

    # Windows reserved + special chars - CON:file becomes confile which is not reserved
    # But CON alone would be reserved
    assert sanitize_filename("CON:file") == "confile"
    assert sanitize_filename("CON: ") == "_con"

    # Leading dots + hyphens
    assert sanitize_filename("...---my-doc---...") == "my-doc"


def test_create_frontmatter():
    """Test YAML frontmatter generation."""
    result = create_frontmatter("Test Document", "https://docs.google.com/document/d/123/edit")

    assert "---" in result
    assert 'title: "Test Document"' in result
    assert 'source: "https://docs.google.com/document/d/123/edit"' in result
    assert "fetched:" in result
    assert result.endswith("---\n\n")


def test_create_frontmatter_basic():
    """Test basic frontmatter creation."""
    result = create_frontmatter("Test Doc", "https://example.com")
    assert 'title: "Test Doc"' in result
    assert 'source: "https://example.com"' in result
    assert "fetched:" in result
    assert result.startswith("---")
    assert "---\n\n" in result


def test_create_frontmatter_yaml_injection_newline():
    """Test prevention of YAML injection via newlines."""
    malicious_title = "My Doc\nsource: evil.com"
    result = create_frontmatter(malicious_title, "https://example.com")

    # Should escape the newline, not create a new YAML field
    assert "\\n" in result
    assert 'title: "My Doc\\nsource: evil.com"' in result
    assert 'source: "https://example.com"' in result


def test_create_frontmatter_yaml_injection_quotes():
    """Test prevention of YAML injection via quotes."""
    malicious_title = 'My Doc"\nsource: evil.com\ntitle: "Real Title'
    result = create_frontmatter(malicious_title, "https://example.com")

    # Should escape quotes and newlines
    assert '\\"' in result
    assert '\\n' in result


def test_create_frontmatter_special_chars():
    """Test handling of various special characters."""
    title = "Doc: with * special & chars # test"
    result = create_frontmatter(title, "https://example.com?param=value")

    # Should be properly quoted
    assert 'title: "Doc: with * special & chars # test"' in result
    assert 'source: "https://example.com?param=value"' in result


def test_create_frontmatter_control_characters():
    """Test handling of control characters."""
    title = "Doc\twith\ttabs"
    url = "https://example.com"
    result = create_frontmatter(title, url)

    # Should escape control characters
    assert "\\t" in result
    assert 'title: "Doc\\twith\\ttabs"' in result


def test_create_frontmatter_backslashes():
    """Test handling of backslashes."""
    title = "Path\\to\\document"
    result = create_frontmatter(title, "https://example.com")

    # Should escape backslashes
    assert "\\\\" in result
    assert 'title: "Path\\\\to\\\\document"' in result


def test_write_document(tmp_path):
    """Test writing document with frontmatter."""
    from gdoc_fetch.writer import write_document

    output_dir = tmp_path / "output"
    markdown_content = "# Test\n\nSome content."

    result_path = write_document(
        title="Test Doc",
        source_url="https://docs.google.com/document/d/123/edit",
        markdown=markdown_content,
        output_dir=str(output_dir)
    )

    assert Path(result_path).exists()
    content = Path(result_path).read_text()
    assert 'title: "Test Doc"' in content
    assert "# Test" in content
    assert "Some content." in content


def test_write_document_creates_directory(tmp_path):
    """Test that write_document creates output directory."""
    from gdoc_fetch.writer import write_document

    output_dir = tmp_path / "output"
    assert not output_dir.exists()

    write_document(
        title="Test",
        source_url="https://example.com",
        markdown="content",
        output_dir=str(output_dir)
    )

    assert output_dir.exists()
    assert (output_dir / "test").exists()


def test_replace_image_placeholders():
    """Test replacing image placeholders with local paths."""
    from gdoc_fetch.writer import replace_image_placeholders

    markdown = """
# Document

![](INLINE_OBJECT_kix.abc123)

Some text.

![](INLINE_OBJECT_kix.def456)
"""

    image_map = {
        "kix.abc123": "image-001.png",
        "kix.def456": "image-002.jpg"
    }

    result = replace_image_placeholders(markdown, image_map)

    assert "![](./images/image-001.png)" in result
    assert "![](./images/image-002.jpg)" in result
    assert "INLINE_OBJECT" not in result


def test_replace_image_placeholders_no_images():
    """Test markdown without images passes through unchanged."""
    from gdoc_fetch.writer import replace_image_placeholders

    markdown = "# Just text\n\nNo images here."
    result = replace_image_placeholders(markdown, {})

    assert result == markdown
