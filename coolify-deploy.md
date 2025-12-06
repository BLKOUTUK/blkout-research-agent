# Deploying BLKOUT Research Agent via Coolify

## Quick Deploy

### 1. Push to GitHub

```bash
cd /home/robbe/blkout-research-agent
git init
git add .
git commit -m "feat: BLKOUT Research Agent - agentic news & events discovery"
git remote add origin https://github.com/BLKOUTUK/blkout-research-agent.git
git push -u origin main
```

### 2. Create Application in Coolify

1. Go to Coolify dashboard → **New Resource** → **Application**
2. Select **GitHub** as source
3. Choose repository: `BLKOUTUK/blkout-research-agent`
4. Build pack: **Dockerfile**
5. Port: None needed (background service)

### 3. Configure Environment Variables

In Coolify application settings → **Environment Variables**:

```
GROQ_API_KEY=gsk_your_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...
MAX_SEARCH_RESULTS=10
RELEVANCE_THRESHOLD=70
```

**Get your Groq API key free:** https://console.groq.com

### 4. Deploy

Click **Deploy** in Coolify.

### 5. Verify

Check logs in Coolify to see:
```
[Scheduler] Jobs configured:
  - Daily News & Events Discovery: cron[hour='6', minute='0']
  - Evening Events Check: cron[hour='18', minute='0']
  - Weekly Deep Research: cron[day_of_week='sun', hour='3', minute='0']
[Scheduler] Started
```

## Manual Trigger

To run discovery immediately, use Coolify's **Execute Command** feature:

```bash
python main.py --run-now daily
```

Or for events only:
```bash
python main.py --run-now events
```

## Database Setup

Run this in Supabase SQL Editor before first deployment:

```sql
-- Add discovery_method to existing news_articles
ALTER TABLE news_articles
ADD COLUMN IF NOT EXISTS discovery_method TEXT;

-- Create events table
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
    event_type TEXT DEFAULT 'community',
    image_url TEXT,
    source_platform TEXT,
    url_hash TEXT UNIQUE,
    relevance_score INTEGER DEFAULT 50,
    status TEXT DEFAULT 'review',
    published BOOLEAN DEFAULT false,
    tags TEXT[],
    discovery_method TEXT DEFAULT 'research_agent',
    discovered_at TIMESTAMPTZ DEFAULT NOW(),
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW()
);

-- Create discovery_logs table for monitoring
CREATE TABLE IF NOT EXISTS discovery_logs (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    run_type TEXT NOT NULL,
    started_at TIMESTAMPTZ DEFAULT NOW(),
    stats JSONB,
    errors TEXT[],
    status TEXT DEFAULT 'running',
    created_at TIMESTAMPTZ DEFAULT NOW()
);

-- Indexes for performance
CREATE INDEX IF NOT EXISTS idx_events_url_hash ON events(url_hash);
CREATE INDEX IF NOT EXISTS idx_events_start_date ON events(start_date);
CREATE INDEX IF NOT EXISTS idx_events_status ON events(status);
CREATE INDEX IF NOT EXISTS idx_discovery_logs_run_type ON discovery_logs(run_type);
```

## Monitoring

### Check Discovery Logs

```sql
-- Recent runs
SELECT run_type, started_at, stats, status
FROM discovery_logs
ORDER BY created_at DESC
LIMIT 10;

-- Today's discoveries
SELECT
    (stats->>'discovered')::int as found,
    (stats->>'inserted')::int as new,
    (stats->>'skipped')::int as duplicates
FROM discovery_logs
WHERE created_at > NOW() - INTERVAL '24 hours';
```

### Check Discovered Content

```sql
-- Recent news articles from agent
SELECT title, source_name, relevance_score, created_at
FROM news_articles
WHERE discovery_method = 'research_agent'
ORDER BY created_at DESC
LIMIT 20;

-- Recent events from agent
SELECT name, venue, city, start_date, source_platform
FROM events
WHERE discovery_method = 'research_agent'
ORDER BY discovered_at DESC
LIMIT 20;
```

## Troubleshooting

### Container won't start

Check Coolify logs. Common issues:
- Missing environment variables
- Playwright browser install failed

### No content being discovered

1. Check `discovery_logs` table for errors
2. Verify Groq API key is valid
3. Run test mode locally: `python main.py --test`

### High memory usage

The browser scraper uses ~500MB RAM. If constrained:
- Disable scraping in `configs/blkout_config.py`
- Use search-only mode (still effective)

## Cost

- **Groq API**: Free tier (30 RPM, 14,400 requests/day)
- **Coolify hosting**: Your existing infrastructure
- **Supabase**: Your existing instance

**Total additional cost: $0**

## Architecture

```
Coolify Container
├── Scheduler (APScheduler)
│   ├── 6 AM: Daily Discovery
│   ├── 6 PM: Events Check
│   └── Sunday 3 AM: Deep Research
│
├── News Agent
│   ├── DuckDuckGo Search (free)
│   ├── Groq LLM Analysis (free)
│   └── Supabase Insert
│
└── Events Agent
    ├── Web Search
    ├── Playwright Scraping
    ├── LLM Extraction
    └── Supabase Insert
```
