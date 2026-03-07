"""Tests for document models."""
from gdoc_fetch.models import (
    Document, Tab, InlineObject,
    TextRun, Paragraph, Heading, ListItem, CodeBlock, Image, MarkdownDocument
)


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


# Markdown model tests

def test_text_run_plain():
    """Test creating a plain TextRun."""
    run = TextRun(text="Hello")

    assert run.text == "Hello"
    assert run.bold is False
    assert run.italic is False
    assert run.link_url is None


def test_text_run_formatted():
    """Test creating a formatted TextRun."""
    run = TextRun(text="Hello", bold=True, italic=True, link_url="https://example.com")

    assert run.text == "Hello"
    assert run.bold is True
    assert run.italic is True
    assert run.link_url == "https://example.com"


def test_paragraph_creation():
    """Test creating a Paragraph."""
    para = Paragraph(text_runs=[
        TextRun(text="Hello "),
        TextRun(text="world", bold=True)
    ])

    assert len(para.text_runs) == 2
    assert para.text_runs[0].text == "Hello "
    assert para.text_runs[1].bold is True


def test_heading_creation():
    """Test creating a Heading."""
    heading = Heading(
        level=1,
        text_runs=[TextRun(text="Title")]
    )

    assert heading.level == 1
    assert len(heading.text_runs) == 1
    assert heading.text_runs[0].text == "Title"


def test_list_item_creation():
    """Test creating a ListItem."""
    item = ListItem(
        text_runs=[TextRun(text="Item 1")],
        ordered=False
    )

    assert len(item.text_runs) == 1
    assert item.text_runs[0].text == "Item 1"
    assert item.ordered is False


def test_code_block_creation():
    """Test creating a CodeBlock."""
    code = CodeBlock(code="print('hello')", language="python")

    assert code.code == "print('hello')"
    assert code.language == "python"


def test_image_creation():
    """Test creating an Image."""
    img = Image(alt_text="Test image", local_path="/path/to/image.png")

    assert img.alt_text == "Test image"
    assert img.local_path == "/path/to/image.png"


def test_markdown_document_creation():
    """Test creating a MarkdownDocument."""
    doc = MarkdownDocument(
        title="Test Doc",
        elements=[
            Heading(level=1, text_runs=[TextRun(text="Title")]),
            Paragraph(text_runs=[TextRun(text="Content")])
        ]
    )

    assert doc.title == "Test Doc"
    assert len(doc.elements) == 2
    assert isinstance(doc.elements[0], Heading)
    assert isinstance(doc.elements[1], Paragraph)
