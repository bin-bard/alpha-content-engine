# Alpha Content Engine

**AI Innovation Intern - OptiBot Mini-Clone Take-Home Test**

## Setup

**Environment Variables:**

```bash
# Create .env file with:
OPENAI_API_KEY=your-openai-api-key
ZS_SUBDOMAIN=optisignshelp
ZS_EMAIL=optional-zendesk-email
ZS_TOKEN=optional-zendesk-token
```

## How to Run Locally

```bash
pip install -r requirements.txt
python main.py
```

**Expected Output:** Scrapes ≥30 OptiSigns articles → API upload to Vector Store → Logs counts (added/updated/skipped)

## Docker Deployment

```bash
docker build -t alpha-content-engine .
docker run -e OPENAI_API_KEY=your-key alpha-content-engine
```

Command runs once and exits 0. No hard-coded keys (uses .env pattern).

## Assignment Deliverables

### 1. Scrape Markdown (~3h)

**Goal:** Ingest messy web content and normalize it
**Implementation:** Pull ≥30 articles from support.optisigns.com via Zendesk API
**Output:** Clean Markdown files as `{slug}.md` with preserved links, headings, no nav/ads

### 2. Build Assistant & Load Vector Store (~2h)

**API Upload:** Mandatory programmatic upload (no UI drag-and-drop)
**System Prompt (Verbatim):**

```
You are OptiBot, the customer-support bot for OptiSigns.com.
• Tone: helpful, factual, concise.
• Only answer using the uploaded docs.
• Max 5 bullet points; else link to the doc.
• Cite up to 3 "Article URL:" lines per reply.
```

### 3. Deploy as Daily Job (~2h)

**Platform:** GitHub Actions (FREE)
**Function:** Re-scrape → Detect changes (hash) → Upload only deltas  
**Logging:** Counts added/updated/skipped
**Job Logs:** [View in Actions tab]

## GitHub Actions Deployment (FREE)

1. **Add Secret**: Repository → Settings → Secrets → `OPENAI_API_KEY`
2. **Push to GitHub**: Workflow in `.github/workflows/scraper.yml`
3. **Automatic**: Runs daily at 9 AM UTC
4. **Manual Trigger**: Actions tab → "Run workflow" button

## Chunking Strategy

**File-based chunking:** Each article = 1 file uploaded to OpenAI Vector Store

**Benefits:** Preserves article structure, maintains URLs for citations, simple & reliable for support use case
**Process:** HTML → Clean Markdown → Metadata footer → API upload
**Logged:** Files embedded in vector store + chunks processed count

## Screenshot of Playground Answer

**Test Question:** "How do I add a YouTube video?"
**Assistant Response:** Shows correct behavior with system prompt compliance

![GPT-4o Response](images/gpt-4o.png)
_GPT-4o: Correctly states no documents available (follows "Only answer using uploaded docs")_

![GPT-3.5-turbo Response](images/gpt-3.5-turbo.png)
_GPT-3.5-turbo: Comparison showing hallucination vs. compliant behavior_

## Docker Local Testing

![Docker Local Test](images/docker-local.PNG)
_Local Docker container execution showing successful scraping and processing_

**Assistant ID:** `asst_[generated-on-run]` (unique per execution)

## Architecture

```
Zendesk API → Delta Detection → OpenAI Vector Store → OptiBot Assistant
     ↓              ↓                    ↓                    ↓
  30+ articles   SHA256 hash         API upload       Customer support
```

**Files:** `main.py` (orchestrator) • `src/scraper.py` (Zendesk) • `src/uploader.py` (OpenAI) • `.github/workflows/scraper.yml` (automation)
