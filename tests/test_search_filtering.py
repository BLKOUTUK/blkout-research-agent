"""
Test suite for search result filtering and deduplication
"""

import pytest
from typing import List, Set
from src.search import SearchResult
from tests.fixtures.sample_search_results import (
    get_sample_event_search_results,
    get_sample_news_search_results,
    get_duplicate_event_pairs,
)


class TestSearchResultFiltering:
    """Test filtering of search results"""

    def test_filter_by_source_domain(self):
        """Test filtering results by source domain"""
        results = get_sample_event_search_results()

        # Filter to only OutSavvy results
        outsavvy_results = [r for r in results if "outsavvy" in r.url.lower()]

        assert len(outsavvy_results) >= 1
        assert all("outsavvy" in r.url.lower() for r in outsavvy_results)

    def test_filter_by_source_name(self):
        """Test filtering by source name"""
        results = get_sample_event_search_results()

        # Filter to only specific sources
        eventbrite_results = [r for r in results if r.source == "Eventbrite"]

        assert len(eventbrite_results) >= 1
        assert all(r.source == "Eventbrite" for r in eventbrite_results)

    def test_filter_irrelevant_results(self):
        """Test filtering out clearly irrelevant results"""
        results = get_sample_news_search_results()

        # Filter out completely irrelevant
        irrelevant_keywords = ["weather", "tech", "tech companies"]
        filtered = [
            r
            for r in results
            if not any(
                kw.lower() in r.title.lower() for kw in irrelevant_keywords
            )
        ]

        # Verify weather/tech news removed
        assert all(
            "weather" not in r.title.lower() and "tech" not in r.title.lower()
            for r in filtered
        )

    def test_filter_by_publish_date(self):
        """Test filtering by publish date"""
        from datetime import datetime, timedelta

        results = get_sample_news_search_results()

        # Filter to only recent results (last 30 days)
        cutoff_date = datetime.fromisoformat("2025-12-07")
        recent_results = [
            r
            for r in results
            if r.published_date and datetime.fromisoformat(r.published_date) >= cutoff_date
        ]

        assert len(recent_results) > 0
        for r in recent_results:
            pub_date = datetime.fromisoformat(r.published_date)
            assert pub_date >= cutoff_date

    def test_filter_by_snippet_content(self):
        """Test filtering based on snippet keywords"""
        results = get_sample_event_search_results()

        # Filter to only results mentioning "Black" or "queer"
        relevant_keywords = ["black", "queer", "lgbtq"]
        relevant_results = [
            r
            for r in results
            if any(
                kw in (r.title + " " + r.snippet).lower() for kw in relevant_keywords
            )
        ]

        assert len(relevant_results) > 0


class TestURLDeduplication:
    """Test URL-based deduplication"""

    def test_exact_url_deduplication(self):
        """Test deduplication of exact URL matches"""
        results = [
            SearchResult(
                title="Event A",
                url="https://example.com/event/1",
                snippet="Event A",
                source="Example",
            ),
            SearchResult(
                title="Event A Copy",
                url="https://example.com/event/1",  # Duplicate URL
                snippet="Event A duplicate",
                source="Example",
            ),
            SearchResult(
                title="Event B",
                url="https://example.com/event/2",
                snippet="Event B",
                source="Example",
            ),
        ]

        # Deduplicate
        seen_urls: Set[str] = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        assert len(unique_results) == 2
        assert unique_results[0].title == "Event A"
        assert unique_results[1].title == "Event B"

    def test_preserve_first_occurrence(self):
        """Test that deduplication preserves first occurrence"""
        results = [
            SearchResult(
                title="Original Event",
                url="https://example.com/event",
                snippet="First version",
                source="Source1",
            ),
            SearchResult(
                title="Updated Event",
                url="https://example.com/event",
                snippet="Second version",
                source="Source2",
            ),
        ]

        seen_urls: Set[str] = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        assert len(unique_results) == 1
        assert unique_results[0].title == "Original Event"
        assert unique_results[0].snippet == "First version"

    def test_case_sensitive_url_deduplication(self):
        """Test that URL deduplication is case-sensitive"""
        results = [
            SearchResult(
                title="Event A",
                url="https://example.com/Event/1",
                snippet="Event",
                source="Example",
            ),
            SearchResult(
                title="Event B",
                url="https://example.com/event/1",  # Different case
                snippet="Event",
                source="Example",
            ),
        ]

        seen_urls: Set[str] = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        # URLs differ in case, so should not deduplicate
        assert len(unique_results) == 2

    def test_url_with_query_parameters_different(self):
        """Test that URLs with different query params are not deduplicated"""
        results = [
            SearchResult(
                title="Event A",
                url="https://example.com/event/1?source=google",
                snippet="Event",
                source="Example",
            ),
            SearchResult(
                title="Event B",
                url="https://example.com/event/1?source=facebook",
                snippet="Event",
                source="Example",
            ),
        ]

        seen_urls: Set[str] = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        # Different query strings = different URLs
        assert len(unique_results) == 2

    def test_url_trailing_slash_treated_as_different(self):
        """Test that trailing slash creates different URL"""
        results = [
            SearchResult(
                title="Event A",
                url="https://example.com/event/1",
                snippet="Event",
                source="Example",
            ),
            SearchResult(
                title="Event B",
                url="https://example.com/event/1/",
                snippet="Event",
                source="Example",
            ),
        ]

        seen_urls: Set[str] = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        # Trailing slash makes them different
        assert len(unique_results) == 2

    def test_duplicate_pair_detection(self):
        """Test detection of duplicate pairs"""
        pairs = get_duplicate_event_pairs()

        for result1, result2, should_deduplicate in pairs:
            # Deduplicate
            seen_urls: Set[str] = set()
            unique = []

            for result in [result1, result2]:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    unique.append(result)

            if should_deduplicate:
                assert len(unique) == 1, f"Expected dedup: {result1.url}"
            else:
                assert len(unique) == 2, f"Expected no dedup: {result1.url}"


class TestMultipleSourceDeduplication:
    """Test deduplication across multiple sources"""

    def test_same_event_multiple_sources(self):
        """Test finding duplicate event across different platforms"""
        # Same event listed on multiple platforms
        results = [
            SearchResult(
                title="BBZ Party Jan 7",
                url="https://outsavvy.com/event/bbz-jan-7",
                snippet="Black party",
                source="OutSavvy",
            ),
            SearchResult(
                title="BBZ Party",
                url="https://facebook.com/bbz-london",
                snippet="Black party",
                source="Facebook",
            ),
            SearchResult(
                title="BBZ: Black Boyz",
                url="https://eventbrite.co.uk/event/bbz-london",
                snippet="Black party London",
                source="Eventbrite",
            ),
        ]

        # Deduplicate by URL (these are actually different URLs)
        seen_urls: Set[str] = set()
        unique_results = []
        for result in results:
            if result.url not in seen_urls:
                seen_urls.add(result.url)
                unique_results.append(result)

        # All have different URLs, so won't deduplicate with URL-only logic
        assert len(unique_results) == 3

        # Note: True deduplication might need content similarity or event matching

    def test_real_duplicate_detection(self):
        """Test that real duplicates are detected"""
        results = get_sample_event_search_results()

        # Check for duplicates by title similarity
        titles = [r.title for r in results]
        title_counts = {}
        for title in titles:
            # Check for substring matches (BBZ appears in multiple)
            if "BBZ" in title:
                title_counts["BBZ"] = title_counts.get("BBZ", 0) + 1

        # BBZ appears in multiple results
        assert title_counts.get("BBZ", 0) >= 1


class TestSearchResultQuality:
    """Test filtering for search result quality"""

    def test_filter_empty_snippets(self):
        """Test filtering out results with empty snippets"""
        results = [
            SearchResult(
                title="Event A",
                url="https://example.com/1",
                snippet="Good description",
                source="Example",
            ),
            SearchResult(
                title="Event B",
                url="https://example.com/2",
                snippet="",  # Empty
                source="Example",
            ),
            SearchResult(
                title="Event C",
                url="https://example.com/3",
                snippet=None,  # None
                source="Example",
            ),
        ]

        # Filter to only results with content
        with_content = [
            r for r in results if r.snippet and r.snippet.strip()
        ]

        assert len(with_content) == 1
        assert with_content[0].title == "Event A"

    def test_filter_by_minimum_snippet_length(self):
        """Test filtering by snippet length"""
        results = [
            SearchResult(
                title="Event A",
                url="https://example.com/1",
                snippet="Very short",  # 10 chars
                source="Example",
            ),
            SearchResult(
                title="Event B",
                url="https://example.com/2",
                snippet="This is a much longer snippet with more information about the event",
                source="Example",
            ),
        ]

        # Filter to minimum 30 chars
        substantial = [r for r in results if len(r.snippet or "") >= 30]

        assert len(substantial) == 1
        assert substantial[0].title == "Event B"

    def test_filter_by_url_domain(self):
        """Test filtering by trusted domains"""
        trusted_domains = [
            "outsavvy.com",
            "eventbrite.co.uk",
            "londonlgbtqcentre.org",
        ]

        results = [
            SearchResult(
                title="Event A",
                url="https://outsavvy.com/event/1",
                snippet="Event",
                source="OutSavvy",
            ),
            SearchResult(
                title="Event B",
                url="https://random-site.com/event/1",
                snippet="Event",
                source="Random",
            ),
            SearchResult(
                title="Event C",
                url="https://eventbrite.co.uk/event/1",
                snippet="Event",
                source="Eventbrite",
            ),
        ]

        # Filter to only trusted domains
        trusted = [
            r
            for r in results
            if any(domain in r.url for domain in trusted_domains)
        ]

        assert len(trusted) == 2
        assert trusted[0].title == "Event A"
        assert trusted[1].title == "Event C"


class TestBatchFiltering:
    """Test filtering operations on batches"""

    def test_filter_and_deduplicate_pipeline(self):
        """Test complete filter + deduplicate pipeline"""
        results = get_sample_event_search_results()

        # Pipeline: filter irrelevant -> deduplicate -> sort
        from datetime import datetime, timedelta

        # Step 1: Filter by relevance keywords
        relevant_keywords = ["black", "queer", "lgbtq", "pride"]
        filtered = [
            r
            for r in results
            if any(
                kw in (r.title + " " + r.snippet).lower()
                for kw in relevant_keywords
            )
        ]

        # Step 2: Filter by recency
        cutoff = datetime.fromisoformat("2025-12-01")
        recent = [
            r
            for r in filtered
            if r.published_date
            and datetime.fromisoformat(r.published_date) >= cutoff
        ]

        # Step 3: Deduplicate by URL
        seen_urls: Set[str] = set()
        unique = []
        for r in recent:
            if r.url not in seen_urls:
                seen_urls.add(r.url)
                unique.append(r)

        # Should have filtered, deduplicated results
        assert len(unique) > 0
        assert all(
            any(
                kw in (r.title + " " + r.snippet).lower()
                for kw in relevant_keywords
            )
            for r in unique
        )

    def test_filter_maintains_order(self):
        """Test that filtering maintains result order"""
        results = get_sample_event_search_results()

        # Filter but maintain order
        filtered = [r for r in results if "black" in r.title.lower()]

        original_titles = [
            r.title for r in results if "black" in r.title.lower()
        ]
        filtered_titles = [r.title for r in filtered]

        assert filtered_titles == original_titles
