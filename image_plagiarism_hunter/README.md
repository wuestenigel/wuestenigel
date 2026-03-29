# Image Plagiarism Hunter

Monitor the web for unauthorized use of your images, photos, and visual content.

## Features

- **Reverse image search** via Google Vision API and TinEye API
- **Automated violation tracking** with persistent JSON database
- **Fair use assessment** heuristics to help prioritize enforcement
- **DMCA takedown notices** auto-generated in English and German
- **Weekly reports** with new violations, resolved cases, and pending actions
- **Dashboard** with all active cases prioritized by commercial impact
- **Approved domain whitelist** to skip authorized usage

## Quick Start

### 1. Install

```bash
pip install -e .
```

### 2. Configure

Set environment variables:

```bash
export GOOGLE_API_KEY="your-google-api-key"
export GOOGLE_CX_ID="your-custom-search-engine-id"
export TINEYE_API_KEY="your-tineye-api-key"
export IPH_OWNER_NAME="Your Name"
export IPH_OWNER_EMAIL="you@example.com"
export IPH_OWNER_ADDRESS="Your Address"
export IPH_OWNER_PHONE="+1-555-0100"
```

Or run the interactive setup:

```bash
image-plagiarism-hunter init
```

### 3. Scan

```bash
# Scan a single image
image-plagiarism-hunter scan "https://example.com/my-photo.jpg"

# Scan multiple images
image-plagiarism-hunter scan "https://example.com/photo1.jpg" "https://example.com/photo2.jpg"
```

### 4. Reports

```bash
# Generate weekly report
image-plagiarism-hunter report --print

# Generate dashboard
image-plagiarism-hunter dashboard --print

# View a specific violation
image-plagiarism-hunter detail <violation-id>
```

### 5. Manage Violations

```bash
# Mark a violation as DMCA sent
image-plagiarism-hunter update <violation-id> dmca_sent

# Mark as resolved
image-plagiarism-hunter update <violation-id> resolved -n "Image was removed"

# Mark as fair use
image-plagiarism-hunter update <violation-id> fair_use -n "Educational blog post"
```

## Configuration

### Approved Domains

Add domains to the whitelist in your config to skip them during scans:

```json
{
  "approved_domains": [
    "mywebsite.com",
    "myportfolio.net",
    "flickr.com"
  ]
}
```

### Similarity Threshold

Adjust the minimum similarity score (default: 80%) to control sensitivity:

```json
{
  "similarity_threshold": 75.0
}
```

## Project Structure

```
image_plagiarism_hunter/
  __init__.py          # Package init
  cli.py               # Command-line interface
  config.py            # Configuration management
  dmca.py              # DMCA notice generator (EN/DE)
  fair_use.py          # Fair use assessment heuristics
  hunter.py            # Core orchestrator
  models.py            # Data models
  report.py            # Report and dashboard generator
  search.py            # Reverse image search engines
  violations_db.py     # Violation tracking database
```

## API Keys

### Google Custom Search

1. Get an API key from [Google Cloud Console](https://console.cloud.google.com/)
2. Create a Custom Search Engine at [CSE](https://cse.google.com/)
3. Enable "Image search" and "Search the entire web"

### TinEye

1. Sign up at [TinEye API](https://tineye.com/developer)
2. Get your API key from the dashboard

## Estimated Cost

~$0.003 per run (based on API call pricing)
