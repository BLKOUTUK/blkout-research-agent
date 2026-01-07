"""
Search Agent - Web search using DuckDuckGo (free, no API key needed)
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta
from ddgs import DDGS


@dataclass
class SearchResult:
    title: str
    url: str
    snippet: str
    source: str
    published_date: Optional[str] = None


class SearchAgent:
    """Web search agent using DuckDuckGo"""

    def __init__(self, max_results: int = 10):
        self.max_results = max_results
        self.ddgs = DDGS()

    async def search(
        self,
        query: str,
        region: str = "uk-en",
        time_range: Optional[str] = "m",  # d=day, w=week, m=month
    ) -> List[SearchResult]:
        """Execute a search query"""
        try:
            # Run sync DuckDuckGo in thread pool
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.text(
                    query,
                    region=region,
                    timelimit=time_range,
                    max_results=self.max_results,
                ))
            )

            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("href", ""),
                    snippet=r.get("body", ""),
                    source=self._extract_source(r.get("href", "")),
                )
                for r in results
            ]
        except Exception as e:
            print(f"Search error for '{query}': {e}")
            return []

    async def search_news(
        self,
        query: str,
        region: str = "uk-en",
        time_range: Optional[str] = "m",
    ) -> List[SearchResult]:
        """Search news specifically"""
        try:
            loop = asyncio.get_event_loop()
            results = await loop.run_in_executor(
                None,
                lambda: list(self.ddgs.news(
                    query,
                    region=region,
                    timelimit=time_range,
                    max_results=self.max_results,
                ))
            )

            return [
                SearchResult(
                    title=r.get("title", ""),
                    url=r.get("url", ""),
                    snippet=r.get("body", ""),
                    source=r.get("source", self._extract_source(r.get("url", ""))),
                    published_date=r.get("date"),
                )
                for r in results
            ]
        except Exception as e:
            print(f"News search error for '{query}': {e}")
            return []

    async def multi_search(
        self,
        queries: List[str],
        search_type: str = "web",  # "web" or "news"
        region: str = "uk-en",
        time_range: Optional[str] = "m",
    ) -> List[SearchResult]:
        """Execute multiple searches and deduplicate results"""
        all_results = []
        seen_urls = set()

        search_fn = self.search_news if search_type == "news" else self.search

        for query in queries:
            results = await search_fn(query, region, time_range)
            for result in results:
                if result.url not in seen_urls:
                    seen_urls.add(result.url)
                    all_results.append(result)

            # Rate limiting - be nice to DuckDuckGo
            await asyncio.sleep(1)

        return all_results

    def _extract_source(self, url: str) -> str:
        """Extract source name from URL"""
        try:
            from urllib.parse import urlparse
            domain = urlparse(url).netloc
            # Remove www. and common TLDs for cleaner source names
            domain = domain.replace("www.", "")
            parts = domain.split(".")
            if len(parts) >= 2:
                return parts[-2].title()
            return domain
        except:
            return "Unknown"


class EventSearchAgent(SearchAgent):
    """Specialized search agent for events"""

    def __init__(self, max_results: int = 15):
        super().__init__(max_results)
        self.event_platforms = [
            "outsavvy.com",
            "eventbrite.co.uk",
            "moonlightexperiences.com",
            "londonlgbtqcentre.org",
            "designmynight.com",
        ]

    async def search_events(
        self,
        base_query: str,
        cities: List[str] = None,
    ) -> List[SearchResult]:
        """Search for events across platforms"""
        cities = cities or ["London", "Manchester", "Birmingham", "Bristol"]
        queries = []

        # Platform-specific searches
        for platform in self.event_platforms:
            queries.append(f"site:{platform} {base_query}")

        # City-specific searches
        for city in cities:
            queries.append(f"{base_query} {city} events")

        return await self.multi_search(queries, search_type="web", time_range="m")

    async def search_qtipoc_events(self) -> List[SearchResult]:
        """Search specifically for QTIPOC events"""
        queries = [
            "QTIPOC events UK",
            "Black LGBTQ party London",
            "Black queer events Manchester",
            "site:outsavvy.com Black LGBTQ",
            "site:eventbrite.co.uk QTIPOC",
            "BBZ London",
            "Misery QTIPOC",
            "Hungama queer",
            "UK Black Pride events",
            "Black gay party UK",
        ]
        return await self.multi_search(queries, search_type="web", time_range="m")
