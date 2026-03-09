"""Unit tests for batch download functionality."""
import pytest

from gdoc_fetch.batch import (
    extract_gdoc_urls_from_markdown,
    extract_gdoc_urls_from_file,
    extract_gdoc_links_from_doc,
    BatchDownloader,
)


def test_extract_gdoc_urls_from_markdown_links():
    """Test extracting URLs from markdown links."""
    markdown = """
# Test Document

[Link 1](https://docs.google.com/document/d/ABC123/edit)
[Link 2](https://docs.google.com/document/d/XYZ789/edit?tab=t.0)
    """

    urls = extract_gdoc_urls_from_markdown(markdown)

    assert len(urls) == 2
    assert 'ABC123' in urls[0]
    assert 'XYZ789' in urls[1]


def test_extract_gdoc_urls_from_plain_text():
    """Test extracting plain URLs from text."""
    markdown = """
Check this doc: https://docs.google.com/document/d/TEST123/edit

And this one: https://docs.google.com/document/d/TEST456/view
    """

    urls = extract_gdoc_urls_from_markdown(markdown)

    assert len(urls) == 2


def test_extract_gdoc_urls_mixed_format():
    """Test extracting both markdown links and plain URLs."""
    markdown = """
[First](https://docs.google.com/document/d/DOC1/edit)

Plain URL: https://docs.google.com/document/d/DOC2/edit

[Second](https://docs.google.com/document/d/DOC3/edit)
    """

    urls = extract_gdoc_urls_from_markdown(markdown)

    assert len(urls) == 3


def test_extract_gdoc_urls_deduplication():
    """Test that duplicate URLs are removed."""
    markdown = """
[Link 1](https://docs.google.com/document/d/SAME/edit)
[Link 2](https://docs.google.com/document/d/SAME/edit)
https://docs.google.com/document/d/SAME/edit
    """

    urls = extract_gdoc_urls_from_markdown(markdown)

    assert len(urls) == 1


def test_extract_gdoc_urls_no_urls():
    """Test with no Google Docs URLs."""
    markdown = """
# Regular Document

Just some text with no Google Docs links.

[Other link](https://example.com)
    """

    urls = extract_gdoc_urls_from_markdown(markdown)

    assert len(urls) == 0


def test_extract_gdoc_urls_from_file(tmp_path):
    """Test extracting URLs from a file."""
    file_path = tmp_path / "test.md"
    file_path.write_text("""
[Doc 1](https://docs.google.com/document/d/TEST1/edit)
[Doc 2](https://docs.google.com/document/d/TEST2/edit)
    """)

    urls = extract_gdoc_urls_from_file(str(file_path))

    assert len(urls) == 2


def test_extract_gdoc_urls_from_file_not_found():
    """Test error when file doesn't exist."""
    with pytest.raises(FileNotFoundError):
        extract_gdoc_urls_from_file("/nonexistent/file.md")


def test_extract_gdoc_links_from_doc():
    """Test extracting links from document structure."""
    doc_structure = {
        'body': {
            'content': [
                {
                    'paragraph': {
                        'elements': [
                            {
                                'textRun': {
                                    'content': 'Check this doc',
                                    'textStyle': {
                                        'link': {
                                            'url': 'https://docs.google.com/document/d/LINKED1/edit'
                                        }
                                    }
                                }
                            }
                        ]
                    }
                },
                {
                    'paragraph': {
                        'elements': [
                            {
                                'textRun': {
                                    'content': 'And this one',
                                    'textStyle': {
                                        'link': {
                                            'url': 'https://docs.google.com/document/d/LINKED2/edit'
                                        }
                                    }
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    urls = extract_gdoc_links_from_doc(doc_structure)

    assert len(urls) == 2
    assert 'LINKED1' in urls[0]
    assert 'LINKED2' in urls[1]


def test_extract_gdoc_links_from_doc_no_links():
    """Test extracting links when there are none."""
    doc_structure = {
        'body': {
            'content': [
                {
                    'paragraph': {
                        'elements': [
                            {
                                'textRun': {
                                    'content': 'Just text'
                                }
                            }
                        ]
                    }
                }
            ]
        }
    }

    urls = extract_gdoc_links_from_doc(doc_structure)

    assert len(urls) == 0


class TestBatchDownloader:
    """Tests for BatchDownloader class."""

    def test_initialization(self):
        """Test initializing batch downloader."""
        downloader = BatchDownloader(max_depth=2)

        assert downloader.max_depth == 2
        assert len(downloader.downloaded) == 0
        assert len(downloader.to_download) == 0

    def test_add_url(self):
        """Test adding URL to download queue."""
        downloader = BatchDownloader()
        downloader.add_url('https://docs.google.com/document/d/TEST123/edit')

        assert downloader.has_pending()
        assert len(downloader.to_download) == 1

    def test_add_url_duplicate(self):
        """Test that duplicates are not added."""
        downloader = BatchDownloader()
        downloader.add_url('https://docs.google.com/document/d/SAME/edit')
        downloader.mark_downloaded('https://docs.google.com/document/d/SAME/edit')
        downloader.add_url('https://docs.google.com/document/d/SAME/edit')

        assert len(downloader.to_download) == 0

    def test_add_url_invalid(self):
        """Test that invalid URLs are skipped."""
        downloader = BatchDownloader()
        downloader.add_url('https://example.com')

        assert not downloader.has_pending()

    def test_get_next(self):
        """Test getting next URL from queue."""
        downloader = BatchDownloader()
        downloader.add_url('https://docs.google.com/document/d/TEST1/edit', depth=0)
        downloader.add_url('https://docs.google.com/document/d/TEST2/edit', depth=1)

        url1, depth1 = downloader.get_next()
        assert 'TEST1' in url1
        assert depth1 == 0

        url2, depth2 = downloader.get_next()
        assert 'TEST2' in url2
        assert depth2 == 1

    def test_get_next_empty(self):
        """Test getting next from empty queue."""
        downloader = BatchDownloader()

        with pytest.raises(IndexError):
            downloader.get_next()

    def test_mark_downloaded(self):
        """Test marking URL as downloaded."""
        downloader = BatchDownloader()
        url = 'https://docs.google.com/document/d/TEST/edit'

        downloader.add_url(url)
        downloader.mark_downloaded(url)

        # Try adding again - should not be added
        downloader.add_url(url)
        assert not downloader.has_pending()

    def test_add_links_from_doc(self):
        """Test adding linked documents."""
        downloader = BatchDownloader(max_depth=2)

        doc_structure = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'Link',
                                        'textStyle': {
                                            'link': {
                                                'url': 'https://docs.google.com/document/d/LINKED/edit'
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        downloader.add_links_from_doc(doc_structure, current_depth=0)

        assert downloader.has_pending()
        url, depth = downloader.get_next()
        assert 'LINKED' in url
        assert depth == 1

    def test_add_links_from_doc_max_depth(self):
        """Test that links are not added beyond max depth."""
        downloader = BatchDownloader(max_depth=1)

        doc_structure = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'content': 'Link',
                                        'textStyle': {
                                            'link': {
                                                'url': 'https://docs.google.com/document/d/LINKED/edit'
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        # At max depth, should not add more links
        downloader.add_links_from_doc(doc_structure, current_depth=1)

        assert not downloader.has_pending()

    def test_get_stats(self):
        """Test getting download statistics."""
        downloader = BatchDownloader()
        downloader.add_url('https://docs.google.com/document/d/TEST1/edit')
        downloader.add_url('https://docs.google.com/document/d/TEST2/edit')
        downloader.mark_downloaded('https://docs.google.com/document/d/TEST1/edit')

        stats = downloader.get_stats()

        assert stats['downloaded'] == 1
        assert stats['pending'] == 1  # TEST1 removed from queue when marked downloaded
        assert stats['total'] == 2

    def test_workflow(self):
        """Test complete workflow."""
        downloader = BatchDownloader(max_depth=1)

        # Add initial URL
        downloader.add_url('https://docs.google.com/document/d/DOC1/edit', depth=0)

        # Process first document
        url1, depth1 = downloader.get_next()
        downloader.mark_downloaded(url1)

        # Simulate finding a linked doc
        doc_structure = {
            'body': {
                'content': [
                    {
                        'paragraph': {
                            'elements': [
                                {
                                    'textRun': {
                                        'textStyle': {
                                            'link': {
                                                'url': 'https://docs.google.com/document/d/DOC2/edit'
                                            }
                                        }
                                    }
                                }
                            ]
                        }
                    }
                ]
            }
        }

        downloader.add_links_from_doc(doc_structure, depth1)

        # Should have second doc in queue
        assert downloader.has_pending()
        url2, depth2 = downloader.get_next()
        assert 'DOC2' in url2
        assert depth2 == 1

        # Mark as downloaded
        downloader.mark_downloaded(url2)

        # No more pending
        assert not downloader.has_pending()

        stats = downloader.get_stats()
        assert stats['downloaded'] == 2
        assert stats['pending'] == 0
