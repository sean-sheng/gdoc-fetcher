"""Batch download and recursive link following for gdoc-fetch."""
import re
from pathlib import Path
from typing import Set, List, Tuple
from urllib.parse import urlparse

from gdoc_common.utils import extract_doc_id


def extract_gdoc_urls_from_markdown(markdown_content: str) -> List[str]:
    """
    Extract all Google Docs URLs from markdown content.

    Supports both markdown links [text](url) and plain URLs.

    Args:
        markdown_content: Markdown text content

    Returns:
        List of Google Docs URLs
    """
    urls = []

    # Pattern for markdown links: [text](url)
    markdown_links = re.findall(r'\[([^\]]+)\]\(([^\)]+)\)', markdown_content)
    for _, url in markdown_links:
        if 'docs.google.com/document' in url:
            urls.append(url)

    # Pattern for plain URLs
    plain_urls = re.findall(
        r'https://docs\.google\.com/document/d/[a-zA-Z0-9_-]+[^\s\)]*',
        markdown_content
    )
    urls.extend(plain_urls)

    # Remove duplicates while preserving order
    seen = set()
    unique_urls = []
    for url in urls:
        # Normalize URL by removing fragments and query params for duplicate detection
        doc_id = extract_doc_id(url)
        if doc_id and doc_id not in seen:
            seen.add(doc_id)
            unique_urls.append(url)

    return unique_urls


def extract_gdoc_urls_from_file(file_path: str) -> List[str]:
    """
    Extract all Google Docs URLs from a markdown file.

    Args:
        file_path: Path to markdown file

    Returns:
        List of Google Docs URLs

    Raises:
        FileNotFoundError: If file doesn't exist
        ValueError: If file is not readable
    """
    path = Path(file_path)

    if not path.exists():
        raise FileNotFoundError(f"File not found: {file_path}")

    if not path.is_file():
        raise ValueError(f"Not a file: {file_path}")

    try:
        content = path.read_text(encoding='utf-8')
    except Exception as e:
        raise ValueError(f"Failed to read file: {e}")

    return extract_gdoc_urls_from_markdown(content)


def extract_gdoc_links_from_doc(doc_structure: dict) -> List[str]:
    """
    Extract Google Docs URLs from a Google Doc structure.

    Searches through all text elements for Google Docs links.

    Args:
        doc_structure: Google Docs API response structure

    Returns:
        List of Google Docs URLs found in the document
    """
    urls = []

    body = doc_structure.get('body', {})
    content = body.get('content', [])

    def extract_from_element(element):
        """Recursively extract URLs from element."""
        # Check paragraph elements
        paragraph = element.get('paragraph', {})
        for para_element in paragraph.get('elements', []):
            text_run = para_element.get('textRun', {})
            text_style = text_run.get('textStyle', {})
            link = text_style.get('link', {})
            url = link.get('url', '')

            if url and 'docs.google.com/document' in url:
                urls.append(url)

        # Check table elements
        table = element.get('table', {})
        for row in table.get('tableRows', []):
            for cell in row.get('tableCells', []):
                for cell_content in cell.get('content', []):
                    extract_from_element(cell_content)

    for element in content:
        extract_from_element(element)

    return urls


class BatchDownloader:
    """
    Batch download Google Docs with recursive link following.

    Features:
    - Download multiple docs from a list of URLs
    - Recursively follow links to other Google Docs
    - Track downloaded docs to avoid duplicates
    - Configurable recursion depth
    """

    def __init__(self, max_depth: int = 2):
        """
        Initialize batch downloader.

        Args:
            max_depth: Maximum recursion depth for following links (default: 2)
                      0 = no recursion (only specified docs)
                      1 = specified docs + their direct links
                      2 = specified docs + links + links of links
        """
        self.max_depth = max_depth
        self.downloaded: Set[str] = set()
        self.to_download: List[Tuple[str, int]] = []  # (url, depth)

    def add_url(self, url: str, depth: int = 0):
        """
        Add URL to download queue.

        Args:
            url: Google Docs URL
            depth: Current recursion depth
        """
        try:
            doc_id = extract_doc_id(url)
            if doc_id and doc_id not in self.downloaded:
                # Also check if not already in queue
                if not any(extract_doc_id(queued_url) == doc_id for queued_url, _ in self.to_download):
                    self.to_download.append((url, depth))
        except ValueError:
            # Invalid URL, skip
            pass

    def add_urls_from_file(self, file_path: str):
        """
        Add all URLs from a markdown file to download queue.

        Args:
            file_path: Path to markdown file
        """
        urls = extract_gdoc_urls_from_file(file_path)
        for url in urls:
            self.add_url(url, depth=0)

    def add_links_from_doc(self, doc_structure: dict, current_depth: int):
        """
        Extract and add linked docs from a downloaded document.

        Args:
            doc_structure: Google Docs API response structure
            current_depth: Current recursion depth
        """
        if current_depth >= self.max_depth:
            return

        urls = extract_gdoc_links_from_doc(doc_structure)
        for url in urls:
            self.add_url(url, depth=current_depth + 1)

    def mark_downloaded(self, url: str):
        """
        Mark URL as downloaded and remove from queue if present.

        Args:
            url: Google Docs URL
        """
        try:
            doc_id = extract_doc_id(url)
            if doc_id:
                self.downloaded.add(doc_id)
                # Also remove from queue if it's there
                self.to_download = [(u, d) for u, d in self.to_download
                                   if extract_doc_id(u) != doc_id]
        except ValueError:
            pass

    def has_pending(self) -> bool:
        """
        Check if there are pending downloads.

        Returns:
            True if there are URLs to download
        """
        return len(self.to_download) > 0

    def get_next(self) -> Tuple[str, int]:
        """
        Get next URL to download.

        Returns:
            Tuple of (url, depth)

        Raises:
            IndexError: If no pending downloads
        """
        if not self.to_download:
            raise IndexError("No pending downloads")

        return self.to_download.pop(0)

    def get_stats(self) -> dict:
        """
        Get download statistics.

        Returns:
            Dictionary with download stats
        """
        return {
            'downloaded': len(self.downloaded),
            'pending': len(self.to_download),
            'total': len(self.downloaded) + len(self.to_download)
        }
