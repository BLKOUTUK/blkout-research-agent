"""
Database Client - Supabase integration for storing discovered content
"""

import os
import hashlib
from typing import List, Dict, Any, Optional
from datetime import datetime
from supabase import create_client, Client


class DatabaseClient:
    """Supabase client for BLKOUT content storage"""

    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL", ""),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY", "")
        )

    def _generate_hash(self, url: str) -> str:
        """Generate URL hash for deduplication"""
        return hashlib.md5(url.lower().strip().encode()).hexdigest()

    # =========================================================================
    # NEWS ARTICLES
    # =========================================================================

    async def article_exists(self, url: str) -> bool:
        """Check if article already exists"""
        url_hash = self._generate_hash(url)
        result = self.client.table("news_articles").select("id").eq("url_hash", url_hash).execute()
        return len(result.data) > 0

    async def insert_article(self, article: Dict[str, Any]) -> Optional[str]:
        """Insert a new article"""
        url_hash = self._generate_hash(article.get("source_url", ""))

        # Check for duplicate
        if await self.article_exists(article.get("source_url", "")):
            return None

        data = {
            "title": article.get("title", "")[:500],
            "excerpt": article.get("excerpt", "")[:1000],
            "content": article.get("content", ""),
            "source_url": article.get("source_url", ""),
            "source_name": article.get("source_name", ""),
            "author": article.get("author", ""),
            "published_at": article.get("published_date") or datetime.utcnow().isoformat(),
            "featured_image": article.get("image_url"),
            "category": article.get("category", "news"),
            "interest_score": min(100, article.get("relevance_score", 50)),
            "url_hash": url_hash,
            "status": "review",  # Requires human review before publishing
            "published": False,
            "moderation_status": "pending",
            "topics": article.get("tags", []),
            "discovery_method": "research_agent",
        }

        result = self.client.table("news_articles").insert(data).execute()
        return result.data[0]["id"] if result.data else None

    async def insert_articles_batch(self, articles: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert multiple articles, skipping duplicates"""
        inserted = 0
        skipped = 0

        for article in articles:
            result = await self.insert_article(article)
            if result:
                inserted += 1
            else:
                skipped += 1

        return {"inserted": inserted, "skipped": skipped}

    # =========================================================================
    # EVENTS
    # =========================================================================

    async def event_exists(self, url: str) -> bool:
        """Check if event already exists"""
        url_hash = self._generate_hash(url)
        result = self.client.table("events").select("id").eq("url_hash", url_hash).execute()
        return len(result.data) > 0

    async def insert_event(self, event: Dict[str, Any]) -> Optional[str]:
        """Insert a new event"""

        # CRITICAL: Skip events without valid date (database constraint)
        event_date = event.get("date") or event.get("start_date")
        if not event_date:
            print(f"[DB] Skipping event without date: {event.get('name', 'Unknown')[:50]}")
            return None

        url_hash = self._generate_hash(event.get("url", ""))

        # Check for duplicate
        if await self.event_exists(event.get("url", "")):
            return None

        # Map to actual events table schema
        # Actual columns: id, title, date, description, location, virtual_link, organizer,
        #                 source, tags, url, cost, start_time, end_time, end_date, status
        # Combine address info into location field
        location_parts = []
        if event.get("venue"):
            location_parts.append(event.get("venue"))
        if event.get("address"):
            location_parts.append(event.get("address"))
        if event.get("city"):
            location_parts.append(event.get("city"))

        location = ", ".join(location_parts) if location_parts else "Location TBA"

        data = {
            "title": event.get("name", "")[:500],
            "description": event.get("description", ""),
            "url": event.get("url", ""),
            "location": location,  # Combined address/venue/city
            "date": event_date,  # Required field - validated above
            "start_time": event.get("start_time"),
            "end_time": event.get("end_time"),
            "end_date": event.get("end_date"),
            "cost": event.get("price"),
            "organizer": event.get("organizer"),
            "source": event.get("source_platform", "research_agent"),
            "tags": event.get("tags", []),
            "status": "draft",  # Goes to moderation queue
            # Note: url_hash, image_url, relevance_score, discovery_method columns don't exist
            # These features need to be added via database migration if needed
        }

        result = self.client.table("events").insert(data).execute()
        return result.data[0]["id"] if result.data else None

    async def insert_events_batch(self, events: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert multiple events, skipping duplicates"""
        inserted = 0
        skipped = 0

        for event in events:
            result = await self.insert_event(event)
            if result:
                inserted += 1
            else:
                skipped += 1

        return {"inserted": inserted, "skipped": skipped}

    # =========================================================================
    # DISCOVERY LOGS
    # =========================================================================

    async def log_discovery_run(
        self,
        run_type: str,
        stats: Dict[str, Any],
        errors: List[str] = None,
    ) -> str:
        """Log a discovery run for monitoring"""
        data = {
            "run_type": run_type,  # "news" | "events" | "deep_research"
            "started_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "errors": errors or [],
            "status": "completed" if not errors else "completed_with_errors",
        }

        result = self.client.table("discovery_logs").insert(data).execute()
        return result.data[0]["id"] if result.data else None


# Singleton
_db: Optional[DatabaseClient] = None


def get_database() -> DatabaseClient:
    global _db
    if _db is None:
        _db = DatabaseClient()
    return _db
