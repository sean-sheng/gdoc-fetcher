"""Tests for Drive API client."""
import pytest
from unittest.mock import Mock, MagicMock, patch
from googleapiclient.errors import HttpError

from gdoc_fetch.drive_client import DriveClient


@pytest.fixture
def mock_drive_service():
    """Create a mock Drive service."""
    with patch('gdoc_fetch.drive_client.build') as mock_build:
        mock_service = MagicMock()
        mock_build.return_value = mock_service
        yield mock_service


@pytest.fixture
def client(mock_drive_service):
    """Create DriveClient instance with mocked service."""
    return DriveClient(token="fake_token")


def test_client_initialization(mock_drive_service):
    """Test DriveClient initialization."""
    client = DriveClient(token="test_token")

    assert client.service == mock_drive_service


def test_upload_image_success(client, mock_drive_service, tmp_path):
    """Test successful image upload."""
    # Create test image file
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake image data")

    # Mock the files().create() response
    mock_create = Mock()
    mock_create.execute.return_value = {
        'id': 'file123',
        'webContentLink': 'https://drive.google.com/uc?id=file123'
    }
    mock_drive_service.files().create.return_value = mock_create

    # Mock permissions
    mock_perm = Mock()
    mock_perm.execute.return_value = {}
    mock_drive_service.permissions().create.return_value = mock_perm

    # Upload
    url = client.upload_image(str(image_file))

    assert url == 'https://drive.google.com/uc?id=file123'
    mock_drive_service.files().create.assert_called_once()
    mock_drive_service.permissions().create.assert_called_once()


def test_upload_image_custom_name(client, mock_drive_service, tmp_path):
    """Test upload with custom name."""
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake image data")

    mock_create = Mock()
    mock_create.execute.return_value = {
        'id': 'file123',
        'webContentLink': 'https://drive.google.com/uc?id=file123'
    }
    mock_drive_service.files().create.return_value = mock_create

    mock_perm = Mock()
    mock_perm.execute.return_value = {}
    mock_drive_service.permissions().create.return_value = mock_perm

    url = client.upload_image(str(image_file), name="custom_name.png")

    assert url == 'https://drive.google.com/uc?id=file123'
    # Check the file metadata used correct name
    call_args = mock_drive_service.files().create.call_args
    assert call_args[1]['body']['name'] == 'custom_name.png'


def test_upload_image_file_not_found(client):
    """Test upload with non-existent file."""
    with pytest.raises(FileNotFoundError):
        client.upload_image("nonexistent.png")


def test_upload_image_not_image_type(client, tmp_path):
    """Test upload with non-image file."""
    text_file = tmp_path / "test.txt"
    text_file.write_text("not an image")

    with pytest.raises(ValueError, match="not a supported image type"):
        client.upload_image(str(text_file))


def test_upload_image_api_error_403(client, mock_drive_service, tmp_path):
    """Test upload with 403 permission error."""
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake image data")

    # Mock HttpError with 403
    mock_response = Mock()
    mock_response.status = 403
    error = HttpError(resp=mock_response, content=b"Permission denied")

    mock_create = Mock()
    mock_create.execute.side_effect = error
    mock_drive_service.files().create.return_value = mock_create

    with pytest.raises(ValueError, match="Permission denied"):
        client.upload_image(str(image_file))


def test_upload_image_api_error_404(client, mock_drive_service, tmp_path):
    """Test upload with 404 API not found error."""
    image_file = tmp_path / "test.png"
    image_file.write_bytes(b"fake image data")

    mock_response = Mock()
    mock_response.status = 404
    error = HttpError(resp=mock_response, content=b"Not found")

    mock_create = Mock()
    mock_create.execute.side_effect = error
    mock_drive_service.files().create.return_value = mock_create

    with pytest.raises(ValueError, match="Drive API not found"):
        client.upload_image(str(image_file))


def test_make_public(client, mock_drive_service):
    """Test making file public."""
    mock_perm = Mock()
    mock_perm.execute.return_value = {}
    mock_drive_service.permissions().create.return_value = mock_perm

    client._make_public('file123')

    mock_drive_service.permissions().create.assert_called_once_with(
        fileId='file123',
        body={'type': 'anyone', 'role': 'reader'}
    )


def test_make_public_fails_gracefully(client, mock_drive_service):
    """Test that permission errors are handled gracefully."""
    mock_response = Mock()
    mock_response.status = 403
    error = HttpError(resp=mock_response, content=b"Permission denied")

    mock_perm = Mock()
    mock_perm.execute.side_effect = error
    mock_drive_service.permissions().create.return_value = mock_perm

    # Should not raise exception
    client._make_public('file123')


def test_batch_upload_images_success(client, mock_drive_service, tmp_path):
    """Test batch upload of multiple images."""
    # Create test image files
    image1 = tmp_path / "image1.png"
    image1.write_bytes(b"fake image 1")
    image2 = tmp_path / "image2.jpg"
    image2.write_bytes(b"fake image 2")

    # Mock responses for each upload
    mock_create1 = Mock()
    mock_create1.execute.return_value = {
        'id': 'file1',
        'webContentLink': 'https://drive.google.com/uc?id=file1'
    }
    mock_create2 = Mock()
    mock_create2.execute.return_value = {
        'id': 'file2',
        'webContentLink': 'https://drive.google.com/uc?id=file2'
    }

    mock_drive_service.files().create.side_effect = [mock_create1, mock_create2]

    mock_perm = Mock()
    mock_perm.execute.return_value = {}
    mock_drive_service.permissions().create.return_value = mock_perm

    # Batch upload
    image_paths = {
        str(image1): None,
        str(image2): 'custom_name.jpg'
    }

    results = client.batch_upload_images(image_paths)

    assert len(results) == 2
    assert str(image1) in results
    assert str(image2) in results
    assert results[str(image1)] == 'https://drive.google.com/uc?id=file1'
    assert results[str(image2)] == 'https://drive.google.com/uc?id=file2'


def test_batch_upload_partial_failure(client, mock_drive_service, tmp_path, capsys):
    """Test batch upload with some failures."""
    image1 = tmp_path / "image1.png"
    image1.write_bytes(b"fake image 1")

    mock_create = Mock()
    mock_create.execute.return_value = {
        'id': 'file1',
        'webContentLink': 'https://drive.google.com/uc?id=file1'
    }
    mock_drive_service.files().create.return_value = mock_create

    mock_perm = Mock()
    mock_perm.execute.return_value = {}
    mock_drive_service.permissions().create.return_value = mock_perm

    # One valid file, one missing file
    image_paths = {
        str(image1): None,
        "nonexistent.png": None
    }

    results = client.batch_upload_images(image_paths)

    # Should return result for successful upload only
    assert len(results) == 1
    assert str(image1) in results

    # Check warning was printed
    captured = capsys.readouterr()
    assert "Warning: Failed to upload" in captured.out


def test_upload_various_image_formats(client, mock_drive_service, tmp_path):
    """Test upload supports various image formats."""
    formats = ['.png', '.jpg', '.jpeg', '.gif', '.webp']

    for fmt in formats:
        image_file = tmp_path / f"test{fmt}"
        image_file.write_bytes(b"fake image data")

        mock_create = Mock()
        mock_create.execute.return_value = {
            'id': f'file{fmt}',
            'webContentLink': f'https://drive.google.com/uc?id=file{fmt}'
        }
        mock_drive_service.files().create.return_value = mock_create

        mock_perm = Mock()
        mock_perm.execute.return_value = {}
        mock_drive_service.permissions().create.return_value = mock_perm

        url = client.upload_image(str(image_file))
        assert url  # Should not raise exception
