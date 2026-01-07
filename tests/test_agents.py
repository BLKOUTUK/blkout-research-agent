"""
Test suite for BLKOUT Research Agents
Tests: Date extraction, event deduplication, relevance filtering, search result processing
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock

from src.agents import (
    NewsResearchAgent,
    EventsDiscoveryAgent,
    DiscoveredArticle,
    DiscoveredEvent,
)
from src.search import SearchResult


class TestNewsResearchAgent:
    """Test news research agent functionality"""

    @pytest.mark.asyncio
    async def test_quick_relevance_check_high_relevance(self, mock_llm_client):
        """Test high-relevance keyword detection"""
        agent = NewsResearchAgent()

        # Test high-relevance intersectional terms
        score = agent._quick_relevance_check("black queer UK community")
        assert score == 95

        score = agent._quick_relevance_check("QTIPOC events London")
        assert score == 95

        score = agent._quick_relevance_check("Black trans pride celebration")
        assert score == 95

    @pytest.mark.asyncio
    async def test_quick_relevance_check_medium_relevance(self):
        """Test medium-relevance keyword combination detection"""
        agent = NewsResearchAgent()

        # Both Black and LGBTQ+ present, with UK = 85
        score = agent._quick_relevance_check("Black gay events in London")
        assert score == 85

        # Both Black and LGBTQ+ present, no UK = 75
        score = agent._quick_relevance_check("Black lesbian festival Brazil")
        assert score == 75

    @pytest.mark.asyncio
    async def test_quick_relevance_check_low_relevance(self):
        """Test low-relevance keyword detection"""
        agent = NewsResearchAgent()

        # Only Black mentioned
        score = agent._quick_relevance_check("Black Friday sales")
        assert score == 40

        # Only LGBTQ+ mentioned
        score = agent._quick_relevance_check("Pride parade information")
        assert score == 40

        # Completely irrelevant
        score = agent._quick_relevance_check("Weather forecast and traffic")
        assert score == 20

    @pytest.mark.asyncio
    async def test_quick_relevance_check_case_insensitive(self):
        """Test that relevance check is case-insensitive"""
        agent = NewsResearchAgent()

        score_lower = agent._quick_relevance_check("black queer uk")
        score_upper = agent._quick_relevance_check("BLACK QUEER UK")
        score_mixed = agent._quick_relevance_check("BlAcK qUeEr Uk")

        assert score_lower == score_upper == score_mixed == 95

    @pytest.mark.asyncio
    async def test_research_filters_by_relevance(self, mock_llm_client, sample_search_results):
        """Test that research properly filters results by relevance"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.SearchAgent") as mock_search_class:
                with patch("src.agents.get_database"):
                    agent = NewsResearchAgent()

                    # Mock search to return sample results
                    mock_search_class.return_value.multi_search = AsyncMock(
                        return_value=sample_search_results
                    )
                    agent.search = mock_search_class.return_value

                    articles = await agent.research(time_range="w")

                    # Should filter out irrelevant content
                    assert all(a.relevance_score >= 40 for a in articles)

                    # Irrelevant articles should be excluded
                    titles = [a.title for a in articles]
                    assert "Irrelevant News Article" not in titles

    @pytest.mark.asyncio
    async def test_research_result_structure(self, mock_llm_client):
        """Test that discovered articles have correct structure"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.SearchAgent") as mock_search_class:
                with patch("src.agents.get_database"):
                    agent = NewsResearchAgent()

                    # Create a high-relevance search result
                    result = SearchResult(
                        title="Black queer UK wins award",
                        url="https://example.com/article",
                        snippet="The community celebrates",
                        source="BLKOUT",
                        published_date="2026-01-07",
                    )

                    mock_search_class.return_value.multi_search = AsyncMock(
                        return_value=[result]
                    )
                    agent.search = mock_search_class.return_value

                    articles = await agent.research(time_range="w")

                    assert len(articles) > 0
                    article = articles[0]
                    assert article.title == "Black queer UK wins award"
                    assert article.url == "https://example.com/article"
                    assert article.source == "BLKOUT"
                    assert article.snippet == "The community celebrates"
                    assert article.published_date == "2026-01-07"
                    assert isinstance(article.relevance_score, int)
                    assert 0 <= article.relevance_score <= 100


class TestEventsDiscoveryAgent:
    """Test events discovery agent functionality"""

    @pytest.mark.asyncio
    async def test_extract_date_iso_format(self, mock_llm_client):
        """Test date extraction with ISO format response"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.get_database"):
                agent = EventsDiscoveryAgent()
                agent.llm = mock_llm_client
                mock_llm_client.complete = AsyncMock(return_value="2026-01-07")

                date = await agent._extract_date_from_text(
                    "BBZ Party Jan 7 2026"
                )

                assert date == "2026-01-07"

    @pytest.mark.asyncio
    async def test_extract_date_no_date_found(self, mock_llm_client):
        """Test date extraction when no date found"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.get_database"):
                agent = EventsDiscoveryAgent()
                agent.llm = mock_llm_client
                mock_llm_client.complete = AsyncMock(return_value="none")

                date = await agent._extract_date_from_text(
                    "Come party with us sometime"
                )

                assert date is None

    @pytest.mark.asyncio
    async def test_extract_date_invalid_format(self, mock_llm_client):
        """Test date extraction with invalid format response"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.get_database"):
                agent = EventsDiscoveryAgent()
                agent.llm = mock_llm_client
                mock_llm_client.complete = AsyncMock(return_value="January 7, 2026")

                date = await agent._extract_date_from_text(
                    "Event on January 7, 2026"
                )

                # Should return None if not ISO format
                assert date is None

    @pytest.mark.asyncio
    async def test_extract_date_empty_response(self, mock_llm_client):
        """Test date extraction with empty response"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.get_database"):
                agent = EventsDiscoveryAgent()
                agent.llm = mock_llm_client
                mock_llm_client.complete = AsyncMock(return_value="")

                date = await agent._extract_date_from_text("Some text")

                assert date is None

    @pytest.mark.asyncio
    async def test_discover_from_search_extracts_dates(self, mock_llm_client, sample_search_results):
        """Test that discovery from search extracts dates from results"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.EventSearchAgent") as mock_search_class:
                with patch("src.agents.get_database"):
                    agent = EventsDiscoveryAgent()
                    agent.llm = mock_llm_client

                    # Mock search to return results
                    mock_search_class.return_value.search_qtipoc_events = AsyncMock(
                        return_value=sample_search_results[:3]
                    )
                    agent.search = mock_search_class.return_value

                    # Mock date extraction
                    mock_llm_client.complete = AsyncMock(return_value="2026-01-07")

                    events = await agent.discover_from_search()

                    assert len(events) == 3
                    # First two should have extracted dates
                    assert events[0].date == "2026-01-07"
                    assert events[1].date == "2026-01-07"

    @pytest.mark.asyncio
    async def test_discover_all_deduplicates_by_url(self, mock_llm_client, sample_event_data):
        """Test that discover_all deduplicates events by URL"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.EventSearchAgent"):
                with patch("src.agents.ScraperAgent"):
                    with patch("src.agents.get_database"):
                        agent = EventsDiscoveryAgent()

                        # Create events with duplicate URLs
                        event1 = DiscoveredEvent(
                            name="BBZ Party",
                            url="https://outsavvy.com/event/bbz-jan-7",
                            venue="Phoenix Bar",
                            date="2026-01-07",
                        )

                        event2 = DiscoveredEvent(
                            name="BBZ: Black Boyz and Girlz",
                            url="https://outsavvy.com/event/bbz-jan-7",  # Same URL
                            venue="The Phoenix",
                            date="2026-01-07",
                        )

                        event3 = DiscoveredEvent(
                            name="Hungama Queer",
                            url="https://moonlight.com/event/hungama",
                            venue="Community Center",
                            date="2026-02-21",
                        )

                        # Mock discover methods to return events
                        agent.discover_from_search = AsyncMock(
                            return_value=[event1, event2]
                        )
                        agent.discover_from_scraping = AsyncMock(
                            return_value=[event3]
                        )

                        unique_events = await agent.discover_all()

                        # Should deduplicate by URL (keep first occurrence)
                        assert len(unique_events) == 2
                        urls = [e.url for e in unique_events]
                        assert urls.count("https://outsavvy.com/event/bbz-jan-7") == 1

    @pytest.mark.asyncio
    async def test_discover_all_handles_errors_gracefully(self):
        """Test that discover_all handles search/scrape errors gracefully"""
        with patch("src.agents.get_llm_client"):
            with patch("src.agents.EventSearchAgent"):
                with patch("src.agents.ScraperAgent"):
                    with patch("src.agents.get_database"):
                        agent = EventsDiscoveryAgent()

                        # Mock one method to raise error, other to succeed
                        agent.discover_from_search = AsyncMock(
                            side_effect=Exception("Search error")
                        )
                        agent.discover_from_scraping = AsyncMock(
                            return_value=[
                                DiscoveredEvent(
                                    name="Test Event",
                                    url="https://example.com/event",
                                )
                            ]
                        )

                        # Should not raise error, should include scrape results
                        events = await agent.discover_all()

                        assert len(events) == 1
                        assert events[0].name == "Test Event"

    @pytest.mark.asyncio
    async def test_discover_event_result_structure(self, mock_llm_client, sample_search_results):
        """Test that discovered events have correct structure"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.EventSearchAgent") as mock_search_class:
                with patch("src.agents.get_database"):
                    agent = EventsDiscoveryAgent()
                    agent.llm = mock_llm_client

                    result = sample_search_results[0]
                    mock_search_class.return_value.search_qtipoc_events = AsyncMock(
                        return_value=[result]
                    )
                    agent.search = mock_search_class.return_value
                    mock_llm_client.complete = AsyncMock(return_value="2026-01-07")

                    events = await agent.discover_from_search()

                    assert len(events) > 0
                    event = events[0]
                    assert event.name == result.title
                    assert event.url == result.url
                    assert event.description == result.snippet
                    assert event.source_platform == "Web Search"
                    assert isinstance(event.relevance_score, int)
                    assert event.relevance_score >= 0

    @pytest.mark.asyncio
    async def test_events_batch_insert_called_on_save(self, mock_llm_client, mock_database):
        """Test that discover_and_save calls database batch insert"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.EventSearchAgent"):
                with patch("src.agents.ScraperAgent"):
                    with patch("src.agents.get_database", return_value=mock_database):
                        agent = EventsDiscoveryAgent()

                        # Create test events
                        test_event = DiscoveredEvent(
                            name="Test Event",
                            url="https://example.com/event",
                            date="2026-01-07",
                        )

                        agent.discover_all = AsyncMock(return_value=[test_event])

                        result = await agent.discover_and_save()

                        # Verify database methods were called
                        mock_database.insert_events_batch.assert_called_once()
                        mock_database.log_discovery_run.assert_called_once()

                        # Verify result structure
                        assert "discovered" in result
                        assert result["discovered"] == 1


class TestDeduplication:
    """Test URL-based deduplication"""

    def test_deduplication_preserves_first_occurrence(self):
        """Test that deduplication keeps the first occurrence"""
        events = [
            DiscoveredEvent(name="Event A", url="https://example.com/1", date="2026-01-01"),
            DiscoveredEvent(name="Event B", url="https://example.com/1", date="2026-01-01"),
            DiscoveredEvent(name="Event C", url="https://example.com/2", date="2026-01-02"),
        ]

        seen_urls = set()
        unique_events = []
        for event in events:
            if event.url not in seen_urls:
                seen_urls.add(event.url)
                unique_events.append(event)

        assert len(unique_events) == 2
        assert unique_events[0].name == "Event A"
        assert unique_events[1].name == "Event C"

    def test_deduplication_with_url_variations(self):
        """Test deduplication doesn't match URL variations"""
        events = [
            DiscoveredEvent(name="Event A", url="https://example.com/event"),
            DiscoveredEvent(name="Event B", url="https://example.com/event?utm=1"),
            DiscoveredEvent(name="Event C", url="https://example.com/event/"),
        ]

        seen_urls = set()
        unique_events = []
        for event in events:
            if event.url not in seen_urls:
                seen_urls.add(event.url)
                unique_events.append(event)

        # URLs are different (query params matter), should not deduplicate
        assert len(unique_events) == 3

    def test_deduplication_case_sensitive(self):
        """Test that deduplication is case-sensitive"""
        events = [
            DiscoveredEvent(name="Event A", url="https://example.com/Event"),
            DiscoveredEvent(name="Event B", url="https://example.com/event"),
        ]

        seen_urls = set()
        unique_events = []
        for event in events:
            if event.url not in seen_urls:
                seen_urls.add(event.url)
                unique_events.append(event)

        # Different cases = different URLs in dedup logic
        assert len(unique_events) == 2


class TestErrorHandling:
    """Test error handling in agents"""

    @pytest.mark.asyncio
    async def test_news_agent_llm_error_fallback(self, mock_llm_client):
        """Test that news agent handles LLM errors gracefully"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.SearchAgent") as mock_search_class:
                with patch("src.agents.get_database"):
                    agent = NewsResearchAgent()

                    # Create result that passes quick filter but LLM fails
                    result = SearchResult(
                        title="Black trans health UK initiative",
                        url="https://example.com/article",
                        snippet="Community health services",
                        source="Health",
                        published_date="2026-01-07",
                    )

                    mock_search_class.return_value.multi_search = AsyncMock(
                        return_value=[result]
                    )
                    agent.search = mock_search_class.return_value

                    # Make LLM fail
                    mock_llm_client.analyze_relevance = AsyncMock(
                        side_effect=Exception("API error")
                    )

                    articles = await agent.research(time_range="w")

                    # Should still include article with fallback score
                    assert len(articles) > 0
                    assert articles[0].title == "Black trans health UK initiative"

    @pytest.mark.asyncio
    async def test_events_agent_date_extraction_error_fallback(self, mock_llm_client):
        """Test that events agent handles date extraction errors"""
        with patch("src.agents.get_llm_client", return_value=mock_llm_client):
            with patch("src.agents.EventSearchAgent") as mock_search_class:
                with patch("src.agents.get_database"):
                    agent = EventsDiscoveryAgent()
                    agent.llm = mock_llm_client

                    result = SearchResult(
                        title="Community Event",
                        url="https://example.com/event",
                        snippet="Join us for celebration",
                        source="Community",
                    )

                    mock_search_class.return_value.search_qtipoc_events = AsyncMock(
                        return_value=[result]
                    )
                    agent.search = mock_search_class.return_value

                    # Make date extraction fail
                    mock_llm_client.complete = AsyncMock(side_effect=Exception("API error"))

                    events = await agent.discover_from_search()

                    # Should still create event with None date
                    assert len(events) > 0
                    assert events[0].name == "Community Event"
                    assert events[0].date is None
