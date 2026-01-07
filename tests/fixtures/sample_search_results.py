"""
Sample search results for testing event and news discovery
"""

from src.search import SearchResult
from datetime import datetime, timedelta


# ============================================================================
# EVENT SEARCH RESULTS - Various quality/completeness levels
# ============================================================================

def get_sample_event_search_results():
    """Get diverse sample event search results for testing"""
    return [
        # Complete, high-quality result
        SearchResult(
            title="BBZ: Black Boyz and Girlz - London Party",
            url="https://outsavvy.com/event/bbz-london-2026-01-07",
            snippet="BBZ is back! Join us for an unforgettable night celebrating Black queer community. Free entry before 11pm. Phoenix Bar, London. January 7, 2026.",
            source="OutSavvy",
            published_date="2026-01-05",
        ),
        # Medium quality - date in title
        SearchResult(
            title="Hungama Queer Night - Feb 21 2026",
            url="https://moonlight.com/events/hungama-2026-02-21",
            snippet="South Asian and Black queer celebration featuring live music and DJs. Community center, Southall.",
            source="Moonlight",
            published_date="2026-02-10",
        ),
        # Medium quality - date in URL
        SearchResult(
            title="Black Pride Manchester",
            url="https://eventbrite.co.uk/events/2026-01-17-black-pride-manchester",
            snippet="Annual celebration of Black LGBTQ+ community. Multiple venues across Manchester.",
            source="Eventbrite",
            published_date="2026-01-10",
        ),
        # Minimal info - no clear date
        SearchResult(
            title="Queer Community Gathering",
            url="https://londonlgbtqcentre.org/events/monthly-gathering",
            snippet="Join our monthly community gathering for Black LGBTQ+ people",
            source="London LGBTQ+ Centre",
            published_date="2026-01-01",
        ),
        # High relevance but unclear event date
        SearchResult(
            title="Black Trans Health Workshop",
            url="https://communityhealth.org/workshops/black-trans-health",
            snippet="Free health and wellness workshop for Black trans people. Saturday afternoon sessions.",
            source="Community Health",
            published_date="2026-01-06",
        ),
        # Duplicate-like result (same event, different source)
        SearchResult(
            title="BBZ Party - Black Celebration",
            url="https://facebook.com/bbz-london-event",
            snippet="BBZ party celebrating Black queer culture January 7th",
            source="Facebook",
            published_date="2026-01-04",
        ),
        # Low relevance result mixed in
        SearchResult(
            title="LGBT History Month Events Schedule",
            url="https://bbc.co.uk/news/uk-lgbt-history",
            snippet="National LGBT history month programming across the UK",
            source="BBC",
            published_date="2025-12-20",
        ),
        # Event with multiple dates (registration vs event)
        SearchResult(
            title="Misery London: Register by Jan 5 for Jan 10 Event",
            url="https://outsavvy.com/misery-london-jan-2026",
            snippet="Registration deadline January 5, 2026. Event date January 10, 2026",
            source="OutSavvy",
            published_date="2025-12-28",
        ),
        # Very recent event with past date (outdated)
        SearchResult(
            title="Pride Parade Recap - What You Missed",
            url="https://news.org/pride-recap-2025",
            snippet="Highlights from last month's Black Pride parade",
            source="News",
            published_date="2025-08-15",
        ),
        # Sparse info
        SearchResult(
            title="Black Queer London",
            url="https://blackqueer.london/events",
            snippet="Events and information for Black queer people in London",
            source="Black Queer London",
            published_date="2026-01-01",
        ),
    ]


# ============================================================================
# NEWS SEARCH RESULTS - Various relevance levels
# ============================================================================

def get_sample_news_search_results():
    """Get diverse sample news results for testing relevance filtering"""
    return [
        # Highly relevant - explicit intersectional content
        SearchResult(
            title="Black LGBTQ+ Organization Launches Mental Health Services",
            url="https://bknews.org/black-lgbtq-mental-health",
            snippet="BLKOUT announces new mental health support services specifically for Black queer men in the UK.",
            source="BK News",
            published_date="2026-01-06",
        ),
        # Highly relevant - QTIPOC focus
        SearchResult(
            title="QTIPOC UK Conference Announces 2026 Speakers",
            url="https://qtipocuk.org/conference-2026",
            snippet="Keynote speakers from across the Black and Indigenous queer community gather for annual conference.",
            source="QTIPOC UK",
            published_date="2026-01-05",
        ),
        # Medium relevance - Black and LGBTQ+ but not UK specific
        SearchResult(
            title="Global Black Trans Rights Movement Gains Momentum",
            url="https://international.news/black-trans-rights",
            snippet="International Black trans activists discuss strategies for liberation and rights",
            source="International News",
            published_date="2026-01-04",
        ),
        # Medium relevance - UK and LGBTQ+ but not Black focused
        SearchResult(
            title="New LGBTQ+ Support Center Opens in Manchester",
            url="https://manchesternews.co.uk/lgbtq-center",
            snippet="Community center launches with counseling and support services for LGBTQ+ people",
            source="Manchester News",
            published_date="2026-01-03",
        ),
        # Low relevance - only one component
        SearchResult(
            title="Black History Month Events Across Britain",
            url="https://culturalnews.org/bh-month-2025",
            snippet="Celebrate Black British culture with events happening nationwide",
            source="Cultural News",
            published_date="2025-10-15",
        ),
        # Low relevance - mentions LGBTQ+ but generic
        SearchResult(
            title="Pride Month Planning Begins for 2026",
            url="https://pride.org/planning-2026",
            snippet="Organizations worldwide start planning Pride celebrations for summer 2026",
            source="Pride News",
            published_date="2025-12-10",
        ),
        # Low relevance - not related to BLKOUT community
        SearchResult(
            title="Tech Companies Release Diversity Reports",
            url="https://tech.news/diversity-reports-2026",
            snippet="Major tech companies publish annual diversity statistics",
            source="Tech News",
            published_date="2026-01-02",
        ),
        # Very low relevance - random UK news
        SearchResult(
            title="Weather Forecast: Rain Expected Next Week",
            url="https://weather.bbc.co.uk/forecast",
            snippet="UK weather service predicts rainy conditions for next 7 days",
            source="BBC Weather",
            published_date="2026-01-06",
        ),
        # Relevant - Black health initiative
        SearchResult(
            title="Black Gay Men HIV Prevention Initiative Expands",
            url="https://health.org/black-gay-men-hiv",
            snippet="New UK-wide initiative provides free testing and support for Black gay men",
            source="Health News",
            published_date="2026-01-01",
        ),
        # Relevant - Black queer arts and culture
        SearchResult(
            title="Black Queer Artists Collaborate on New Film Project",
            url="https://artsnews.org/black-queer-film",
            snippet="Black LGBTQ+ filmmakers from London, Manchester, and Bristol join forces for groundbreaking project",
            source="Arts News",
            published_date="2025-12-28",
        ),
    ]


# ============================================================================
# DEDUPLICATION TEST DATA - URLs and variations
# ============================================================================

def get_duplicate_event_pairs():
    """Get event pairs that should be deduplicated"""
    return [
        # Exact URL duplicates
        (
            SearchResult(
                title="BBZ Party Version 1",
                url="https://outsavvy.com/event/bbz-jan-7",
                snippet="BBZ party",
                source="OutSavvy",
            ),
            SearchResult(
                title="BBZ Party Version 2",
                url="https://outsavvy.com/event/bbz-jan-7",  # Exact match
                snippet="BBZ party updated",
                source="OutSavvy",
            ),
            True,  # Should deduplicate
        ),
        # Different events (should NOT deduplicate)
        (
            SearchResult(
                title="BBZ Party January 7",
                url="https://outsavvy.com/event/bbz-jan-7",
                snippet="Party on Jan 7",
                source="OutSavvy",
            ),
            SearchResult(
                title="BBZ Party January 14",
                url="https://outsavvy.com/event/bbz-jan-14",
                snippet="Party on Jan 14",
                source="OutSavvy",
            ),
            False,  # Should NOT deduplicate
        ),
        # Same event, different domain (should NOT deduplicate - different URLs)
        (
            SearchResult(
                title="Event",
                url="https://outsavvy.com/event/party",
                snippet="party",
                source="OutSavvy",
            ),
            SearchResult(
                title="Event",
                url="https://facebook.com/event/party",
                snippet="party",
                source="Facebook",
            ),
            False,  # Different URLs = no dedup (unless content hash is used)
        ),
        # URL with and without trailing slash (different as strings)
        (
            SearchResult(
                title="Event",
                url="https://example.com/event/party",
                snippet="party",
                source="Example",
            ),
            SearchResult(
                title="Event",
                url="https://example.com/event/party/",
                snippet="party",
                source="Example",
            ),
            False,  # Technically different URLs (string comparison)
        ),
    ]


# ============================================================================
# DATE EXTRACTION TEST DATA - Various formats
# ============================================================================

def get_date_extraction_test_cases():
    """Get test cases for date extraction"""
    return [
        # ISO format in title
        {
            "title": "Event 2026-01-07",
            "url": "https://example.com/event",
            "snippet": "Join us",
            "expected_date": "2026-01-07",
            "extraction_source": "title",
        },
        # ISO format in URL
        {
            "title": "Party Night",
            "url": "https://outsavvy.com/event/2026-01-07-party",
            "snippet": "Join us",
            "expected_date": "2026-01-07",
            "extraction_source": "url",
        },
        # ISO format in snippet
        {
            "title": "Black Celebration",
            "url": "https://example.com/event/123",
            "snippet": "Event on 2026-01-07 at venue",
            "expected_date": "2026-01-07",
            "extraction_source": "snippet",
        },
        # Natural language - needs LLM
        {
            "title": "BBZ Party Jan 7 2026",
            "url": "https://outsavvy.com/event/bbz",
            "snippet": "Come join us",
            "expected_date": "2026-01-07",
            "extraction_source": "llm_required",
        },
        # No date
        {
            "title": "Community Event",
            "url": "https://example.com/event",
            "snippet": "Join our community",
            "expected_date": None,
            "extraction_source": "none",
        },
    ]


# ============================================================================
# RELEVANCE SCORING TEST DATA
# ============================================================================

def get_relevance_test_cases():
    """Get test cases for relevance scoring"""
    return [
        # High relevance
        {
            "title": "Black LGBTQ+ UK Community Conference",
            "snippet": "Join Black queer activists from London and Manchester",
            "expected_score_min": 85,
            "category": "high",
        },
        # High relevance - QTIPOC specific
        {
            "title": "QTIPOC Pride Celebration 2026",
            "snippet": "Annual Black Indigenous trans celebration",
            "expected_score_min": 85,
            "category": "high",
        },
        # Medium relevance - Black + LGBTQ+ (no UK)
        {
            "title": "Black Gay Men Coalition",
            "snippet": "Global organization for Black gay men",
            "expected_score_min": 70,
            "expected_score_max": 84,
            "category": "medium",
        },
        # Medium relevance - LGBTQ+ + UK (no Black)
        {
            "title": "Manchester LGBTQ+ Support",
            "snippet": "Local queer support services in Manchester",
            "expected_score_min": 40,
            "expected_score_max": 70,
            "category": "medium",
        },
        # Low relevance
        {
            "title": "Weather Forecast",
            "snippet": "Rain expected tomorrow",
            "expected_score_min": 0,
            "expected_score_max": 39,
            "category": "low",
        },
    ]


# ============================================================================
# INTEGRATION TEST DATA - Complete scenarios
# ============================================================================

def get_integration_test_scenario():
    """Get a complete scenario for integration testing"""
    return {
        "search_query": "Black LGBTQ+ UK events",
        "search_results": get_sample_event_search_results(),
        "expected_events_found": 6,  # Approximate, depends on filtering
        "expected_high_relevance": [0, 1, 2, 5],  # Indices of high-relevance results
        "expected_dates_extracted": 4,  # Number that should have dates
        "expected_after_dedup": 5,  # After removing duplicates
    }
