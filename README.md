# gdoc-skill

**gdoc-fetch** and **gdoc-upload** — fetch Google Docs to Markdown (with images) and upload Markdown to new Google Docs.

A standalone Python CLI that integrates with Claude Code: fetch Google Docs (download images, convert to Markdown) and upload Markdown files to create new Google Docs with formatting and images.

## ✨ Features

- 📥 **Fetch Google Docs** - Works with both public and private documents
- 📤 **Upload to Google Docs** - Convert Markdown files to Google Docs with formatting
- 🖼️ **Image Support** - Download images from Docs, upload images from Markdown
- 📝 **Clean Markdown** - Preserves formatting (bold, italic, links, lists, code blocks)
- 🔒 **Secure** - Uses Google Cloud authentication (no API keys needed)
- 🤖 **Claude Code Ready** - Integrates as a skill for seamless use in conversations
- ✅ **Well Tested** - Comprehensive unit tests with high coverage

## 🚀 Quick Start

See [QUICKSTART.md](QUICKSTART.md) for a 5-minute setup guide!

```bash
# 1. Clone the repository
git clone https://github.com/sean-sheng/gdoc-fetcher.git
cd gdoc-fetcher

# 2. Install
pip3 install --user -e .

# 3. Authenticate (one-time)
gcloud auth login --enable-gdrive-access

# 4. Fetch a Google Doc
gdoc-fetch "https://docs.google.com/document/d/YOUR_DOC_ID/edit"

# Or upload a Markdown file
gdoc-upload document.md
```

## 📚 Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Get started in 5 minutes
- **[INSTALLATION.md](INSTALLATION.md)** - Complete installation guide with troubleshooting
- **[SKILL.md](SKILL.md)** - Claude Code integration documentation

## 💻 Usage

### Fetch from Google Docs

```bash
gdoc-fetch <google-doc-url> [--output-dir ./output] [--no-images]
```

### Upload to Google Docs

```bash
gdoc-upload <markdown_file> [--title TITLE] [--no-images]
```

### Examples

```bash
# Fetch a document
gdoc-fetch "https://docs.google.com/document/d/123abc/edit"

# Custom output location
gdoc-fetch "https://docs.google.com/document/d/123abc/edit" --output-dir ./docs

# Skip images (faster)
gdoc-fetch "https://docs.google.com/document/d/123abc/edit" --no-images

# Use document ID directly
gdoc-fetch "123abc"
```

### Upload to Google Docs

Convert and upload Markdown files to create new Google Docs:

```bash
# Upload markdown file
gdoc-upload document.md

# Upload with custom title
gdoc-upload document.md --title "My Project Spec"

# Upload without images (faster)
gdoc-upload document.md --no-images
```

**Supported Markdown Features:**
- Headings (H1-H6)
- Bold, italic, links
- Bulleted and numbered lists
- Code blocks (rendered as monospace)
- Images (automatically uploaded to Google Drive)

**Output:**
The command outputs a clickable Google Docs URL for the newly created document.

### Output Structure

```
output/
└── document-name/
    ├── document-name.md    # Markdown with frontmatter
    └── images/
        ├── image-001.png
        └── image-002.jpg
```

## 🔐 Authentication

Requires Google Cloud SDK (gcloud) for authentication.

**One-time setup:**
```bash
gcloud auth login --enable-gdrive-access
```

This uses your Google account credentials - no API keys needed!

## 🤖 Claude Code Integration

Works seamlessly with Claude Code:
- **Fetch:** Paste a Google Docs URL and Claude can fetch and read the document.
- **Upload:** Ask Claude to create a Google Doc from a Markdown file; it can run `gdoc-upload` and share the new doc link.

See [SKILL.md](SKILL.md) for integration details.

## 🛠️ Development

### Install Dev Dependencies

```bash
pip3 install -e ".[dev]"
```

### Run Tests

```bash
# Quick way - run unit tests only (fast)
./run_tests.sh

# Or use pytest directly
pytest tests/unit/ -v

# Run integration tests (requires authentication)
./run_tests.sh integration

# Run all tests
./run_tests.sh all

# Expected: 121 unit tests + 20 integration tests
```

See [tests/integration/README.md](tests/integration/README.md) for integration test details.

### Project Structure

This repo provides two CLIs: **gdoc-fetch** (Docs → Markdown) and **gdoc-upload** (Markdown → Docs).

```
gdoc-skill/
├── gdoc_fetch/           # Shared source
│   ├── auth.py           # Authentication
│   ├── cli.py            # gdoc-fetch entry point
│   ├── cli_upload.py     # gdoc-upload entry point
│   ├── converter.py      # Docs→HTML→Markdown
│   ├── docs_builder.py   # Markdown→Docs API requests
│   ├── drive_client.py   # Google Drive API (images)
│   ├── google_api.py     # Google Docs API client
│   ├── images.py         # Image download/upload
│   ├── markdown_parser.py # Markdown parser
│   ├── models.py         # Data models
│   ├── utils.py          # URL parsing
│   └── writer.py         # File writing
├── tests/                # Test suite
├── SKILL.md              # Claude Code integration
└── README.md             # This file
```

## 🐛 Troubleshooting

See [INSTALLATION.md](INSTALLATION.md) for detailed troubleshooting guides.

**Common issues:**

- **Command not found**: Add `~/.local/bin` to your PATH
- **Auth error**: Run `gcloud auth login --enable-gdrive-access`
- **Module not found**: Install dependencies with pip

## 📝 Requirements

- Python 3.10+
- Google Cloud SDK (gcloud)
- Dependencies: google-api-python-client, google-auth, markdownify, markdown

## 🤝 Contributing

Contributions welcome! The codebase is well-tested and documented.

1. Fork the repository
2. Create a feature branch
3. Write tests for your changes
4. Ensure all tests pass
5. Submit a pull request

## 📄 License

MIT License - See LICENSE file for details

## 🙏 Acknowledgments

Built with:
- [google-api-python-client](https://github.com/googleapis/google-api-python-client) - Google Docs & Drive API access
- [markdownify](https://github.com/matthewwithanm/python-markdownify) - HTML to Markdown conversion
- [markdown](https://github.com/Python-Markdown/markdown) - Markdown to HTML parsing
- [pytest](https://pytest.org/) - Testing framework

---

**Made with ❤️ for seamless Google Docs ↔ Markdown with Claude Code (gdoc-fetch + gdoc-upload)**
