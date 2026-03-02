"""Tests for file writer module."""
import pytest
from pathlib import Path
from gdoc_fetch.writer import sanitize_filename, create_frontmatter


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
