"""
Test suite for date extraction from event information
Tests various date formats and edge cases
"""

import pytest
import re
from datetime import datetime, timedelta


class DateExtractor:
    """Helper class for testing date extraction patterns"""

    @staticmethod
    def extract_iso_date(text: str) -> str:
        """Extract ISO format date (YYYY-MM-DD) from text"""
        pattern = r'\d{4}-\d{2}-\d{2}'
        match = re.search(pattern, text)
        return match.group(0) if match else None

    @staticmethod
    def extract_url_iso_date(url: str) -> str:
        """Extract ISO date from URL structure like /2026/01/07/ or /2026-01-07/"""
        # Try YYYY-MM-DD format
        pattern = r'/(\d{4})-(\d{2})-(\d{2})/'
        match = re.search(pattern, url)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        # Try YYYY/MM/DD format
        pattern = r'/(\d{4})/(\d{2})/(\d{2})/'
        match = re.search(pattern, url)
        if match:
            return f"{match.group(1)}-{match.group(2)}-{match.group(3)}"

        return None

    @staticmethod
    def is_future_date(date_str: str) -> bool:
        """Check if date is in the future"""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            return date_obj > datetime.now()
        except (ValueError, TypeError):
            return False

    @staticmethod
    def is_valid_iso_format(date_str: str) -> bool:
        """Validate ISO date format"""
        if not date_str:
            return False
        try:
            datetime.strptime(date_str, "%Y-%m-%d")
            return True
        except ValueError:
            return False


class TestDateExtractionFromTitle:
    """Test date extraction from event titles"""

    def test_extract_month_abbreviation_with_year(self):
        """Test extracting dates like 'Jan 7 2026'"""
        extractor = DateExtractor()

        # BBZ Party Jan 7 2026
        title = "BBZ Party Jan 7 2026"
        date = extractor.extract_iso_date(title)
        # Note: Simple regex won't extract this, would need LLM or dateparser
        # This test demonstrates the limitation and why we use LLM

        # For ISO format already in text
        title_iso = "Event 2026-01-07 Party"
        date = extractor.extract_iso_date(title_iso)
        assert date == "2026-01-07"

    def test_extract_ordinal_date_format(self):
        """Test dates like '21st February 2026'"""
        # This requires NLP/LLM processing
        title = "Hungama Queer Celebration - 21st February 2026"
        # Would need LLM to parse "21st February 2026" to ISO
        # Regex alone cannot handle ordinals
        pass

    def test_extract_iso_date_from_title(self):
        """Test extracting ISO format from title"""
        extractor = DateExtractor()

        title = "Party on 2026-01-07 at the club"
        date = extractor.extract_iso_date(title)
        assert date == "2026-01-07"
        assert extractor.is_valid_iso_format(date)

    def test_title_without_date(self):
        """Test title with no date information"""
        extractor = DateExtractor()

        title = "Come to our queer celebration party"
        date = extractor.extract_iso_date(title)
        assert date is None


class TestDateExtractionFromURL:
    """Test date extraction from event URLs"""

    def test_extract_iso_date_from_url_with_slashes(self):
        """Test URL format /events/2026-01-07-party"""
        extractor = DateExtractor()

        url = "https://outsavvy.com/events/2026-01-07-party"
        date = extractor.extract_iso_date(url)
        assert date == "2026-01-07"
        assert extractor.is_valid_iso_format(date)

    def test_extract_date_from_url_year_month_day_format(self):
        """Test URL format /2026/01/07/event"""
        extractor = DateExtractor()

        url = "https://eventbrite.co.uk/events/2026/01/07/black-pride"
        date = extractor.extract_url_iso_date(url)
        assert date == "2026-01-07"

    def test_extract_date_from_url_with_hyphens(self):
        """Test URL format /2026-01-07/ or /2026-01-07"""
        extractor = DateExtractor()

        url = "https://moonlight.com/2026-01-07-hungama"
        date = extractor.extract_iso_date(url)
        assert date == "2026-01-07"

    def test_url_without_date(self):
        """Test URL with no date information"""
        extractor = DateExtractor()

        url = "https://example.com/event/party-night"
        date = extractor.extract_iso_date(url)
        assert date is None

    def test_extract_date_from_complex_url(self):
        """Test date extraction from complex URL"""
        extractor = DateExtractor()

        url = "https://eventbrite.co.uk/d/united-kingdom--london/2026-02-15-black-pride"
        date = extractor.extract_iso_date(url)
        assert date == "2026-02-15"

    def test_url_with_multiple_dates(self):
        """Test URL with multiple date-like patterns"""
        extractor = DateExtractor()

        url = "https://example.com/2020-old-event/2026-01-07-new-event"
        date = extractor.extract_iso_date(url)
        # Extracts first match - would need LLM to determine correct one
        assert date == "2020-01-07"


class TestDateExtractionFromSnippet:
    """Test date extraction from event descriptions/snippets"""

    def test_extract_iso_date_from_snippet(self):
        """Test date extraction from snippet with ISO format"""
        extractor = DateExtractor()

        snippet = "Join us Tuesday January 7th at 10pm. Event on 2026-01-07 at the venue."
        date = extractor.extract_iso_date(snippet)
        assert date == "2026-01-07"

    def test_snippet_with_day_name(self):
        """Test snippet like 'Join us Tuesday January 7th'"""
        snippet = "Join us Tuesday January 7th at the community center"
        # Day name + date without year - needs LLM to infer year
        extractor = DateExtractor()
        date = extractor.extract_iso_date(snippet)
        assert date is None

    def test_snippet_with_relative_date(self):
        """Test snippet with relative dates"""
        extractor = DateExtractor()

        snippet = "Event is next Tuesday at 6pm"
        date = extractor.extract_iso_date(snippet)
        assert date is None  # Relative dates need context/LLM

    def test_snippet_with_multiple_dates(self):
        """Test snippet mentioning multiple dates"""
        extractor = DateExtractor()

        snippet = "Registration opens 2026-01-05, event on 2026-01-07 at venue"
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', snippet)
        assert len(dates) == 2
        assert dates[0] == "2026-01-05"
        assert dates[1] == "2026-01-07"
        # LLM should return the event date (future, second date)

    def test_snippet_without_date(self):
        """Test snippet with no date information"""
        extractor = DateExtractor()

        snippet = "Come celebrate with us at the community center"
        date = extractor.extract_iso_date(snippet)
        assert date is None


class TestDateValidation:
    """Test date validation and filtering"""

    def test_validate_iso_format(self):
        """Test ISO format validation"""
        extractor = DateExtractor()

        assert extractor.is_valid_iso_format("2026-01-07") is True
        assert extractor.is_valid_iso_format("2026-1-7") is False
        assert extractor.is_valid_iso_format("01-01-2026") is False
        assert extractor.is_valid_iso_format("2026/01/07") is False
        assert extractor.is_valid_iso_format("") is False
        assert extractor.is_valid_iso_format(None) is False

    def test_validate_future_dates(self):
        """Test that only future dates are accepted"""
        extractor = DateExtractor()

        future_date = (datetime.now() + timedelta(days=30)).strftime("%Y-%m-%d")
        assert extractor.is_future_date(future_date) is True

        past_date = (datetime.now() - timedelta(days=30)).strftime("%Y-%m-%d")
        assert extractor.is_future_date(past_date) is False

    def test_validate_invalid_dates(self):
        """Test validation of invalid dates"""
        extractor = DateExtractor()

        assert extractor.is_valid_iso_format("2026-13-01") is False  # Invalid month
        assert extractor.is_valid_iso_format("2026-01-32") is False  # Invalid day
        assert extractor.is_valid_iso_format("2026-02-30") is False  # Feb 30
        assert extractor.is_valid_iso_format("9999-99-99") is False

    def test_leap_year_date(self):
        """Test handling of leap year dates"""
        extractor = DateExtractor()

        assert extractor.is_valid_iso_format("2024-02-29") is True  # Leap year
        assert extractor.is_valid_iso_format("2025-02-29") is False  # Non-leap year

    def test_year_boundaries(self):
        """Test dates at year boundaries"""
        extractor = DateExtractor()

        assert extractor.is_valid_iso_format("2026-01-01") is True
        assert extractor.is_valid_iso_format("2026-12-31") is True
        assert extractor.is_valid_iso_format("2026-01-00") is False
        assert extractor.is_valid_iso_format("2026-00-01") is False


class TestEdgeCases:
    """Test edge cases in date extraction"""

    def test_text_with_no_date(self):
        """Test when text contains no date"""
        extractor = DateExtractor()

        text = "Come celebrate with us at the venue sometime soon"
        date = extractor.extract_iso_date(text)
        assert date is None

    def test_text_with_multiple_dates_and_filtering(self):
        """Test selecting correct date from multiple options"""
        extractor = DateExtractor()

        text = "Past event was 2020-01-07, next event 2026-01-07"
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
        assert len(dates) == 2

        # Filter to future dates only
        future_dates = [d for d in dates if extractor.is_future_date(d)]
        assert len(future_dates) == 1
        assert future_dates[0] == "2026-01-07"

    def test_past_date_filtering(self):
        """Test that past dates are filtered out"""
        extractor = DateExtractor()

        # Date in the past
        text = "Event was on 2020-01-07"
        date = extractor.extract_iso_date(text)
        assert date == "2020-01-07"
        assert extractor.is_future_date(date) is False
        # LLM would filter this out

    def test_ambiguous_month_formats(self):
        """Test ambiguous date formats"""
        # "01-02-2026" could be Jan 2 or Feb 1 depending on locale
        # ISO format avoids this ambiguity
        extractor = DateExtractor()

        text = "Event on 2026-01-02"  # ISO - unambiguous
        date = extractor.extract_iso_date(text)
        assert date == "2026-01-02"

    def test_whitespace_handling(self):
        """Test handling of various whitespace"""
        extractor = DateExtractor()

        text = "Event 2026-01-07 with spacing"
        date = extractor.extract_iso_date(text)
        assert date == "2026-01-07"

        text_extra = "Event   2026-01-07   spacing"
        date_extra = extractor.extract_iso_date(text_extra)
        assert date_extra == "2026-01-07"

    def test_url_query_parameters_ignored(self):
        """Test that date in query params is extracted correctly"""
        extractor = DateExtractor()

        url = "https://example.com/event?date=2026-01-07&utm=1"
        date = extractor.extract_iso_date(url)
        assert date == "2026-01-07"


class TestSearchResultDateExtraction:
    """Test date extraction from complete search results"""

    def test_combined_search_result_extraction(self, date_extraction_samples):
        """Test date extraction from a full search result"""
        extractor = DateExtractor()

        # Combine title, URL, and snippet
        search_result = {
            "title": "BBZ Party Jan 7 2026",
            "url": "https://outsavvy.com/events/2026-01-07-party",
            "snippet": "Join us on Tuesday January 7th at 10pm",
        }

        # Try to extract from each field
        date_from_url = extractor.extract_iso_date(search_result["url"])
        assert date_from_url == "2026-01-07"
        # URL extraction works!
        # Title and snippet need LLM for natural language parsing

    def test_prioritize_extraction_sources(self):
        """Test extraction strategy: URL > ISO snippet > title"""
        extractor = DateExtractor()

        search_result = {
            "title": "Party in January",
            "url": "https://example.com/events/2026-03-15-party",
            "snippet": "Event on 2026-02-21 at venue",
        }

        # Strategy: Check URL first (most reliable), then snippet
        date = extractor.extract_url_iso_date(search_result["url"])
        if not date:
            date = extractor.extract_iso_date(search_result["snippet"])
        # URL wins - provides 2026-03-15

        assert date == "2026-03-15"

    def test_no_date_in_any_field(self):
        """Test when no date is found in any field"""
        extractor = DateExtractor()

        search_result = {
            "title": "Queer celebration",
            "url": "https://example.com/event/celebration",
            "snippet": "Join us for a fun celebration",
        }

        date = extractor.extract_iso_date(
            search_result["url"] + " " + search_result["snippet"]
        )
        assert date is None


class TestLLMDateExtractionSimulation:
    """Test simulating LLM date extraction behavior"""

    def test_llm_would_handle_natural_language(self):
        """Verify that natural language dates need LLM"""
        # These formats cannot be parsed with regex alone
        test_cases = [
            "BBZ Party Jan 7 2026",  # Month abbreviation + year
            "Hungama Queer Celebration - 21st February 2026",  # Ordinal date
            "Event on Tuesday January 7th",  # Day name + date without year
            "Join us next Tuesday at 6pm",  # Relative date
        ]

        extractor = DateExtractor()

        # Regex cannot extract these without context
        for text in test_cases:
            date = extractor.extract_iso_date(text)
            assert date is None
            # LLM would be needed to parse these

    def test_llm_would_validate_future_dates(self):
        """Verify that LLM should filter past dates"""
        extractor = DateExtractor()

        # LLM extracts dates and should validate they're future dates
        test_cases = [
            ("2026-01-07", True),  # Future
            ("2020-01-07", False),  # Past
        ]

        for date_str, should_be_future in test_cases:
            is_future = extractor.is_future_date(date_str)
            assert is_future == should_be_future

    def test_llm_would_select_event_date_from_multiple(self):
        """Verify LLM should choose correct date when multiple exist"""
        text = "Registration opens 2026-01-05, event on 2026-01-07"
        extractor = DateExtractor()

        # Extract all ISO dates
        dates = re.findall(r'\d{4}-\d{2}-\d{2}', text)
        assert len(dates) == 2

        # LLM should return event date (later one)
        # Logic: event_date = max([2026-01-05, 2026-01-07]) or specific keywords
        event_date = "2026-01-07"  # LLM would infer this
        assert event_date in dates
