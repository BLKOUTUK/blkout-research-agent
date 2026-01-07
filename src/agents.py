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
    negative_keywords,
    domain_blacklist,
    domain_whitelist,
    relevance_threshold,
    event_relevance_threshold,
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

    def _is_domain_acceptable(self, url: str) -> bool:
        """Check if domain is acceptable for news/events content"""
        url_lower = url.lower()
        domain = self._extract_domain(url_lower)

        # REJECT blacklisted domains
        for blacklisted in domain_blacklist:
            if blacklisted in domain:
                return False

        # WHITELIST sources (preferred)
        for whitelisted in domain_whitelist:
            whitelisted_clean = whitelisted.replace("*.", "")
            if whitelisted_clean in domain or domain.endswith(whitelisted_clean):
                return True

        # Accept other sources IF they pass keyword checks (less preferred)
        # This allows legitimate news sources not in whitelist
        return True

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").lower()
            return domain
        except:
            return ""

    def _quick_relevance_check(self, text: str, url: str = "") -> int:
        """Fast keyword-based relevance check before LLM analysis

        Returns:
            -1: Rejected (domain blacklist, negative keywords)
            0-45: Too low relevance
            46-74: Borderline (needs LLM review)
            75+: High confidence match
        """
        text_lower = text.lower()

        # FIRST: Domain-based rejection
        if url and not self._is_domain_acceptable(url):
            return -1  # Signal rejection

        # SECOND: Negative keywords (should exclude)
        for neg_term in negative_keywords:
            if neg_term in text_lower:
                # Unless overridden by high-relevance keywords
                has_high_relevance = any(
                    term in text_lower for term in high_relevance_keywords
                )
                if not has_high_relevance:
                    return 15  # Very low, likely false positive

        # Check for high-relevance intersectional terms (strongest signal)
        for term in high_relevance_keywords:
            if term in text_lower:
                return 95  # Definitely relevant

        # Check for Black + LGBTQ+ combination (must have BOTH + UK)
        has_black = any(kw in text_lower for kw in black_keywords)
        has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
        has_uk = any(kw in text_lower for kw in uk_keywords)

        # Require UK location for news (high confidence)
        if has_black and has_lgbtq and has_uk:
            return 85  # Strong match

        # Single keywords alone are insufficient (changed from 75/40)
        if has_black and has_lgbtq:
            # Without UK, needs deeper analysis
            return 60  # Borderline (was 75 - too lenient)
        elif (has_black or has_lgbtq) and has_uk:
            # One keyword + UK location
            return 50  # Borderline (was 40)
        elif has_black or has_lgbtq:
            # Single keyword only
            return 25  # Low (was 40 - too lenient)

        return 10  # No relevant keywords

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

        # Phase 2: Quick filter with domain and keyword validation
        candidates = []
        rejected = []
        for result in all_results:
            combined_text = f"{result.title} {result.snippet}"
            quick_score = self._quick_relevance_check(combined_text, url=result.url)

            if quick_score == -1:
                # Domain rejection
                rejected.append((result, "domain_blacklist"))
            elif quick_score >= 45:  # Significantly stricter than before (was 40)
                # Worth deeper analysis
                candidates.append((result, quick_score))
            else:
                rejected.append((result, f"low_score_{quick_score}"))

        print(f"[NewsAgent] {len(candidates)} candidates passed quick filter")
        print(f"[NewsAgent] {len(rejected)} results rejected (domain/keywords)")

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

    def _is_domain_acceptable(self, url: str) -> bool:
        """Check if domain is acceptable for events content"""
        url_lower = url.lower()
        domain = self._extract_domain(url_lower)

        # REJECT blacklisted domains (no Wikipedia, gaming, etc)
        for blacklisted in domain_blacklist:
            if blacklisted in domain:
                return False

        # WHITELIST event platforms (strongly preferred)
        event_whitelist = ["outsavvy", "eventbrite", "moonlight", "londonlgbtq",
                          "designmynight", "eventim", "ticketmaster"]
        for whitelisted in event_whitelist:
            if whitelisted in domain:
                return True

        # Accept social platforms (Instagram, Facebook for announcements)
        social = ["instagram", "facebook", "twitter", "x.com"]
        for soc in social:
            if soc in domain:
                return True

        return True  # Other sources OK if they pass keyword checks

    def _extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            domain = parsed.netloc.replace("www.", "").lower()
            return domain
        except:
            return ""

    def _is_likely_event(self, text: str) -> bool:
        """Check if content appears to be an actual event"""
        text_lower = text.lower()

        # Negative indicators (NOT an event)
        non_event_terms = [
            "musician", "band", "game", "character",
            "tv show", "movie", "film", "wikipedia",
            "tutorial", "guide", "tips", "tricks",
        ]
        for term in non_event_terms:
            if term in text_lower:
                # Unless it has clear event indicators
                event_terms = ["event", "party", "night", "club", "gather",
                              "show", "performance", "live", "date:"]
                if not any(et in text_lower for et in event_terms):
                    return False

        # Positive indicators (IS an event)
        event_terms = [
            "event", "party", "night", "club", "gathering", "gathering",
            "show", "performance", "live", "happening", "gig",
            "club night", "celebration", "festival", "pride",
        ]
        return any(term in text_lower for term in event_terms)

    async def discover_from_search(self) -> List[DiscoveredEvent]:
        """Discover events via web search"""
        print("[EventsAgent] Searching for QTIPOC events...")

        results = await self.search.search_qtipoc_events()
        print(f"[EventsAgent] Found {len(results)} search results")

        events = []
        rejected = []

        for result in results:
            combined_text = f"{result.title} {result.snippet}"

            # Filter 1: Domain validation
            if not self._is_domain_acceptable(result.url):
                rejected.append((result, "domain_blacklist"))
                continue

            # Filter 2: Check if it's actually an event (not a band/musician/game)
            if not self._is_likely_event(combined_text):
                rejected.append((result, "not_event"))
                continue

            # Filter 3: Must contain relevant keywords
            text_lower = combined_text.lower()
            has_black = any(kw in text_lower for kw in black_keywords)
            has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
            has_uk = any(kw in text_lower for kw in uk_keywords)

            # Events need stronger relevance (both Black AND LGBTQ+)
            if not (has_black and has_lgbtq):
                rejected.append((result, "weak_keywords"))
                continue

            # Extract date from title, snippet, or URL using LLM
            extracted_date = await self._extract_date_from_text(
                f"Title: {result.title}\nURL: {result.url}\nSnippet: {result.snippet}"
            )

            # Determine relevance score based on filters passed
            if any(kw in text_lower for kw in high_relevance_keywords):
                relevance = 95
            elif has_black and has_lgbtq and has_uk:
                relevance = 85
            else:
                relevance = 75

            # Extract basic event info
            events.append(DiscoveredEvent(
                name=result.title,
                url=result.url,
                description=result.snippet,
                date=extracted_date,
                source_platform="Web Search",
                relevance_score=relevance,
            ))

        print(f"[EventsAgent] {len(events)} events passed filters")
        print(f"[EventsAgent] {len(rejected)} results rejected")
        return events

    async def _extract_date_from_text(self, text: str) -> Optional[str]:
        """Extract event date from text using LLM"""
        try:
            prompt = f"""Extract the event date from this text. Return ONLY the date in ISO format (YYYY-MM-DD) or "none" if no date found.

Text: {text[:500]}

Rules:
- Look for dates in title, URL path, or snippet
- Common patterns: "Jan 7", "7th January 2026", "/2026/01/07/", "Tue, 7 Jan"
- If multiple dates, return the earliest future date
- If no clear date, return "none"

Date (YYYY-MM-DD or "none"):"""

            response = await self.llm.complete(prompt, max_tokens=20)
            date_str = response.strip().lower()

            if date_str == "none" or not date_str:
                return None

            # Validate it looks like a date (YYYY-MM-DD format)
            if len(date_str) == 10 and date_str[4] == '-' and date_str[7] == '-':
                return date_str

            return None
        except Exception as e:
            return None

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
