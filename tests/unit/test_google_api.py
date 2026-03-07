"""Tests for Google API client."""
from unittest.mock import MagicMock, Mock
import pytest
from googleapiclient.errors import HttpError
from gdoc_fetch.google_api import DocsClient
from gdoc_fetch.models import Document


def test_docs_client_fetch_document(mocker):
    """Test fetching a document from Google Docs API."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_get = mock_docs.get.return_value
    mock_get.execute.return_value = {
        'documentId': '123abc',
        'title': 'Test Document',
        'body': {
            'content': [
                {
                    'paragraph': {
                        'elements': [
                            {'textRun': {'content': 'Test content\n'}}
                        ]
                    }
                }
            ]
        },
        'inlineObjects': {}
    }

    client = DocsClient(token="test-token")
    client.service = mock_service

    doc = client.fetch_document("123abc")

    assert doc.doc_id == "123abc"
    assert doc.title == "Test Document"
    mock_docs.get.assert_called_once_with(documentId="123abc")


def test_docs_client_parse_inline_objects(mocker):
    """Test parsing inline objects from API response."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_get = mock_docs.get.return_value
    mock_get.execute.return_value = {
        'documentId': '123',
        'title': 'Test',
        'body': {'content': []},
        'inlineObjects': {
            'kix.abc123': {
                'inlineObjectProperties': {
                    'embeddedObject': {
                        'imageProperties': {
                            'contentUri': 'https://lh3.googleusercontent.com/image.png'
                        }
                    }
                }
            }
        }
    }

    client = DocsClient(token="test-token")
    client.service = mock_service

    doc = client.fetch_document("123")

    assert len(doc.inline_objects) == 1
    assert 'kix.abc123' in doc.inline_objects
    assert 'googleusercontent' in doc.inline_objects['kix.abc123'].image_url


def test_create_document_success(mocker):
    """Test creating a new document."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_create = mock_docs.create.return_value
    mock_create.execute.return_value = {
        'documentId': 'new-doc-123'
    }

    client = DocsClient(token="test-token")
    client.service = mock_service

    doc_id = client.create_document("My Title")

    assert doc_id == "new-doc-123"
    mock_docs.create.assert_called_once_with(body={'title': 'My Title'})


def test_create_document_permission_error(mocker):
    """Test create document with 403 error."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_create = mock_docs.create.return_value

    mock_response = Mock()
    mock_response.status = 403
    error = HttpError(resp=mock_response, content=b"Permission denied")
    mock_create.execute.side_effect = error

    client = DocsClient(token="test-token")
    client.service = mock_service

    with pytest.raises(ValueError, match="Permission denied"):
        client.create_document("Title")


def test_create_document_api_not_found(mocker):
    """Test create document with 404 error."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_create = mock_docs.create.return_value

    mock_response = Mock()
    mock_response.status = 404
    error = HttpError(resp=mock_response, content=b"Not found")
    mock_create.execute.side_effect = error

    client = DocsClient(token="test-token")
    client.service = mock_service

    with pytest.raises(ValueError, match="Docs API not found"):
        client.create_document("Title")


def test_update_document_content_success(mocker):
    """Test updating document content."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_batch = mock_docs.batchUpdate.return_value
    mock_batch.execute.return_value = {}

    client = DocsClient(token="test-token")
    client.service = mock_service

    requests = [
        {'insertText': {'location': {'index': 1}, 'text': 'Hello'}}
    ]

    client.update_document_content("doc-123", requests)

    mock_docs.batchUpdate.assert_called_once_with(
        documentId="doc-123",
        body={'requests': requests}
    )


def test_update_document_content_empty_requests(mocker):
    """Test update with empty requests list."""
    mock_service = MagicMock()
    client = DocsClient(token="test-token")
    client.service = mock_service

    # Should not call API
    client.update_document_content("doc-123", [])

    mock_service.documents.assert_not_called()


def test_update_document_permission_error(mocker):
    """Test update document with 403 error."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_batch = mock_docs.batchUpdate.return_value

    mock_response = Mock()
    mock_response.status = 403
    error = HttpError(resp=mock_response, content=b"Permission denied")
    mock_batch.execute.side_effect = error

    client = DocsClient(token="test-token")
    client.service = mock_service

    requests = [{'insertText': {}}]

    with pytest.raises(ValueError, match="Permission denied"):
        client.update_document_content("doc-123", requests)


def test_update_document_not_found(mocker):
    """Test update document with 404 error."""
    mock_service = MagicMock()
    mock_docs = mock_service.documents.return_value
    mock_batch = mock_docs.batchUpdate.return_value

    mock_response = Mock()
    mock_response.status = 404
    error = HttpError(resp=mock_response, content=b"Not found")
    mock_batch.execute.side_effect = error

    client = DocsClient(token="test-token")
    client.service = mock_service

    requests = [{'insertText': {}}]

    with pytest.raises(ValueError, match="Document not found"):
        client.update_document_content("doc-123", requests)


def test_get_document_url():
    """Test generating document URL."""
    client = DocsClient(token="test-token")

    url = client.get_document_url("abc123xyz")

    assert url == "https://docs.google.com/document/d/abc123xyz/edit"
