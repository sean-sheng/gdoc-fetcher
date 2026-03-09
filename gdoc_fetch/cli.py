"""Command-line interface for gdoc-fetch with batch and recursive support."""
import argparse
import sys
from pathlib import Path
from datetime import datetime

from gdoc_common.auth import get_access_token, AuthenticationError
from gdoc_common.utils import extract_doc_id
from gdoc_common.google_api import DocsClient
from gdoc_fetch.converter import DocsToHtmlParser, HtmlToMarkdownConverter
from gdoc_fetch.images import extract_image_urls, download_images
from gdoc_fetch.writer import write_document, replace_image_placeholders, sanitize_filename
from gdoc_fetch.batch import BatchDownloader, extract_gdoc_urls_from_file


def parse_args():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Fetch Google Docs, download images, convert to Markdown',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Single document
  gdoc-fetch "https://docs.google.com/document/d/DOC_ID/edit"
  gdoc-fetch "DOC_ID"

  # Batch download from markdown file
  gdoc-fetch --file filelist.md
  gdoc-fetch --file filelist.md --recursive
  gdoc-fetch --file filelist.md --max-depth 2

  # Options
  gdoc-fetch "url" --output-dir ./my-docs
  gdoc-fetch "url" --no-images
        """
    )

    parser.add_argument(
        'url',
        nargs='?',
        help='Google Docs URL or document ID'
    )

    parser.add_argument(
        '--file',
        help='Markdown file containing Google Docs URLs to download'
    )

    parser.add_argument(
        '--output-dir',
        default='./output',
        help='Output directory (default: ./output)'
    )

    parser.add_argument(
        '--no-images',
        action='store_true',
        help='Skip downloading images'
    )

    parser.add_argument(
        '--recursive',
        action='store_true',
        help='Recursively download linked Google Docs (default depth: 1)'
    )

    parser.add_argument(
        '--max-depth',
        type=int,
        default=1,
        help='Maximum recursion depth for following links (default: 1, use 0 to disable)'
    )

    args = parser.parse_args()

    # Validate arguments
    if not args.url and not args.file:
        parser.error('Either url or --file must be provided')

    if args.url and args.file:
        parser.error('Cannot specify both url and --file')

    return args


def fetch_single_document(doc_id: str, token: str, output_dir: Path, no_images: bool) -> dict:
    """
    Fetch and save a single document.

    Args:
        doc_id: Document ID
        token: Access token
        output_dir: Output directory
        no_images: Whether to skip images

    Returns:
        Dictionary with document structure (for recursive link extraction)
    """
    docs_client = DocsClient(token=token)

    # Fetch document
    doc = docs_client.fetch_document(doc_id)
    print(f"  ✓ Fetched: {doc.title}")

    # Convert to markdown
    converter_html = DocsToHtmlParser()
    converter_md = HtmlToMarkdownConverter()

    doc_data = docs_client.service.documents().get(documentId=doc_id).execute()
    html = converter_html.parse(doc_data)
    markdown = converter_md.convert(html)

    # Handle images
    image_map = {}
    if not no_images:
        image_urls = extract_image_urls(doc)

        if image_urls:
            print(f"    Downloading {len(image_urls)} image(s)...")
            safe_name = sanitize_filename(doc.title)
            doc_output_dir = output_dir / safe_name
            image_map = download_images(image_urls, str(doc_output_dir), token)

    # Replace image placeholders
    if image_map:
        markdown = replace_image_placeholders(markdown, image_map)

    # Write document
    source_url = f'https://docs.google.com/document/d/{doc_id}/edit'
    file_path = write_document(doc.title, source_url, markdown, str(output_dir))

    print(f"    Saved to: {file_path}")
    return doc_data


def main():
    """Main entry point for gdoc-fetch CLI."""
    args = parse_args()

    try:
        # Authenticate
        print("Authenticating with gcloud...")
        try:
            token = get_access_token()
            print("✓ Authentication successful\n")
        except AuthenticationError as e:
            print(f"\nAuthentication Error: {e}", file=sys.stderr)
            print("\nPlease run: gcloud auth login --enable-gdrive-access", file=sys.stderr)
            return 1

        # Create datetime-based output directory
        base_output_dir = Path(args.output_dir)
        timestamp = datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
        output_dir = base_output_dir / timestamp

        # Check if batch mode (file input)
        if args.file:
            print(f"Batch mode: Loading URLs from {args.file}...")

            try:
                urls = extract_gdoc_urls_from_file(args.file)
                print(f"✓ Found {len(urls)} Google Docs URL(s)\n")
            except (FileNotFoundError, ValueError) as e:
                print(f"\nError reading file: {e}", file=sys.stderr)
                return 1

            if not urls:
                print("No Google Docs URLs found in file.", file=sys.stderr)
                return 1

            # Set up batch downloader
            max_depth = args.max_depth if args.recursive else 0
            downloader = BatchDownloader(max_depth=max_depth)

            # Add URLs from file
            for url in urls:
                downloader.add_url(url, depth=0)

            if max_depth > 0:
                print(f"Recursive mode enabled (max depth: {max_depth})\n")
            else:
                print("Recursive mode disabled\n")

            # Download all documents
            download_count = 0
            error_count = 0

            while downloader.has_pending():
                url, depth = downloader.get_next()
                doc_id = extract_doc_id(url)

                print(f"[{download_count + 1}] Downloading {doc_id} (depth: {depth})...")

                try:
                    doc_data = fetch_single_document(doc_id, token, output_dir, args.no_images)
                    downloader.mark_downloaded(url)
                    download_count += 1

                    # Extract and add linked docs if recursive
                    if depth < max_depth:
                        downloader.add_links_from_doc(doc_data, depth)

                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    error_count += 1

                print()

            # Print summary
            stats = downloader.get_stats()
            print("=" * 60)
            print(f"Batch download complete!")
            print(f"  Downloaded: {stats['downloaded']} document(s)")
            if error_count > 0:
                print(f"  Errors: {error_count}")
            print(f"  Output directory: {output_dir}")
            print("=" * 60)

            return 0 if error_count == 0 else 1

        # Single document mode
        else:
            print(f"Single document mode: {args.url}")
            doc_id = extract_doc_id(args.url)
            print(f"Document ID: {doc_id}\n")

            max_depth = args.max_depth if args.recursive else 0
            downloader = BatchDownloader(max_depth=max_depth)
            downloader.add_url(args.url, depth=0)

            if max_depth > 0:
                print(f"Recursive mode enabled (max depth: {max_depth})\n")

            download_count = 0
            error_count = 0

            while downloader.has_pending():
                url, depth = downloader.get_next()
                doc_id = extract_doc_id(url)

                print(f"Downloading {doc_id} (depth: {depth})...")

                try:
                    doc_data = fetch_single_document(doc_id, token, output_dir, args.no_images)
                    downloader.mark_downloaded(url)
                    download_count += 1

                    # Extract and add linked docs if recursive
                    if depth < max_depth:
                        downloader.add_links_from_doc(doc_data, depth)

                except Exception as e:
                    print(f"  ✗ Failed: {e}")
                    error_count += 1

                print()

            print("=" * 60)
            print(f"Success! Downloaded {download_count} document(s)")
            if error_count > 0:
                print(f"Errors: {error_count}")
            print(f"Output directory: {output_dir}")
            print("=" * 60)

            return 0 if error_count == 0 else 1

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user.", file=sys.stderr)
        return 130

    except Exception as e:
        print(f"\nError: {e}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == '__main__':
    sys.exit(main())
