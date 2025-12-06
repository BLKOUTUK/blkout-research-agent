"""
BLKOUT Research Agent Configuration
Optimized for Black LGBTQ+ UK community content discovery
"""

# =============================================================================
# MODEL CONFIGURATION - Using Groq Free Tier
# =============================================================================

llm_config = {
    "provider": "groq",
    "model": "llama-3.3-70b-versatile",  # Best free model on Groq
    "fallback_model": "llama-3.1-8b-instant",  # Faster, for simple tasks
    "temperature": 0.3,  # Lower for factual research
    "max_tokens": 4096,
}

# =============================================================================
# AGENT CONFIGURATION
# =============================================================================

planning_agent_config = {
    "name": "blkout_planner",
    "description": "Coordinates news and events research for Black LGBTQ+ UK community",
    "max_steps": 10,
    "model": "llama-3.3-70b-versatile",
}

researcher_agent_config = {
    "name": "blkout_researcher",
    "description": "Deep research on Black queer UK topics",
    "max_depth": 2,
    "max_results_per_search": 10,
    "model": "llama-3.3-70b-versatile",
}

scraper_agent_config = {
    "name": "blkout_scraper",
    "description": "Extracts structured event data from websites",
    "timeout": 30,
    "model": "llama-3.1-8b-instant",  # Faster model for extraction
}

analyzer_agent_config = {
    "name": "blkout_analyzer",
    "description": "Scores content relevance to Black LGBTQ+ UK community",
    "model": "llama-3.3-70b-versatile",
}

# =============================================================================
# SEARCH CONFIGURATION
# =============================================================================

news_search_queries = [
    # Primary intersectional queries
    "Black queer UK news",
    "Black LGBTQ Britain",
    "UK Black Pride",
    "QTIPOC UK",
    "Black gay men Britain",
    "Black trans UK",
    "Black lesbian UK",

    # Community organizations
    "BlackOut UK community",
    "Black queer organizations Britain",

    # Health & wellbeing
    "Black LGBTQ mental health UK",
    "HIV Black gay men UK",

    # Culture & arts
    "Black queer artists UK",
    "Black LGBTQ film UK",
]

events_search_queries = [
    # Direct event searches
    "Black LGBTQ events London",
    "QTIPOC parties UK",
    "Black queer events Manchester",
    "Black Pride events UK",

    # Platform-specific
    "site:outsavvy.com Black LGBTQ",
    "site:eventbrite.co.uk Black queer",
    "site:moonlightexperiences.com",

    # Venue/organizer searches
    "BBZ London events",
    "Misery QTIPOC",
    "Hungama queer",
    "Pxssy Palace",
]

# =============================================================================
# EVENT PLATFORMS TO SCRAPE
# =============================================================================

event_platforms = [
    {
        "name": "OutSavvy",
        "base_url": "https://www.outsavvy.com",
        "search_url": "https://www.outsavvy.com/search?q=",
        "selectors": {
            "event_card": ".event-card",
            "title": ".event-title",
            "date": ".event-date",
            "venue": ".event-venue",
            "link": "a[href*='/event/']",
        }
    },
    {
        "name": "Eventbrite",
        "base_url": "https://www.eventbrite.co.uk",
        "search_url": "https://www.eventbrite.co.uk/d/united-kingdom--london/",
        "selectors": {
            "event_card": "[data-testid='event-card']",
            "title": "h3",
            "date": "[data-testid='event-card-date']",
            "venue": "[data-testid='event-card-location']",
            "link": "a",
        }
    },
    {
        "name": "Moonlight Experiences",
        "base_url": "https://www.moonlightexperiences.com",
        "search_url": "https://www.moonlightexperiences.com/experiences",
        "selectors": {
            "event_card": ".experience-card",
            "title": ".experience-title",
            "date": ".experience-date",
            "venue": ".experience-venue",
            "link": "a",
        }
    },
    {
        "name": "London LGBTQ Centre",
        "base_url": "https://londonlgbtqcentre.org",
        "search_url": "https://londonlgbtqcentre.org/whats-on/",
        "selectors": {
            "event_card": ".event-item",
            "title": ".event-title",
            "date": ".event-date",
            "venue": ".event-venue",
            "link": "a",
        }
    },
]

# =============================================================================
# RELEVANCE SCORING
# =============================================================================

# Keywords that indicate HIGH relevance (intersectional Black LGBTQ+ UK)
high_relevance_keywords = [
    "black queer", "black gay", "black lgbtq", "black trans", "black lesbian",
    "qtipoc", "qpoc", "blkout", "blackout uk", "uk black pride",
    "black bisexual", "black nonbinary", "black non-binary",
    "african diaspora lgbtq", "caribbean lgbtq",
    "windrush lgbtq", "black british queer",
]

# Keywords that indicate MEDIUM relevance (need both Black AND LGBTQ+)
black_keywords = [
    "black", "african", "caribbean", "windrush", "diaspora", "afro",
    "nigerian", "jamaican", "ghanaian", "somali",
]

lgbtq_keywords = [
    "lgbtq", "queer", "gay", "lesbian", "trans", "bisexual",
    "pride", "nonbinary", "non-binary", "drag", "same-sex",
]

uk_keywords = [
    "uk", "britain", "british", "london", "manchester", "birmingham",
    "bristol", "leeds", "glasgow", "edinburgh", "cardiff",
]

# Minimum relevance score to include content (0-100)
relevance_threshold = 70

# =============================================================================
# OUTPUT CONFIGURATION
# =============================================================================

output_config = {
    "news_table": "news_articles",
    "events_table": "events",
    "batch_size": 50,
    "dedupe_field": "url_hash",
}

# =============================================================================
# SCHEDULING
# =============================================================================

schedule_config = {
    "news_research": {
        "frequency": "daily",
        "time": "06:00",
        "timezone": "Europe/London",
    },
    "events_scrape": {
        "frequency": "twice_daily",
        "times": ["08:00", "18:00"],
        "timezone": "Europe/London",
    },
    "deep_research": {
        "frequency": "weekly",
        "day": "sunday",
        "time": "03:00",
        "timezone": "Europe/London",
    },
}
