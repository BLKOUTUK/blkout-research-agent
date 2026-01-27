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


def parse_date_to_iso(date_str: str) -> Optional[str]:
    """Parse various date formats to ISO format YYYY-MM-DD"""
    if not date_str:
        return None

    date_str = date_str.strip()

    # Already ISO format
    if re.match(r'^\d{4}-\d{2}-\d{2}', date_str):
        return date_str.split('T')[0]

    # Month name mappings
    months = {
        'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
        'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
        'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
        'aug': '08', 'august': '08', 'sep': '09', 'september': '09',
        'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
        'dec': '12', 'december': '12'
    }

    # Try "25 January 2026" or "25 Jan 2026"
    match = re.search(r'(\d{1,2})\s+([A-Za-z]+)\s+(202\d)', date_str)
    if match:
        day = match.group(1).zfill(2)
        month_name = match.group(2).lower()
        year = match.group(3)
        month = months.get(month_name[:3])
        if month:
            return f"{year}-{month}-{day}"

    # Try "January 25, 2026" or "Jan 25 2026"
    match = re.search(r'([A-Za-z]+)\s+(\d{1,2}),?\s+(202\d)', date_str)
    if match:
        month_name = match.group(1).lower()
        day = match.group(2).zfill(2)
        year = match.group(3)
        month = months.get(month_name[:3])
        if month:
            return f"{year}-{month}-{day}"

    # Try "Sat 25 Jan 2026" or "Saturday 25 January 2026"
    match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*\s+(\d{1,2})\s+([A-Za-z]+)\s*(202\d)?', date_str, re.IGNORECASE)
    if match:
        day = match.group(1).zfill(2)
        month_name = match.group(2).lower()
        year = match.group(3) or '2026'  # Default to 2026 if not specified
        month = months.get(month_name[:3])
        if month:
            return f"{year}-{month}-{day}"

    # Try "Sat, Jan 25" (no year - assume 2026)
    match = re.search(r'(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+([A-Za-z]+)\s+(\d{1,2})', date_str, re.IGNORECASE)
    if match:
        month_name = match.group(1).lower()
        day = match.group(2).zfill(2)
        month = months.get(month_name[:3])
        if month:
            return f"2026-{month}-{day}"

    return None


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
            await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")

            # Wait for page to fully load and JS to render
            await asyncio.sleep(3)

            # Wait for events to load - use actual OutSavvy selectors with fallbacks
            try:
                await page.wait_for_selector("article, a[href*='/event/']", timeout=30000)
            except Exception as e:
                print(f"OutSavvy: No events loaded after 30s: {e}")
                return events

            # Extract event links using actual selector that works
            event_links = await page.eval_on_selector_all(
                "a[href*='/event/']",
                "elements => elements.map(e => e.href)"
            )

            # Deduplicate and limit
            unique_links = list(set(event_links))[:20]
            print(f"OutSavvy: Found {len(unique_links)} unique event links")

            for link in unique_links:
                try:
                    event = await self._scrape_outsavvy_event(page, link)
                    if event:
                        events.append(event)
                except Exception as e:
                    print(f"Error scraping {link}: {e}")
                    continue  # Skip failed events, don't crash entire scrape

        except Exception as e:
            print(f"OutSavvy scrape error: {e}")
            # Don't raise - return partial results
        finally:
            await page.close()

        return events

    async def _scrape_outsavvy_event(self, page: Page, url: str) -> Optional[ScrapedEvent]:
        """Scrape individual OutSavvy event page"""
        # Helper to check if text is a placeholder/invalid
        def is_placeholder(text: str) -> bool:
            if not text or len(text.strip()) < 5:
                return True
            invalid_phrases = ['select', 'choose', 'pick', 'filter', 'event time', 'tba', 'tbd']
            return any(phrase in text.lower() for phrase in invalid_phrases)

        try:
            await page.goto(url, timeout=self.timeout, wait_until="domcontentloaded")
            await asyncio.sleep(2)  # Allow JS to render

            # Title - OutSavvy uses h1 tags
            title = ""
            if await page.locator("h1").count() > 0:
                title = await page.locator("h1").first.text_content() or ""

            # Date/Time - Multiple extraction strategies (prioritize regex as most reliable)
            date_elem = ""

            # Strategy 1: Extract date from page body using regex patterns (most reliable)
            try:
                body_text = await page.evaluate('() => document.body.innerText')
                # Look for various date patterns including OutSavvy's "THURSDAY 12TH MARCH 2026" format
                date_patterns = [
                    # OutSavvy format: "THURSDAY 12TH MARCH 2026 AT 7:30 PM"
                    r'\b(?:Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})(?:st|nd|rd|th)?\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(202[4-9])\b',
                    # Standard: "25 January 2026"
                    r'\b(\d{1,2})\s+(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(202[4-9])\b',
                    # Short day: "Sat 25 Jan 2026" or "Sat, 25 Jan 2026"
                    r'\b(?:Mon|Tue|Wed|Thu|Fri|Sat|Sun)[a-z]*,?\s+(\d{1,2})\s+(Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+(202[4-9])\b',
                    # US format: "January 25, 2026"
                    r'\b(Jan(?:uary)?|Feb(?:ruary)?|Mar(?:ch)?|Apr(?:il)?|May|Jun(?:e)?|Jul(?:y)?|Aug(?:ust)?|Sep(?:tember)?|Oct(?:ober)?|Nov(?:ember)?|Dec(?:ember)?)\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(202[4-9])\b',
                    # ISO format: "2026-01-25"
                    r'\b(202[4-9])-(\d{2})-(\d{2})\b'
                ]

                months = {
                    'jan': '01', 'january': '01', 'feb': '02', 'february': '02',
                    'mar': '03', 'march': '03', 'apr': '04', 'april': '04',
                    'may': '05', 'jun': '06', 'june': '06', 'jul': '07', 'july': '07',
                    'aug': '08', 'august': '08', 'sep': '09', 'september': '09',
                    'oct': '10', 'october': '10', 'nov': '11', 'november': '11',
                    'dec': '12', 'december': '12'
                }

                for i, pattern in enumerate(date_patterns):
                    match = re.search(pattern, body_text, re.IGNORECASE)
                    if match:
                        groups = match.groups()
                        if i == 0 or i == 1:  # "THURSDAY 12TH MARCH 2026" or "25 January 2026"
                            day = groups[0].zfill(2)
                            month = months.get(groups[1].lower()[:3], '01')
                            year = groups[2]
                            date_elem = f"{year}-{month}-{day}"
                        elif i == 2:  # "Sat 25 Jan 2026"
                            day = groups[0].zfill(2)
                            month = months.get(groups[1].lower()[:3], '01')
                            year = groups[2]
                            date_elem = f"{year}-{month}-{day}"
                        elif i == 3:  # "January 25, 2026"
                            month = months.get(groups[0].lower()[:3], '01')
                            day = groups[1].zfill(2)
                            year = groups[2]
                            date_elem = f"{year}-{month}-{day}"
                        elif i == 4:  # "2026-01-25"
                            date_elem = f"{groups[0]}-{groups[1]}-{groups[2]}"
                        break
            except:
                pass

            # Strategy 2: Try to get date from JSON-LD structured data
            if not date_elem:
                try:
                    json_ld = await page.evaluate('''() => {
                        const scripts = document.querySelectorAll('script[type="application/ld+json"]');
                        for (const script of scripts) {
                            try {
                                const data = JSON.parse(script.textContent);
                                if (data.startDate) return data.startDate;
                                if (data['@graph']) {
                                    for (const item of data['@graph']) {
                                        if (item.startDate) return item.startDate;
                                    }
                                }
                            } catch (e) {}
                        }
                        return null;
                    }''')
                    if json_ld and not is_placeholder(json_ld):
                        date_elem = json_ld
                except:
                    pass

            # Strategy 3: Try meta tags
            if not date_elem:
                try:
                    meta_date = await page.evaluate('''() => {
                        const meta = document.querySelector('meta[property="event:start_time"], meta[name="date"], meta[property="og:event:start_time"]');
                        return meta ? meta.getAttribute('content') : null;
                    }''')
                    if meta_date and not is_placeholder(meta_date):
                        date_elem = meta_date
                except:
                    pass

            # Strategy 4: Look for visible date elements (excluding form inputs)
            if not date_elem:
                # Use more specific selectors and filter out form placeholders
                date_selectors = [
                    "[class*='EventDate']", "[class*='event-date']",
                    "[class*='startDate']", "[class*='start-date']",
                    "[data-testid*='date']", "time[datetime]",
                    ".date-display", ".event-info time"
                ]
                for selector in date_selectors:
                    if await page.locator(selector).count() > 0:
                        text = await page.locator(selector).first.text_content() or ""
                        # Filter out form placeholders
                        if text.strip() and not is_placeholder(text):
                            date_elem = text.strip()
                            break

            # Venue - OutSavvy uses classes with "Venue" or "Location"
            venue = ""
            venue_selectors = ["[class*='Venue']", "[class*='Location']", ".where", ".venue"]
            for selector in venue_selectors:
                if await page.locator(selector).count() > 0:
                    venue = await page.locator(selector).first.text_content() or ""
                    if venue.strip():
                        break

            # Price - OutSavvy uses classes with "price"
            price = ""
            price_selectors = ["[class*='price']", ".price", ".ticket-price"]
            for selector in price_selectors:
                if await page.locator(selector).count() > 0:
                    price = await page.locator(selector).first.text_content() or ""
                    if price.strip():
                        break

            # Description - OutSavvy uses .event-description or classes with "Description"
            description = ""
            desc_selectors = [".event-description", "[class*='Description']", "[class*='about']", ".description"]
            for selector in desc_selectors:
                if await page.locator(selector).count() > 0:
                    description = await page.locator(selector).first.text_content() or ""
                    if description.strip() and len(description.strip()) > 20:
                        break

            if not title:
                return None

            # Parse the date to ISO format
            parsed_date = parse_date_to_iso(date_elem) if date_elem else None
            if date_elem and not parsed_date:
                print(f"Could not parse date '{date_elem}' for event: {title[:50]}")

            return ScrapedEvent(
                name=title.strip(),
                url=url,
                venue=venue.strip() if venue else None,
                date=parsed_date,  # Use parsed ISO date
                price=price.strip() if price else None,
                description=description.strip()[:500] if description else None,
                source_platform="OutSavvy",
            )
        except Exception as e:
            print(f"Error scraping event page {url}: {e}")
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
                        # Parse the date to ISO format
                        parsed_date = parse_date_to_iso(date) if date else None
                        events.append(ScrapedEvent(
                            name=title.strip(),
                            url=link if link.startswith("http") else f"https://www.eventbrite.co.uk{link}",
                            venue=venue.strip() if venue else None,
                            date=parsed_date,  # Use parsed ISO date
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
        """Scrape all configured event platforms with error isolation"""
        all_events = []

        # OutSavvy searches - isolated error handling
        print("\n=== Scraping OutSavvy ===")
        for query in ["Black LGBTQ", "QTIPOC", "queer POC"]:
            try:
                events = await self.scrape_outsavvy(query)
                all_events.extend(events)
                print(f"OutSavvy '{query}': {len(events)} events found")
            except Exception as e:
                print(f"OutSavvy '{query}' failed: {e}")
                # Continue to next platform - don't crash entire discovery
            await asyncio.sleep(2)  # Rate limiting

        # Eventbrite searches - isolated error handling
        print("\n=== Scraping Eventbrite ===")
        for query in ["Black-queer", "QTIPOC", "Black-LGBTQ"]:
            try:
                events = await self.scrape_eventbrite(query)
                all_events.extend(events)
                print(f"Eventbrite '{query}': {len(events)} events found")
            except Exception as e:
                print(f"Eventbrite '{query}' failed: {e}")
                # Continue to next platform
            await asyncio.sleep(2)

        # Moonlight - isolated error handling
        print("\n=== Scraping Moonlight ===")
        try:
            events = await self.scrape_moonlight()
            all_events.extend(events)
            print(f"Moonlight: {len(events)} events found")
        except Exception as e:
            print(f"Moonlight failed: {e}")
            # Continue anyway

        # Deduplicate by URL hash
        seen = set()
        unique_events = []
        for event in all_events:
            if event.url_hash not in seen:
                seen.add(event.url_hash)
                unique_events.append(event)

        print(f"\n=== Total unique events: {len(unique_events)} ===")
        return unique_events
