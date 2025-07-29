# Alpha Content Engine

OptiSigns support article scraper and OpenAI assistant synchronization system.

## Overview

Automated system that:

- Scrapes 35+ articles from OptiSigns support (Zendesk API)
- Converts HTML to clean Markdown
- Detects content changes via SHA256 hash comparison
- Uploads only changed files to OpenAI Assistant
- Provides OptiBot customer support functionality

## Setup

### 1. Clone Repository

```bash
git clone https://github.com/bin-bard/alpha-content-engine.git
cd alpha-content-engine
```

### 2. Environment Variables

```bash
cp .env.sample .env
```

Edit `.env` file:

```
ZS_SUBDOMAIN=optisignshelp
ZS_EMAIL=your-zendesk-email@example.com  # Optional for auth
ZS_TOKEN=your-zendesk-token              # Optional for auth
OPENAI_API_KEY=your-openai-api-key       # Required
```

### 3. Install Dependencies

```bash
pip install -r requirements.txt
```

## Usage

### Run Locally

```bash
python main.py
```

**First run:** Scrapes all articles, creates assistant

```
Processing changes:
- NEW: 35 articles
- UPDATED: 0 articles
- UNCHANGED: 0 articles
Added: 35, Updated: 0, Skipped: 0
```

**Subsequent runs:** Only processes changes

```
Processing changes:
- NEW: 2 articles
- UPDATED: 1 articles
- UNCHANGED: 32 articles
Added: 2, Updated: 1, Skipped: 32
```

### Docker

```bash
docker build -t alpha-content-engine .
docker run -e OPENAI_API_KEY=your-key alpha-content-engine
```

## Chunking Strategy

**File-based chunking:** Each article becomes one file uploaded to OpenAI Assistant.

**Benefits:**

- Preserves article structure and context
- Maintains original URLs and metadata for citations
- Simple and reliable for customer support use case
- Each article is independently searchable

**Process:**

1. HTML → Clean Markdown conversion
2. Add metadata footer (Article URL, ID, Last Updated)
3. Save as `{slug}.md` files
4. Upload to OpenAI with `file_search` capability

## Assistant Configuration

**System Prompt:**

```
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
```

**Model:** gpt-4o-mini  
**Tools:** file_search

## Daily Job Deployment

**Platform:** DigitalOcean App Platform  
**Schedule:** Daily cron job  
**Logs:** Available at [deployment URL]/logs

**Job functionality:**

1. Re-scrape OptiSigns support articles
2. Detect changes via content hash comparison
3. Upload only new/updated articles to OpenAI
4. Log detailed counts: added, updated, skipped

## Test Results

**OptiBot Assistant ID:** `asst_TOlJVwtDI4yIgWYE5fCc85yE`

**Test Question:** "How do I add a YouTube video?"

**Response:** Assistant provides helpful steps in bullet format with appropriate tone.

![OptiBot Screenshot](images/screenshot.png)

## Architecture

```
[Zendesk API] → [Scraper] → [Delta Detection] → [OpenAI Assistant]
                     ↓
              [Markdown Files] → [Hash Comparison] → [Upload Only Changes]
```

**Files:**

- `main.py` - Combined scraper + uploader
- `article_metadata.json` - Change tracking
- `optibot_config.json` - Assistant configuration
- `articles/` - Scraped Markdown files
