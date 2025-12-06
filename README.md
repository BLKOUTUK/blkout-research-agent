# BLKOUT Research Agent

Agentic news and events discovery for the Black LGBTQ+ UK community.

## Overview

This agent uses AI to discover relevant news articles and events that matter to Black queer people in Britain. Unlike traditional RSS scraping, it:

- **Understands context** - Recognizes intersectional content semantically
- **Discovers dynamically** - Finds content across the web, not just predefined sources
- **Learns relevance** - Scores content based on community relevance
- **Scrapes events** - Extracts structured event data from platforms like OutSavvy, Eventbrite

## Architecture

```
┌─────────────────────────────────────┐
│         Planning Agent              │
│   (coordinates all discovery)       │
└──────────────┬──────────────────────┘
               │
    ┌──────────┼──────────┐
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ News   │ │ Events │ │Relevance│
│Research│ │Scraper │ │Analyzer │
└────────┘ └────────┘ └────────┘
    │          │          │
    └──────────┼──────────┘
               ▼
         ┌──────────┐
         │ Supabase │
         └──────────┘
```

## Quick Start

### 1. Install Dependencies

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # or `venv\Scripts\activate` on Windows

# Install dependencies
pip install -r requirements.txt

# Install Playwright browsers
playwright install chromium
```

### 2. Configure Environment

```bash
cp .env.template .env
# Edit .env with your API keys
```

Required:
- `GROQ_API_KEY` - Get free at https://console.groq.com
- `SUPABASE_URL` - Your Supabase project URL
- `SUPABASE_SERVICE_ROLE_KEY` - Your Supabase service role key

### 3. Test It

```bash
# Run in test mode (no database writes)
python main.py --test
```

### 4. Run Discovery

```bash
# Run daily discovery immediately
python main.py --run-now daily

# Run events-only discovery
python main.py --run-now events

# Run as daemon (scheduled execution)
python main.py
```

## Schedules

| Job | Time | Description |
|-----|------|-------------|
| Daily Discovery | 6:00 AM | News + events search |
| Evening Events | 6:00 PM | Additional events check |
| Weekly Deep Research | Sunday 3:00 AM | Broader time range search |

## Relevance Scoring

Content is scored 0-100 based on relevance to Black LGBTQ+ UK community:

- **90-100**: Explicitly intersectional (Black + LGBTQ+ + UK)
- **70-89**: Strong relevance (two of three criteria)
- **50-69**: Moderate relevance
- **0-49**: Low/no relevance (filtered out)

### High-Relevance Keywords (Auto 95+)

- "black queer", "black gay", "black lgbtq", "black trans"
- "qtipoc", "qpoc", "blkout", "uk black pride"
- "african diaspora lgbtq", "caribbean lgbtq"

## Event Platforms Scraped

- OutSavvy
- Eventbrite UK
- Moonlight Experiences
- London LGBTQ Centre

## Hosting on Hostinger

To run as a background service:

```bash
# Using screen
screen -S blkout-agent
python main.py
# Ctrl+A, D to detach

# Or using systemd (create /etc/systemd/system/blkout-agent.service)
[Unit]
Description=BLKOUT Research Agent
After=network.target

[Service]
Type=simple
User=your-user
WorkingDirectory=/path/to/blkout-research-agent
ExecStart=/path/to/venv/bin/python main.py
Restart=always

[Install]
WantedBy=multi-user.target
```

## Cost

- **Groq**: Free tier (30 RPM, 14,400 RPD)
- **DuckDuckGo Search**: Free, no API key
- **Playwright**: Free, local browser

Estimated monthly cost: **$0**

## Database Tables Required

```sql
-- news_articles table (likely exists)
ALTER TABLE news_articles ADD COLUMN IF NOT EXISTS discovery_method TEXT;

-- events table (create if needed)
CREATE TABLE IF NOT EXISTS events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name TEXT NOT NULL,
    description TEXT,
    url TEXT,
    venue TEXT,
    address TEXT,
    city TEXT,
    start_date TIMESTAMPTZ,
    end_date TIMESTAMPTZ,
    price TEXT,
    organizer TEXT,
    event_type TEXT,
    image_url TEXT,
    source_platform TEXT,
    url_hash TEXT UNIQUE,
    relevance_score INTEGER,
    status TEXT DEFAULT 'review',
    published BOOLEAN DEFAULT false,
    tags TEXT[],
    discovery_method TEXT,
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- discovery_logs table (for monitoring)
CREATE TABLE IF NOT EXISTS discovery_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type TEXT,
    started_at TIMESTAMPTZ,
    stats JSONB,
    errors TEXT[],
    status TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW()
);
```

## License

MIT - Built for BLKOUT UK community.
