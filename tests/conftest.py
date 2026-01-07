"""
Pytest configuration and fixtures for BLKOUT Research Agent tests
"""

import pytest
import asyncio
import os
from unittest.mock import Mock, AsyncMock, MagicMock
from datetime import datetime, timedelta


@pytest.fixture
def event_loop():
    """Create event loop for async tests"""
    loop = asyncio.new_event_loop()
    yield loop
    loop.close()


@pytest.fixture
def mock_llm_client():
    """Mock LLM client for testing"""
    mock = AsyncMock()
    mock.complete = AsyncMock(return_value="2026-01-07")
    mock.complete_json = AsyncMock(return_value={
        "relevance_score": 85,
        "reasoning": "Test article",
        "suggested_category": "news",
        "suggested_tags": ["test"],
        "recommended_action": "publish",
    })
    mock.analyze_relevance = AsyncMock(return_value={
        "relevance_score": 85,
        "reasoning": "Test content",
        "suggested_category": "news",
        "suggested_tags": ["black", "queer", "uk"],
        "recommended_action": "publish",
    })
    return mock


@pytest.fixture
def mock_search_agent():
    """Mock search agent for testing"""
    mock = AsyncMock()
    mock.multi_search = AsyncMock(return_value=[])
    mock.search = AsyncMock(return_value=[])
    mock.search_news = AsyncMock(return_value=[])
    return mock


@pytest.fixture
def mock_database():
    """Mock database client for testing"""
    mock = AsyncMock()
    mock.insert_articles_batch = AsyncMock(return_value={
        "inserted": 5,
        "duplicates": 2,
        "errors": 0,
    })
    mock.insert_events_batch = AsyncMock(return_value={
        "inserted": 3,
        "duplicates": 1,
        "errors": 0,
    })
    mock.log_discovery_run = AsyncMock(return_value=True)
    return mock


@pytest.fixture
def sample_search_results():
    """Sample search results for testing"""
    from src.search import SearchResult

    return [
        SearchResult(
            title="BBZ Party Jan 7 2026",
            url="https://outsavvy.com/event/bbz-jan-7",
            snippet="Join us for the BBZ party on Tuesday, January 7th at the Phoenix Bar",
            source="OutSavvy",
            published_date="2026-01-07",
        ),
        SearchResult(
            title="Black LGBTQ Pride Manchester",
            url="https://eventbrite.co.uk/events/black-pride-manchester",
            snippet="Annual Black LGBTQ Pride celebration in Manchester. January 17-19, 2026",
            source="Eventbrite",
            published_date="2026-01-15",
        ),
        SearchResult(
            title="Hunagama Queer Night",
            url="https://moonlightexperiences.com/hungama-2026",
            snippet="South Asian and Black queer celebration. Event date: 2026-02-21",
            source="Moonlight",
            published_date="2026-02-10",
        ),
        SearchResult(
            title="Black Trans Health Workshop UK",
            url="https://londonlgbtqcentre.org/workshops/trans-health",
            snippet="Free health workshop for Black trans people. Saturday Feb 7",
            source="London",
            published_date="2026-01-20",
        ),
        SearchResult(
            title="Irrelevant News Article",
            url="https://bbc.co.uk/news/world-45678",
            snippet="Breaking news about weather and traffic",
            source="BBC",
            published_date="2026-01-06",
        ),
    ]


@pytest.fixture
def sample_article_data():
    """Sample article data for relevance testing"""
    return {
        "high_relevance": {
            "title": "Black LGBTQ UK wins community award",
            "snippet": "The Black queer organization celebrates recognition in London",
            "source": "QTIPOC News",
            "url": "https://qtipocnews.org/article/1",
        },
        "medium_relevance": {
            "title": "Queer events in Manchester",
            "snippet": "Local LGBTQ+ events happening this month",
            "source": "Manchester Events",
            "url": "https://manchesterevents.org/lgbtq",
        },
        "low_relevance": {
            "title": "Weather forecast for next week",
            "snippet": "Expect rainy conditions across the UK",
            "source": "Weather.com",
            "url": "https://weather.com/forecast",
        },
    }


@pytest.fixture
def sample_event_data():
    """Sample event data for testing"""
    return {
        "complete_event": {
            "name": "BBZ: Black Boyz and Girlz",
            "url": "https://outsavvy.com/event/bbz-jan-2026",
            "venue": "Phoenix Bar",
            "city": "London",
            "date": "2026-01-07",
            "price": "Free",
            "description": "Black queer party night celebrating community",
            "source_platform": "OutSavvy",
        },
        "minimal_event": {
            "name": "Queer event",
            "url": "https://example.com/event/123",
            "venue": None,
            "city": None,
            "date": None,
            "price": None,
            "description": "A queer community event",
            "source_platform": "Web Search",
        },
        "duplicate_event": {
            "name": "BBZ Party",
            "url": "https://outsavvy.com/event/bbz-jan-2026",  # Same URL as complete_event
            "venue": "The Phoenix",
            "city": "London",
            "date": "2026-01-07",
            "price": "£5",
            "description": "Black LGBTQ party",
            "source_platform": "EventBrite",
        },
    }


@pytest.fixture
def date_extraction_samples():
    """Sample text with various date formats for testing date extraction"""
    return {
        "title_with_month_day_year": {
            "text": "BBZ Party Jan 7 2026",
            "expected": "2026-01-07",
        },
        "title_with_ordinal": {
            "text": "Hungama Queer Celebration - 21st February 2026",
            "expected": "2026-02-21",
        },
        "url_with_iso_date": {
            "text": "https://outsavvy.com/events/2026-01-07-party",
            "expected": "2026-01-07",
        },
        "url_with_slashes": {
            "text": "https://eventbrite.co.uk/events/2026/02/15/black-pride",
            "expected": "2026-02-15",
        },
        "snippet_with_day_name": {
            "text": "Join us Tuesday January 7th at 10pm",
            "expected": "2026-01-07",
        },
        "snippet_with_full_date": {
            "text": "Event happening on 2026-03-14 at the community center",
            "expected": "2026-03-14",
        },
        "multiple_dates": {
            "text": "Registration opens Jan 5, event on Jan 7 2026",
            "expected": "2026-01-07",
        },
        "no_date": {
            "text": "Come celebrate with us at the venue",
            "expected": None,
        },
        "past_date": {
            "text": "Event was on Jan 1 2020",
            "expected": None,
        },
        "relative_date": {
            "text": "Next Tuesday at 6pm",
            "expected": None,
        },
    }
