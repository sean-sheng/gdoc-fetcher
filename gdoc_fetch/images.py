"""Image downloading and management."""
from pathlib import Path
from typing import Dict
import urllib.request


def extract_image_urls(doc) -> Dict[str, str]:
    """
    Extract image URLs from document's inline objects.

    Args:
        doc: Document model with inline_objects

    Returns:
        Dict mapping object_id to image URL
    """
    image_map = {}

    for object_id, inline_obj in doc.inline_objects.items():
        if inline_obj.image_url:
            image_map[object_id] = inline_obj.image_url

    return image_map


def download_image(url: str, output_path: str, token: str) -> bool:
    """
    Download an image from URL with authentication.

    Args:
        url: Image URL
        output_path: Local path to save image
        token: OAuth access token

    Returns:
        True if successful, False otherwise
    """
    try:
        req = urllib.request.Request(
            url,
            headers={'Authorization': f'Bearer {token}'}
        )

        with urllib.request.urlopen(req, timeout=30) as response:
            image_data = response.read()

        Path(output_path).write_bytes(image_data)
        return True

    except Exception as e:
        print(f"Warning: Failed to download image from {url}: {e}")
        return False


def download_images(
    image_urls: Dict[str, str],
    output_dir: str,
    token: str
) -> Dict[str, str]:
    """
    Download all images and return mapping of object_id to filename.

    Args:
        image_urls: Dict of object_id -> URL
        output_dir: Document output directory
        token: OAuth access token

    Returns:
        Dict mapping object_id to local filename
    """
    if not image_urls:
        return {}

    # Create images directory
    images_dir = Path(output_dir) / "images"
    images_dir.mkdir(parents=True, exist_ok=True)

    image_map = {}
    image_counter = 1

    for object_id, url in image_urls.items():
        # Determine file extension from URL or content type
        extension = _get_extension_from_url(url)
        filename = f"image-{image_counter:03d}{extension}"

        output_path = images_dir / filename

        success = download_image(url, str(output_path), token)

        if success:
            image_map[object_id] = filename
            image_counter += 1

    return image_map


def _get_extension_from_url(url: str) -> str:
    """Extract file extension from URL."""
    # Common image extensions
    for ext in ['.png', '.jpg', '.jpeg', '.gif', '.webp']:
        if ext in url.lower():
            return ext

    # Default to .png
    return '.png'
