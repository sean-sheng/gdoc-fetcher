"""Tests for image downloading module."""
from gdoc_fetch.images import extract_image_urls
from gdoc_fetch.models import Document, InlineObject
from unittest.mock import Mock, patch, MagicMock
import pytest


def test_extract_image_urls():
    """Test extracting image URLs from document."""
    doc = Document(
        doc_id="123",
        title="Test",
        tabs=[],
        inline_objects={
            "kix.abc123": InlineObject(
                object_id="kix.abc123",
                image_url="https://lh3.googleusercontent.com/image1.png",
                content_type="image/png"
            ),
            "kix.def456": InlineObject(
                object_id="kix.def456",
                image_url="https://lh3.googleusercontent.com/image2.jpg",
                content_type="image/jpeg"
            )
        }
    )

    result = extract_image_urls(doc)

    assert len(result) == 2
    assert result["kix.abc123"] == "https://lh3.googleusercontent.com/image1.png"
    assert result["kix.def456"] == "https://lh3.googleusercontent.com/image2.jpg"


def test_extract_image_urls_no_images():
    """Test document with no images."""
    doc = Document(
        doc_id="123",
        title="Test",
        tabs=[],
        inline_objects={}
    )

    result = extract_image_urls(doc)

    assert len(result) == 0


def test_download_image(tmp_path, mocker):
    """Test downloading a single image."""
    from gdoc_fetch.images import download_image

    # Mock urllib.request.urlopen
    mock_response = MagicMock()
    mock_response.read.return_value = b'fake image data'
    mock_response.__enter__.return_value = mock_response

    mocker.patch('urllib.request.urlopen', return_value=mock_response)

    output_path = tmp_path / "test.png"
    success = download_image(
        url="https://example.com/image.png",
        output_path=str(output_path),
        token="test-token"
    )

    assert success
    assert output_path.exists()
    assert output_path.read_bytes() == b'fake image data'


def test_download_image_failure(tmp_path, mocker):
    """Test handling download failure."""
    from gdoc_fetch.images import download_image

    mocker.patch('urllib.request.urlopen', side_effect=Exception("Network error"))

    output_path = tmp_path / "test.png"
    success = download_image(
        url="https://example.com/image.png",
        output_path=str(output_path),
        token="test-token"
    )

    assert not success
    assert not output_path.exists()


def test_download_images_batch(tmp_path, mocker):
    """Test downloading multiple images."""
    from gdoc_fetch.images import download_images

    # Mock successful downloads
    mock_download = mocker.patch('gdoc_fetch.images.download_image', return_value=True)

    image_urls = {
        "kix.abc123": "https://example.com/img1.png",
        "kix.def456": "https://example.com/img2.jpg"
    }

    result = download_images(
        image_urls=image_urls,
        output_dir=str(tmp_path),
        token="test-token"
    )

    assert len(result) == 2
    assert result["kix.abc123"] == "image-001.png"
    assert result["kix.def456"] == "image-002.jpg"
    assert mock_download.call_count == 2


def test_download_images_creates_directory(tmp_path, mocker):
    """Test that images directory is created."""
    from gdoc_fetch.images import download_images

    mocker.patch('gdoc_fetch.images.download_image', return_value=True)

    output_dir = tmp_path / "doc"
    images_dir = output_dir / "images"

    assert not images_dir.exists()

    download_images(
        image_urls={"id1": "http://example.com/img.png"},
        output_dir=str(output_dir),
        token="token"
    )

    assert images_dir.exists()
