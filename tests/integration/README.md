# Integration Tests

Comprehensive end-to-end tests for gdoc-fetch and gdoc-upload functionality.

## Overview

These tests verify the complete workflows:

- **gdoc-upload**: Upload Markdown files to create Google Docs
- **gdoc-fetch**: Fetch Google Docs and convert to Markdown
- **Round-trip**: Upload → Fetch → Verify content preservation

## Prerequisites

### 1. Authentication

Integration tests require Google Cloud authentication:

```bash
gcloud auth login --enable-gdrive-access
```

### 2. Dependencies

All dependencies should be installed:

```bash
pip install -e ".[dev]"
```

## Running Tests

### Run All Integration Tests

```bash
pytest tests/integration/ -v
```

Or explicitly mark:

```bash
pytest -m integration -v
```

### Run Specific Test Files

```bash
# Upload tests only
pytest tests/integration/test_gdoc_upload_integration.py -v

# Fetch tests only
pytest tests/integration/test_gdoc_fetch_integration.py -v
```

### Run Specific Test Classes

```bash
# Upload CLI tests
pytest tests/integration/test_gdoc_upload_integration.py::TestGdocUploadIntegration -v

# Fetch CLI tests
pytest tests/integration/test_gdoc_fetch_integration.py::TestGdocFetchIntegration -v

# Round-trip tests
pytest tests/integration/test_gdoc_fetch_integration.py::TestRoundTripIntegration -v
```

### Run Specific Test Cases

```bash
# Test simple markdown upload
pytest tests/integration/test_gdoc_upload_integration.py::TestGdocUploadIntegration::test_upload_simple_markdown -v

# Test roundtrip workflow
pytest tests/integration/test_gdoc_fetch_integration.py::TestRoundTripIntegration::test_upload_and_fetch_roundtrip -v
```

## Run Unit Tests Only (Default)

Unit tests run by default and skip integration tests:

```bash
pytest
# or explicitly
pytest -m "not integration"
```

## Test Coverage

### Upload Tests (`test_gdoc_upload_integration.py`)

- ✅ Upload simple markdown
- ✅ Upload with --no-images flag
- ✅ Upload complex markdown (headings, lists, code, links)
- ✅ Auto-extract title from H1
- ✅ Error handling for nonexistent files
- ✅ Special characters and unicode
- ✅ MarkdownParser integration
- ✅ DocsRequestBuilder integration

### Fetch Tests (`test_gdoc_fetch_integration.py`)

- ✅ Fetch public document with URL
- ✅ Fetch with document ID
- ✅ Fetch with --no-images flag
- ✅ Fetch with images
- ✅ Error handling for invalid URLs
- ✅ Error handling for nonexistent documents
- ✅ Custom output directory
- ✅ Verify output structure
- ✅ GoogleDocsConverter integration

### Round-Trip Tests

- ✅ Upload → Fetch → Verify simple document
- ✅ Upload → Fetch → Verify complex document
- ✅ Content preservation validation

## Important Notes

### Document Cleanup

**Created test documents are NOT automatically deleted.** The Google Docs API does not support document deletion.

After running tests, you may want to manually clean up test documents from your Google Drive:

1. Look for documents with titles like:
   - "Integration Test Simple"
   - "Integration Test Complex"
   - "Roundtrip Test Document"

2. The test output will print URLs of created documents for easy cleanup.

### Test Isolation

- Each test uses temporary directories that are automatically cleaned up
- Tests are independent and can run in any order
- Tests should be idempotent (safe to run multiple times)

### Authentication Skipping

If authentication is not available, integration tests will be automatically skipped:

```
SKIPPED [1] tests/integration/conftest.py:28: Authentication not available
```

To enable, run: `gcloud auth login --enable-gdrive-access`

## CI/CD Integration

### GitHub Actions Example

```yaml
name: Integration Tests

on: [push, pull_request]

jobs:
  integration:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3

      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.11'

      - name: Install dependencies
        run: |
          pip install -e ".[dev]"

      - name: Authenticate with Google Cloud
        uses: google-github-actions/auth@v1
        with:
          credentials_json: ${{ secrets.GCP_SA_KEY }}

      - name: Run integration tests
        run: pytest -m integration -v
```

### Required Secrets

For CI/CD, you'll need to configure:
- `GCP_SA_KEY`: Service account key with Google Docs and Drive API access

## Troubleshooting

### Authentication Errors

```
pytest.skip: Authentication not available
```

**Solution**: Run `gcloud auth login --enable-gdrive-access`

### Permission Denied

```
403 Forbidden
```

**Solution**: Ensure your Google account has proper API access enabled

### Timeout Errors

Some tests have timeouts (60-120 seconds). If tests timeout:
- Check internet connection
- Verify Google API is accessible
- Increase timeout if needed for slow connections

## Development Workflow

### Before Committing Code

Run all tests to ensure nothing breaks:

```bash
# Run unit tests (fast)
pytest -m "not integration"

# Run integration tests (slower, requires auth)
pytest -m integration
```

### Adding New Tests

1. Add test to appropriate file:
   - `test_gdoc_upload_integration.py` for upload features
   - `test_gdoc_fetch_integration.py` for fetch features

2. Mark as integration test:
   ```python
   @pytest.mark.integration
   class TestNewFeature:
       def test_something(self):
           ...
   ```

3. Use fixtures from `conftest.py`:
   - `auth_token`: Authentication token
   - `docs_client`: DocsClient instance
   - `temp_dir`: Temporary directory
   - `created_docs`: Track created docs
   - `sample_markdown`: Sample markdown file

4. Run new test:
   ```bash
   pytest tests/integration/test_*.py::TestNewFeature -v
   ```

## Performance

Integration tests are slower than unit tests:

- **Unit tests**: ~0.5 seconds (121 tests)
- **Integration tests**: ~30-60 seconds (depends on API latency)

Use unit tests for rapid development, integration tests for final verification.

## Test Matrix

| Test Type | Speed | Requires Auth | Requires Network | Creates Docs |
|-----------|-------|---------------|------------------|--------------|
| Unit      | Fast  | ❌            | ❌               | ❌           |
| Integration | Slow | ✅           | ✅               | ✅           |

---

**For questions or issues, check the main [README.md](../../README.md) or [INSTALLATION.md](../../INSTALLATION.md)**
