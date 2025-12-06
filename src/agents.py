"""
Research Agents - Coordinated agents for news and events discovery
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from .llm import get_llm_client, LLMClient
from .search import SearchAgent, EventSearchAgent, SearchResult
from .scraper import ScraperAgent, ScrapedEvent
from .database import get_database, DatabaseClient
from .ivor_sync import IVORSync

import sys
sys.path.append("..")
from configs.blkout_config import (
    news_search_queries,
    events_search_queries,
    high_relevance_keywords,
    black_keywords,
    lgbtq_keywords,
    uk_keywords,
    relevance_threshold,
)


@dataclass
class DiscoveredArticle:
    title: str
    url: str
    source: str
    snippet: str
    published_date: Optional[str] = None
    relevance_score: int = 0
    category: str = "news"
    tags: List[str] = None
    reasoning: str = ""


@dataclass
class DiscoveredEvent:
    name: str
    url: str
    venue: Optional[str] = None
    city: Optional[str] = None
    date: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    source_platform: Optional[str] = None
    relevance_score: int = 0
    event_type: str = "community"
    tags: List[str] = None


class NewsResearchAgent:
    """Agent for discovering news relevant to Black LGBTQ+ UK community"""

    def __init__(self):
        self.llm = get_llm_client()
        self.search = SearchAgent(max_results=10)
        self.db = get_database()

    def _quick_relevance_check(self, text: str) -> int:
        """Fast keyword-based relevance check before LLM analysis"""
        text_lower = text.lower()

        # Check for high-relevance intersectional terms
        for term in high_relevance_keywords:
            if term in text_lower:
                return 95

        # Check for Black + LGBTQ+ combination
        has_black = any(kw in text_lower for kw in black_keywords)
        has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
        has_uk = any(kw in text_lower for kw in uk_keywords)

        if has_black and has_lgbtq:
            return 85 if has_uk else 75
        elif has_black or has_lgbtq:
            return 40  # Needs further analysis
        return 20

    async def research(self, time_range: str = "w") -> List[DiscoveredArticle]:
        """Execute news research across all configured queries"""
        print(f"[NewsAgent] Starting research with {len(news_search_queries)} queries...")

        # Phase 1: Search
        all_results = await self.search.multi_search(
            news_search_queries,
            search_type="news",
            time_range=time_range,
        )
        print(f"[NewsAgent] Found {len(all_results)} raw results")

        # Phase 2: Quick filter
        candidates = []
        for result in all_results:
            combined_text = f"{result.title} {result.snippet}"
            quick_score = self._quick_relevance_check(combined_text)
            if quick_score >= 40:  # Worth deeper analysis
                candidates.append((result, quick_score))

        print(f"[NewsAgent] {len(candidates)} candidates passed quick filter")

        # Phase 3: LLM relevance analysis for borderline cases
        discovered = []
        for result, quick_score in candidates:
            if quick_score >= 80:
                # High confidence, skip LLM
                discovered.append(DiscoveredArticle(
                    title=result.title,
                    url=result.url,
                    source=result.source,
                    snippet=result.snippet,
                    published_date=result.published_date,
                    relevance_score=quick_score,
                    reasoning="High-confidence keyword match",
                ))
            else:
                # Use LLM for deeper analysis
                try:
                    analysis = await self.llm.analyze_relevance(
                        title=result.title,
                        content=result.snippet,
                        source=result.source,
                        url=result.url,
                    )
                    score = analysis.get("relevance_score", 0)
                    if score >= relevance_threshold:
                        discovered.append(DiscoveredArticle(
                            title=result.title,
                            url=result.url,
                            source=result.source,
                            snippet=result.snippet,
                            published_date=result.published_date,
                            relevance_score=score,
                            category=analysis.get("suggested_category", "news"),
                            tags=analysis.get("suggested_tags", []),
                            reasoning=analysis.get("reasoning", ""),
                        ))
                except Exception as e:
                    print(f"[NewsAgent] LLM analysis error: {e}")
                    # Fall back to quick score if high enough
                    if quick_score >= relevance_threshold:
                        discovered.append(DiscoveredArticle(
                            title=result.title,
                            url=result.url,
                            source=result.source,
                            snippet=result.snippet,
                            relevance_score=quick_score,
                        ))

        # Sort by relevance
        discovered.sort(key=lambda x: x.relevance_score, reverse=True)
        print(f"[NewsAgent] Discovered {len(discovered)} relevant articles")

        return discovered

    async def research_and_save(self, time_range: str = "w") -> Dict[str, Any]:
        """Research and save to database"""
        articles = await self.research(time_range)

        # Convert to dict format for database
        article_dicts = [
            {
                "title": a.title,
                "source_url": a.url,
                "source_name": a.source,
                "excerpt": a.snippet,
                "published_date": a.published_date,
                "relevance_score": a.relevance_score,
                "category": a.category,
                "tags": a.tags or [],
            }
            for a in articles
        ]

        stats = await self.db.insert_articles_batch(article_dicts)
        await self.db.log_discovery_run("news", {
            "total_found": len(articles),
            **stats,
        })

        return {
            "discovered": len(articles),
            **stats,
        }


class EventsDiscoveryAgent:
    """Agent for discovering events relevant to Black LGBTQ+ UK community"""

    def __init__(self):
        self.llm = get_llm_client()
        self.search = EventSearchAgent(max_results=15)
        self.db = get_database()

    async def discover_from_search(self) -> List[DiscoveredEvent]:
        """Discover events via web search"""
        print("[EventsAgent] Searching for QTIPOC events...")

        results = await self.search.search_qtipoc_events()
        print(f"[EventsAgent] Found {len(results)} search results")

        events = []
        for result in results:
            # Extract basic event info
            events.append(DiscoveredEvent(
                name=result.title,
                url=result.url,
                description=result.snippet,
                source_platform="Web Search",
                relevance_score=80,  # Search results are pre-filtered by query
            ))

        return events

    async def discover_from_scraping(self) -> List[DiscoveredEvent]:
        """Discover events by scraping platforms"""
        print("[EventsAgent] Scraping event platforms...")

        events = []
        async with ScraperAgent(headless=True) as scraper:
            scraped = await scraper.scrape_all_platforms()
            print(f"[EventsAgent] Scraped {len(scraped)} events")

            for item in scraped:
                events.append(DiscoveredEvent(
                    name=item.name,
                    url=item.url,
                    venue=item.venue,
                    date=item.date,
                    price=item.price,
                    description=item.description,
                    source_platform=item.source_platform,
                    relevance_score=75,  # Platform search pre-filtered
                ))

        return events

    async def discover_all(self) -> List[DiscoveredEvent]:
        """Discover events from all sources"""
        # Run search and scraping in parallel
        search_task = self.discover_from_search()
        scrape_task = self.discover_from_scraping()

        search_results, scrape_results = await asyncio.gather(
            search_task, scrape_task, return_exceptions=True
        )

        all_events = []

        if isinstance(search_results, list):
            all_events.extend(search_results)
        else:
            print(f"[EventsAgent] Search error: {search_results}")

        if isinstance(scrape_results, list):
            all_events.extend(scrape_results)
        else:
            print(f"[EventsAgent] Scrape error: {scrape_results}")

        # Deduplicate by URL
        seen_urls = set()
        unique_events = []
        for event in all_events:
            if event.url not in seen_urls:
                seen_urls.add(event.url)
                unique_events.append(event)

        print(f"[EventsAgent] Total unique events: {len(unique_events)}")
        return unique_events

    async def discover_and_save(self) -> Dict[str, Any]:
        """Discover and save events to database"""
        events = await self.discover_all()

        # Convert to dict format
        event_dicts = [
            {
                "name": e.name,
                "url": e.url,
                "venue": e.venue,
                "city": e.city,
                "date": e.date,
                "price": e.price,
                "description": e.description,
                "source_platform": e.source_platform,
                "relevance_score": e.relevance_score,
                "event_type": e.event_type,
                "tags": e.tags or [],
            }
            for e in events
        ]

        stats = await self.db.insert_events_batch(event_dicts)
        await self.db.log_discovery_run("events", {
            "total_found": len(events),
            **stats,
        })

        return {
            "discovered": len(events),
            **stats,
        }


class PlanningAgent:
    """Top-level agent that coordinates news and events discovery"""

    def __init__(self):
        self.news_agent = NewsResearchAgent()
        self.events_agent = EventsDiscoveryAgent()
        self.db = get_database()
        self.ivor_sync = IVORSync()

    async def run_daily_discovery(self) -> Dict[str, Any]:
        """Run daily news and events discovery"""
        print("[PlanningAgent] Starting daily discovery...")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "news": {},
            "events": {},
            "ivor_sync": {},
            "errors": [],
        }

        # Run news research
        try:
            results["news"] = await self.news_agent.research_and_save(time_range="d")
        except Exception as e:
            results["errors"].append(f"News research failed: {str(e)}")
            print(f"[PlanningAgent] News error: {e}")

        # Run events discovery
        try:
            results["events"] = await self.events_agent.discover_and_save()
        except Exception as e:
            results["errors"].append(f"Events discovery failed: {str(e)}")
            print(f"[PlanningAgent] Events error: {e}")

        # Sync to IVOR intelligence - keeps IVOR informed of discoveries
        try:
            print("[PlanningAgent] Syncing discoveries to IVOR...")
            results["ivor_sync"] = await self.ivor_sync.sync_daily_discoveries(results)
            print(f"[PlanningAgent] IVOR sync complete: {results['ivor_sync']}")
        except Exception as e:
            results["errors"].append(f"IVOR sync failed: {str(e)}")
            print(f"[PlanningAgent] IVOR sync error: {e}")

        print(f"[PlanningAgent] Daily discovery complete: {results}")
        return results

    async def run_weekly_deep_research(self) -> Dict[str, Any]:
        """Run deeper weekly research with broader time range"""
        print("[PlanningAgent] Starting weekly deep research...")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "news": {},
            "ivor_sync": {},
            "errors": [],
        }

        try:
            results["news"] = await self.news_agent.research_and_save(time_range="m")
        except Exception as e:
            results["errors"].append(f"Deep research failed: {str(e)}")

        # Sync to IVOR after deep research too
        try:
            results["ivor_sync"] = await self.ivor_sync.sync_daily_discoveries(results)
        except Exception as e:
            results["errors"].append(f"IVOR sync failed: {str(e)}")

        return results
