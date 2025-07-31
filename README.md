# Alpha Content Engine

## Overview

**Enterprise-grade content pipeline** that transforms web documentation into intelligent AI assistants through automated scraping, processing, and deployment.

**Core Achievements:**

- **30+ Articles Processed**: Zendesk API → Clean Markdown with preserved structure
- **Zero-UI Deployment**: 100% programmatic OpenAI API integration
- **Smart Delta Detection**: Hash-based change tracking for efficient updates
- **Production Ready**: Dockerized with daily automation and comprehensive logging

**Technical Excellence:**

- **API-First Architecture**: No manual uploads, fully automated vector store management
- **Intelligent Chunking**: File-based strategy optimized for accurate citations
- **Cost-Effective Scaling**: GitHub Actions over expensive cloud platforms
- **Security Best Practices**: Environment-based secrets, no hardcoded keys

## System Architecture

![Architecture](images/Architecture.png)

## Screenshots

### OpenAI Playground Answer - **Strict Compliance Achieved**

![GPT-4o Response](images/gpt-4o.png)
_**GPT-4o**: Perfect adherence to "Only answer using uploaded docs" with proper citations_

![GPT-3.5-turbo Response](images/gpt-3.5-turbo.png)
_**Comparison**: GPT-3.5-turbo shows hallucination vs. compliant behavior demonstration_

### GitHub Actions Deployment - **Zero-Cost Automation**

![GitHub Actions](images/github-action1.png)
_**Production Pipeline**: Automated daily execution with assistant reuse and intelligent delta tracking_

### Docker Local Testing - **One-Command Deployment**

![Docker Local Test](images/docker-local.PNG)
_**Container Success**: Clean execution showing scraping, processing, and exit 0 compliance_

## Quick Start

**Setup:**

```bash
# Windows: Copy template file and rename
copy .env.sample .env
# Edit .env file and replace with your actual API key:
# OPENAI_API_KEY=your-actual-openai-api-key

# Linux/Mac alternative:
# cp .env.sample .env
```

**How to run locally:**

```bash
# Install dependencies and run
pip install -r requirements.txt
python main.py

# Build and run Docker container (exits 0 as required)
docker build -t alpha-content-engine .
docker run -e OPENAI_API_KEY=your-api-key alpha-content-engine
```

**Link to daily job logs:**

[**All GitHub Actions Logs**](https://github.com/bin-bard/alpha-content-engine/actions) - **Public repository** with complete run history, logs, and downloadable artifacts including config files and scraper logs.

**Note:** First run will show "artifact not found" warning (expected behavior) as no previous config exists. **Assistant reuse starts from second run onwards** for optimal performance.

## Chunking Strategy

**File-based chunking:** Each article = 1 file uploaded to OpenAI Vector Store

**Benefits:**

- Preserves article structure for better context
- Maintains URLs for accurate citations
- Simple & reliable for support use cases
- Optimal for retrieval accuracy

**Process:** `HTML → Clean Markdown → Metadata footer → API upload`

**Logged:** Files embedded in vector store + chunks processed count for full transparency
