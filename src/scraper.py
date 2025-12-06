"""
Web Scraper Agent - Browser automation for event extraction
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, asdict
from datetime import datetime
import hashlib
import re

from playwright.async_api import async_playwright, Browser, Page


@dataclass
class ScrapedEvent:
    name: str
    url: str
    venue: Optional[str] = None
    address: Optional[str] = None
    city: Optional[str] = None
    date: Optional[str] = None
    end_date: Optional[str] = None
    price: Optional[str] = None
    description: Optional[str] = None
    organizer: Optional[str] = None
    event_type: Optional[str] = None
    image_url: Optional[str] = None
    source_platform: Optional[str] = None
    scraped_at: Optional[str] = None
    url_hash: Optional[str] = None

    def __post_init__(self):
        self.scraped_at = datetime.utcnow().isoformat()
        self.url_hash = hashlib.md5(self.url.encode()).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


class ScraperAgent:
    """Browser-based scraper for event platforms"""

    def __init__(self, headless: bool = True, timeout: int = 30000):
        self.headless = headless
        self.timeout = timeout
        self.browser: Optional[Browser] = None

    async def __aenter__(self):
        playwright = await async_playwright().start()
        self.browser = await playwright.chromium.launch(headless=self.headless)
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.browser:
            await self.browser.close()

    async def scrape_page(self, url: str) -> str:
        """Scrape raw HTML from a URL"""
        if not self.browser:
            raise RuntimeError("Scraper not initialized. Use 'async with' context.")

        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")
            content = await page.content()
            return content
        finally:
            await page.close()

    async def scrape_outsavvy(self, search_query: str = "Black LGBTQ") -> List[ScrapedEvent]:
        """Scrape events from OutSavvy"""
        events = []
        url = f"https://www.outsavvy.com/search?q={search_query.replace(' ', '+')}"

        if not self.browser:
            raise RuntimeError("Scraper not initialized")

        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # Wait for events to load
            await page.wait_for_selector(".event-card, .search-result", timeout=10000)

            # Extract event links
            event_links = await page.eval_on_selector_all(
                "a[href*='/event/']",
                "elements => elements.map(e => e.href)"
            )

            # Deduplicate and limit
            unique_links = list(set(event_links))[:20]

            for link in unique_links:
                try:
                    event = await self._scrape_outsavvy_event(page, link)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"Error scraping {link}: {e}")

        except Exception as e:
            print(f"OutSavvy scrape error: {e}")
        finally:
            await page.close()

        return events

    async def _scrape_outsavvy_event(self, page: Page, url: str) -> Optional[ScrapedEvent]:
        """Scrape individual OutSavvy event page"""
        await page.goto(url, timeout=self.timeout, wait_until="networkidle")

        try:
            title = await page.text_content("h1") or ""
            date_elem = await page.text_content(".event-date, .date-time") or ""
            venue = await page.text_content(".venue-name, .location") or ""
            price = await page.text_content(".price, .ticket-price") or ""
            description = await page.text_content(".event-description, .description") or ""

            return ScrapedEvent(
                name=title.strip(),
                url=url,
                venue=venue.strip() if venue else None,
                date=date_elem.strip() if date_elem else None,
                price=price.strip() if price else None,
                description=description.strip()[:500] if description else None,
                source_platform="OutSavvy",
            )
        except:
            return None

    async def scrape_eventbrite(self, search_query: str = "Black-queer") -> List[ScrapedEvent]:
        """Scrape events from Eventbrite UK"""
        events = []
        url = f"https://www.eventbrite.co.uk/d/united-kingdom/{search_query}/"

        if not self.browser:
            raise RuntimeError("Scraper not initialized")

        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # Extract event cards
            event_cards = await page.query_selector_all("[data-testid='event-card'], .search-event-card")

            for card in event_cards[:20]:
                try:
                    title_elem = await card.query_selector("h3, .event-card-title")
                    title = await title_elem.text_content() if title_elem else ""

                    link_elem = await card.query_selector("a")
                    link = await link_elem.get_attribute("href") if link_elem else ""

                    date_elem = await card.query_selector("[data-testid='event-card-date'], .event-card-date")
                    date = await date_elem.text_content() if date_elem else ""

                    venue_elem = await card.query_selector("[data-testid='event-card-location'], .event-card-location")
                    venue = await venue_elem.text_content() if venue_elem else ""

                    if title and link:
                        events.append(ScrapedEvent(
                            name=title.strip(),
                            url=link if link.startswith("http") else f"https://www.eventbrite.co.uk{link}",
                            venue=venue.strip() if venue else None,
                            date=date.strip() if date else None,
                            source_platform="Eventbrite",
                        ))
                except Exception as e:
                    print(f"Error extracting event card: {e}")

        except Exception as e:
            print(f"Eventbrite scrape error: {e}")
        finally:
            await page.close()

        return events

    async def scrape_moonlight(self) -> List[ScrapedEvent]:
        """Scrape events from Moonlight Experiences"""
        events = []
        url = "https://www.moonlightexperiences.com/experiences"

        if not self.browser:
            raise RuntimeError("Scraper not initialized")

        page = await self.browser.new_page()
        try:
            await page.goto(url, timeout=self.timeout, wait_until="networkidle")

            # Extract experience cards
            cards = await page.query_selector_all(".experience-card, .event-item, a[href*='/event']")

            for card in cards[:20]:
                try:
                    title = await card.text_content() or ""
                    link = await card.get_attribute("href") or ""

                    if title and link:
                        full_url = link if link.startswith("http") else f"https://www.moonlightexperiences.com{link}"
                        events.append(ScrapedEvent(
                            name=title.strip()[:200],
                            url=full_url,
                            source_platform="Moonlight Experiences",
                        ))
                except:
                    pass

        except Exception as e:
            print(f"Moonlight scrape error: {e}")
        finally:
            await page.close()

        return events

    async def scrape_all_platforms(self) -> List[ScrapedEvent]:
        """Scrape all configured event platforms"""
        all_events = []

        # OutSavvy searches
        for query in ["Black LGBTQ", "QTIPOC", "queer POC"]:
            events = await self.scrape_outsavvy(query)
            all_events.extend(events)
            await asyncio.sleep(2)  # Rate limiting

        # Eventbrite searches
        for query in ["Black-queer", "QTIPOC", "Black-LGBTQ"]:
            events = await self.scrape_eventbrite(query)
            all_events.extend(events)
            await asyncio.sleep(2)

        # Moonlight
        events = await self.scrape_moonlight()
        all_events.extend(events)

        # Deduplicate by URL hash
        seen = set()
        unique_events = []
        for event in all_events:
            if event.url_hash not in seen:
                seen.add(event.url_hash)
                unique_events.append(event)

        return unique_events
