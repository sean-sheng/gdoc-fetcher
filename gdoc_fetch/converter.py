"""Document conversion from Google Docs to Markdown."""
from typing import Dict, List, Any
from markdownify import markdownify as md


class DocsToHtmlParser:
    """Converts Google Docs JSON structure to HTML."""

    def parse(self, doc_structure: Dict[str, Any]) -> str:
        """
        Parse Google Docs structure to HTML.

        Args:
            doc_structure: Google Docs API response structure

        Returns:
            HTML string
        """
        self.lists_data = doc_structure.get('lists', {})
        html_parts = []

        body = doc_structure.get('body', {})
        content = body.get('content', [])

        # Group consecutive list items
        i = 0
        while i < len(content):
            element = content[i]

            # Check if this is a list item
            if 'paragraph' in element and 'bullet' in element['paragraph']:
                # Collect all consecutive items from the same list
                list_items = []
                current_list_id = element['paragraph']['bullet'].get('listId')

                while i < len(content):
                    curr_elem = content[i]
                    if 'paragraph' in curr_elem and 'bullet' in curr_elem['paragraph']:
                        bullet = curr_elem['paragraph']['bullet']
                        if bullet.get('listId') == current_list_id:
                            list_items.append(curr_elem)
                            i += 1
                        else:
                            break
                    else:
                        break

                # Generate list HTML
                html_parts.append(self._parse_list(list_items, current_list_id))
            else:
                html_parts.append(self._parse_structural_element(element))
                i += 1

        return ''.join(html_parts)

    def _parse_structural_element(self, element: Dict[str, Any]) -> str:
        """Parse a single structural element."""
        if 'paragraph' in element:
            return self._parse_paragraph(element['paragraph'])

        return ''

    def _parse_list(self, list_items: List[Dict[str, Any]], list_id: str) -> str:
        """Parse a list of items into HTML."""
        if not list_items:
            return ''

        # Determine if it's ordered or unordered
        list_props = self.lists_data.get(list_id, {}).get('listProperties', {})
        nesting_levels = list_props.get('nestingLevels', [{}])
        glyph_type = nesting_levels[0].get('glyphType', 'BULLET')

        is_ordered = glyph_type in ['DECIMAL', 'ROMAN', 'ALPHA']
        tag = 'ol' if is_ordered else 'ul'

        items_html = []
        for item in list_items:
            paragraph = item['paragraph']
            elements = paragraph.get('elements', [])
            text_parts = []

            for elem in elements:
                if 'textRun' in elem:
                    text_parts.append(self._parse_text_run(elem['textRun']))

            text = ''.join(text_parts).strip()
            if text:
                items_html.append(f'<li>{text}</li>')

        return f'<{tag}>{"".join(items_html)}</{tag}>'

    def _parse_paragraph(self, paragraph: Dict[str, Any]) -> str:
        """Parse a paragraph element."""
        elements = paragraph.get('elements', [])
        text_parts = []

        for elem in elements:
            if 'textRun' in elem:
                text_parts.append(self._parse_text_run(elem['textRun']))
            elif 'inlineObjectElement' in elem:
                text_parts.append(self._parse_inline_object(elem['inlineObjectElement']))

        text = ''.join(text_parts).strip()
        if not text:
            return ''

        return f'<p>{text}</p>'

    def _parse_inline_object(self, inline_object: Dict[str, Any]) -> str:
        """Parse an inline object (typically an image) to a placeholder."""
        object_id = inline_object.get('inlineObjectId', '')
        return f'<img src="INLINE_OBJECT_{object_id}" />'

    def _parse_text_run(self, text_run: Dict[str, Any]) -> str:
        """Parse a text run with optional styling."""
        content = text_run.get('content', '').rstrip('\n')
        if not content:
            return ''

        text_style = text_run.get('textStyle', {})

        # Apply bold
        if text_style.get('bold'):
            content = f'<strong>{content}</strong>'

        # Apply italic
        if text_style.get('italic'):
            content = f'<em>{content}</em>'

        # Apply link
        if 'link' in text_style:
            url = text_style['link'].get('url', '')
            content = f'<a href="{url}">{content}</a>'

        return content


class HtmlToMarkdownConverter:
    """Converts HTML to Markdown using markdownify."""

    def __init__(self):
        """Initialize converter with default options."""
        self.options = {
            'heading_style': 'ATX',  # Use # for headings
            'bullets': '-',  # Use - for bullets
            'strip': ['script', 'style'],
        }

    def convert(self, html: str) -> str:
        """
        Convert HTML to Markdown.

        Args:
            html: HTML string

        Returns:
            Markdown string
        """
        return md(html, **self.options)
