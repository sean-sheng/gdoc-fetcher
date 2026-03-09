---
name: gdoc-skill
description: gdoc-fetch and gdoc-upload. Fetch Google Docs to Markdown (with images) or upload Markdown to new Google Docs. Supports batch download from markdown files and recursive link following. Use when user provides a Google Docs URL to read/save as Markdown, or when user wants to create a Google Doc from a Markdown file.
---

# Google Docs ↔ Markdown (gdoc-fetch & gdoc-upload)

**gdoc-fetch:** Fetch Google Docs and convert to Markdown with images. Supports batch download and recursive link following.
**gdoc-upload:** Upload Markdown files to create new Google Docs with formatting and images.

## When to Use This Tool

Use **gdoc-fetch** when the user:
- Provides a Google Docs URL (e.g., `https://docs.google.com/document/d/.../edit`)
- Provides a markdown file containing multiple Google Docs URLs to batch download
- Asks you to read, review, or analyze a Google Doc
- Wants to import documentation, specifications, or requirements from Google Docs
- Needs to convert a Google Doc to Markdown format
- Wants to save a Google Doc locally with all its images
- Wants to download a document and all linked Google Docs recursively

Use **gdoc-upload** when the user:
- Wants to create a Google Doc from a Markdown file
- Asks you to upload, publish, or share a document to Google Docs
- Has a local Markdown file (e.g. a spec or report) they want as a Google Doc

## Usage

### gdoc-fetch — Fetch a Google Doc to Markdown

**Single Document:**
```bash
gdoc-fetch "<google-doc-url>" --output-dir <project-dir>/docs
```

**Batch Download from File:**
```bash
gdoc-fetch --file urls.md --output-dir <project-dir>/docs
```

**Recursive Download (follow links):**
```bash
gdoc-fetch "<google-doc-url>" --recursive --max-depth 2
gdoc-fetch --file urls.md --recursive --max-depth 2
```

**Options:**
- `url`: Google Docs URL or document ID (for single document mode)
- `--file`: Markdown file containing Google Docs URLs to batch download
- `--output-dir`: Output directory (default: `./output`). Files are saved to a timestamped subfolder
- `--no-images`: Skip downloading images (faster, but document won't include images)
- `--recursive`: Recursively download linked Google Docs (default depth: 1)
- `--max-depth`: Maximum recursion depth for following links (default: 1, use 0 to disable)

### gdoc-upload — Upload Markdown to a new Google Doc

```bash
gdoc-upload <markdown_file> [--title TITLE] [--no-images]
```

**Options:**
- `markdown_file` (required): Path to the Markdown file
- `--title`: Document title (default: derived from filename)
- `--no-images`: Skip uploading images (faster)

### Typical Workflow

When the user provides a Google Docs URL:

1. **Run the fetch command:**
   ```bash
   gdoc-fetch "https://docs.google.com/document/d/ABC123/edit" --output-dir ./docs
   ```

2. **The tool will:**
   - Extract the document ID from the URL
   - Authenticate using gcloud credentials
   - Fetch the full document structure via Google Docs API
   - Convert Google Docs format to clean HTML, then to Markdown
   - Download all embedded images (with authentication)
   - Save to organized directory structure
   - Add frontmatter with document title and source URL

3. **Read the generated markdown file:**
   ```bash
   cat docs/document-name/document-name.md
   ```
   Or use the Read tool to view the file content.

4. **Discuss the document naturally with the user:**
   Analyze the content, answer questions, extract requirements, etc.

## Output Structure

The tool creates a well-organized directory structure with timestamp-based organization:

```
output/
└── 2026-03-08_14-30-45/        # Execution timestamp
    ├── document-name/          # Sanitized document title
    │   ├── document-name.md    # Main markdown file with frontmatter
    │   └── images/             # All embedded images
    │       ├── image-001.png
    │       ├── image-002.jpg
    │       └── ...
    └── another-document/       # Additional documents (batch mode)
        ├── another-document.md
        └── images/
            └── ...
```

**Note:** Each execution creates a new timestamped subfolder to keep downloads organized by session.

### Markdown File Format

Each generated markdown file includes:

```markdown
---
title: Document Title
source: https://docs.google.com/document/d/.../edit
fetched_at: 2026-03-02T10:30:00
---

# Document Title

[Content here with proper formatting]

![Alt text](images/image-001.png)
```

## Examples

### Example 1: User Provides a Specification Document

```
User: "Here's the spec: https://docs.google.com/document/d/1abc123/edit"

Actions:
1. Run: gdoc-fetch "https://docs.google.com/document/d/1abc123/edit" --output-dir ./docs
2. Wait for completion (shows progress: authenticating, fetching, converting, downloading images)
3. Read: ./docs/product-spec/product-spec.md
4. Respond: "I've reviewed the specification. Here are the main requirements..."
```

### Example 2: User Wants to Import Documentation

```
User: "Can you pull this doc into the project? https://docs.google.com/document/d/xyz789/edit"

Actions:
1. Run: gdoc-fetch "https://docs.google.com/document/d/xyz789/edit" --output-dir ./docs
2. Confirm: "I've imported the documentation to ./docs/api-guide/api-guide.md"
3. Summarize key sections if requested
```

### Example 3: Quick Fetch Without Images

```
User: "Read this doc: https://docs.google.com/document/d/def456/edit"

Actions:
1. Run: gdoc-fetch "https://docs.google.com/document/d/def456/edit" --output-dir ./docs --no-images
   (Faster if images aren't needed)
2. Read the generated markdown
3. Discuss content with user
```

### Example 4: Using Document ID Directly

```bash
# Both work the same:
gdoc-fetch "https://docs.google.com/document/d/1abc123xyz/edit"
gdoc-fetch "1abc123xyz"
```

### Example 5: Batch Download from Markdown File

```
User: "Download all the docs listed in urls.md"

Actions:
1. Run: gdoc-fetch --file urls.md --output-dir ./docs
2. Tool extracts all Google Docs URLs from the markdown file
3. Downloads each document to ./docs/YYYY-MM-DD_HH-MM-SS/
4. Respond: "Downloaded 5 documents to ./docs/2026-03-08_14-30-45/"
```

### Example 6: Recursive Download (Follow Links)

```
User: "Download this doc and all the docs it links to"

Actions:
1. Run: gdoc-fetch "<url>" --recursive --max-depth 2 --output-dir ./docs
2. Tool downloads the initial document
3. Extracts all Google Docs links from the document
4. Recursively downloads linked documents up to max-depth
5. Respond: "Downloaded 8 documents (1 initial + 7 linked) to ./docs/2026-03-08_14-30-45/"
```

### Example 7: Upload Markdown to Google Docs

```
User: "Turn docs/spec.md into a Google Doc and share the link"

Actions:
1. Run: gdoc-upload docs/spec.md --title "Project Spec"
2. Command prints the new Google Docs URL
3. Respond: "Created: https://docs.google.com/document/d/.../edit"
```

## Authentication

### Prerequisites

The tool requires Google Cloud authentication with Google Drive access.

### Initial Setup

User must authenticate once with:
```bash
gcloud auth login --enable-gdrive-access
```

This provides:
- OAuth access token for Google Docs API
- Google Drive scope for reading documents and downloading images
- Token cached by gcloud CLI for future requests

### Checking Authentication

If you encounter authentication errors, tell the user to verify their authentication:
```bash
gcloud auth list
gcloud auth application-default print-access-token
```

## Error Handling

### Authentication Errors

**Symptom:** `Authentication Error: gcloud auth login required`

**Solution:**
```
Tell user: "You need to authenticate with Google Cloud. Please run:
  gcloud auth login --enable-gdrive-access
Then try again."
```

### Document Access Errors

**Symptom:** `403 Forbidden` or `The caller does not have permission`

**Solution:**
```
Tell user: "I don't have access to this document. Please:
1. Open the document
2. Click 'Share'
3. Change access to 'Anyone with the link can view'
   OR
   Add your Google account email with view permissions
Then try again."
```

### Document Not Found

**Symptom:** `404 Not Found` or `Invalid document ID`

**Solution:**
```
Verify the URL is correct and the document exists.
Make sure the URL includes the full document ID.
```

### gcloud Not Installed

**Symptom:** `gcloud command not found` or `FileNotFoundError`

**Solution:**
```
Tell user: "Google Cloud SDK is not installed. Please install it:
  macOS: brew install google-cloud-sdk
  Other: https://cloud.google.com/sdk/docs/install
Then authenticate with:
  gcloud auth login --enable-gdrive-access"
```

### Image Download Failures

**Symptom:** Some images show as `[Image: <url>]` instead of local paths

**Behavior:** The tool is resilient - the document will still be created with markdown, but failed images will remain as URL references instead of local file paths.

**Solution:**
```
If critical images are missing:
1. Check authentication includes Drive access
2. Verify the images are accessible in the original document
3. Re-run the command
4. If persistent, use --no-images and reference original doc for images
```

### Invalid URL Format

**Symptom:** `ValueError: Invalid Google Docs URL or ID`

**Solution:**
```
The URL must be in one of these formats:
- https://docs.google.com/document/d/DOCUMENT_ID/edit
- https://docs.google.com/document/d/DOCUMENT_ID
- DOCUMENT_ID (just the ID string)
```

## Best Practices

1. **Always specify output directory:** Use `--output-dir` to organize docs in a logical location (e.g., `./docs`, `./specs`, `./requirements`)

2. **Read the generated file:** After fetching, always read the markdown file to understand the content before discussing with the user.

3. **Check for images:** If the document is visual or contains diagrams, don't use `--no-images`.

4. **Handle errors gracefully:** If authentication fails, provide clear instructions to the user.

5. **Verify file paths:** After successful fetch, the tool prints the output path - use this exact path to read the file.

6. **Multiple documents:** You can fetch multiple documents into the same output directory - they'll be organized in separate subdirectories.

## Technical Details

### Document Conversion Process

1. **API Fetch:** Uses Google Docs API to get full document structure (content, styles, inline objects)
2. **HTML Generation:** Converts Google Docs elements to semantic HTML
3. **Markdown Conversion:** Uses `markdownify` to convert HTML to clean Markdown
4. **Image Handling:**
   - Extracts all `inlineObjects` with image URLs
   - Downloads each image with authentication
   - Replaces placeholder URLs with local file paths
5. **File Writing:** Creates directory structure and writes markdown with frontmatter

### Supported Google Docs Features

- Text formatting (bold, italic, underline, strikethrough)
- Headings (H1-H6)
- Lists (bulleted, numbered)
- Links
- Inline images
- Tables (converted to markdown tables)
- Code blocks (converted to fenced code blocks)

### Limitations

- Comments are not included in the export
- Suggestions/tracked changes are not included
- Complex formatting may be simplified
- Some Google Docs-specific features (e.g., smart chips) may not convert perfectly
- Drawing objects are not supported

## Installation

If the tool is not installed, user should run:

```bash
# From the gdoc-skill directory
pip install -e .
```

This installs the `gdoc-fetch` and `gdoc-upload` commands.

## Summary

- **gdoc-fetch:** Use when a user shares a Google Docs URL. Fetch the doc to Markdown (with images), read the output, then discuss.
- **gdoc-upload:** Use when a user wants a Markdown file turned into a Google Doc. Run `gdoc-upload <file>`, then share the returned Google Docs URL.

Authenticate once with `gcloud auth login --enable-gdrive-access`; both commands use the same credentials.
