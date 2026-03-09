"""Pytest configuration and fixtures for integration tests."""
import os
import shutil
import tempfile
from pathlib import Path
from typing import Generator, List

import pytest

from gdoc_fetch.auth import get_access_token, AuthenticationError
from gdoc_fetch.google_api import DocsClient


@pytest.fixture(scope="session")
def auth_token() -> str:
    """
    Get authentication token for integration tests.

    Returns:
        Access token

    Raises:
        pytest.skip: If authentication is not available
    """
    try:
        token = get_access_token()
        return token
    except AuthenticationError:
        pytest.skip("Authentication not available. Run: gcloud auth login --enable-gdrive-access")


@pytest.fixture(scope="session")
def docs_client(auth_token: str) -> DocsClient:
    """
    Create DocsClient for integration tests.

    Args:
        auth_token: Authentication token

    Returns:
        Configured DocsClient instance
    """
    return DocsClient(token=auth_token)


@pytest.fixture
def temp_dir() -> Generator[Path, None, None]:
    """
    Create temporary directory for test outputs.

    Yields:
        Path to temporary directory
    """
    temp_path = Path(tempfile.mkdtemp(prefix="gdoc_test_"))
    try:
        yield temp_path
    finally:
        if temp_path.exists():
            shutil.rmtree(temp_path)


@pytest.fixture
def created_docs(docs_client: DocsClient) -> Generator[List[str], None, None]:
    """
    Track and cleanup created Google Docs.

    Yields:
        List to append created document IDs

    Note:
        Documents are NOT automatically deleted. Google Docs API
        does not support deletion. Created docs will be left in
        the user's Google Drive.
    """
    doc_ids: List[str] = []
    try:
        yield doc_ids
    finally:
        # Note: Google Docs API doesn't support document deletion
        # Created test documents will remain in the user's Google Drive
        # They can be manually deleted if needed
        if doc_ids:
            print(f"\nCreated {len(doc_ids)} test document(s). "
                  f"Manual cleanup may be needed:")
            for doc_id in doc_ids:
                url = docs_client.get_document_url(doc_id)
                print(f"  - {url}")


@pytest.fixture
def fixtures_dir() -> Path:
    """
    Get path to test fixtures directory.

    Returns:
        Path to fixtures directory
    """
    return Path(__file__).parent.parent / "fixtures"


@pytest.fixture
def sample_markdown(fixtures_dir: Path) -> Path:
    """
    Get path to sample markdown file.

    Args:
        fixtures_dir: Fixtures directory path

    Returns:
        Path to sample markdown file
    """
    return fixtures_dir / "test_document.md"


# Public test document for fetch tests
PUBLIC_TEST_DOC_ID = "1BxiMVs0XRA5nFMdKvBdBZjgmUUqptlbs74OgVE2upms"
PUBLIC_TEST_DOC_URL = f"https://docs.google.com/document/d/{PUBLIC_TEST_DOC_ID}/edit"
