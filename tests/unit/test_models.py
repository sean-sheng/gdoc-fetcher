"""Tests for document models."""
from gdoc_fetch.models import Document, Tab, InlineObject


def test_document_creation():
    """Test creating a Document model."""
    doc = Document(
        doc_id="123abc",
        title="Test Document",
        tabs=[],
        inline_objects={}
    )

    assert doc.doc_id == "123abc"
    assert doc.title == "Test Document"
    assert len(doc.tabs) == 0


def test_tab_creation():
    """Test creating a Tab model."""
    tab = Tab(
        tab_id="tab1",
        title="Main",
        content=[]
    )

    assert tab.tab_id == "tab1"
    assert tab.title == "Main"


def test_inline_object_creation():
    """Test creating an InlineObject model."""
    obj = InlineObject(
        object_id="kix.abc123",
        image_url="https://lh3.googleusercontent.com/...",
        content_type="image/png"
    )

    assert obj.object_id == "kix.abc123"
    assert "googleusercontent" in obj.image_url
    assert obj.content_type == "image/png"
