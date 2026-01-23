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
            "category": article.get("category", "community"),
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

        # Validate date format - reject placeholder text
        event_date_str = str(event_date).strip()
        if not event_date_str or len(event_date_str) < 10:
            print(f"[DB] Skipping event with invalid date '{event_date_str}': {event.get('name', 'Unknown')[:50]}")
            return None

        # Reject placeholder/invalid date strings
        invalid_dates = ["select", "tba", "tbd", "coming soon", "date not set"]
        if any(invalid in event_date_str.lower() for invalid in invalid_dates):
            print(f"[DB] Skipping event with placeholder date '{event_date_str}': {event.get('name', 'Unknown')[:50]}")
            return None

        # Validate ISO-like format (YYYY-MM-DD)
        try:
            from datetime import datetime
            # Try parsing as ISO date
            datetime.fromisoformat(event_date_str.split('T')[0])
        except (ValueError, AttributeError):
            print(f"[DB] Skipping event with unparseable date '{event_date_str}': {event.get('name', 'Unknown')[:50]}")
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
            "status": "pending",  # Goes to moderation queue (draft not allowed by constraint)
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
            "run_type": run_type,  # "news" | "events" | "deep_research" | "creators"
            "started_at": datetime.utcnow().isoformat(),
            "stats": stats,
            "errors": errors or [],
            "status": "completed" if not errors else "completed_with_errors",
        }

        result = self.client.table("discovery_logs").insert(data).execute()
        return result.data[0]["id"] if result.data else None

    # =========================================================================
    # CREATORS (The Channel integration)
    # =========================================================================

    async def creator_exists(
        self,
        youtube_handle: Optional[str] = None,
        instagram_handle: Optional[str] = None,
        tiktok_handle: Optional[str] = None,
        twitter_handle: Optional[str] = None
    ) -> bool:
        """Check if creator already exists by handles"""
        try:
            # Build OR query for any matching handle
            query = self.client.table("channel_creators").select("id")

            if youtube_handle:
                query = query.or_(f"youtube_handle.eq.{youtube_handle}")
            if instagram_handle:
                query = query.or_(f"instagram_handle.eq.{instagram_handle}")
            if tiktok_handle:
                query = query.or_(f"tiktok_handle.eq.{tiktok_handle}")
            if twitter_handle:
                query = query.or_(f"twitter_handle.eq.{twitter_handle}")

            result = query.limit(1).execute()
            return len(result.data) > 0

        except Exception as e:
            print(f"[DB] Creator existence check failed: {e}")
            return False

    async def insert_creator(self, creator: Dict[str, Any]) -> Optional[str]:
        """Insert a new creator"""

        # Check for duplicate
        exists = await self.creator_exists(
            youtube_handle=creator.get("youtube_handle"),
            instagram_handle=creator.get("instagram_handle"),
            tiktok_handle=creator.get("tiktok_handle"),
            twitter_handle=creator.get("twitter_handle")
        )

        if exists:
            return None

        data = {
            "creator_name": creator.get("creator_name", "")[:255],
            "location": creator.get("location") or "London",  # Ensure never null
            "primary_platform": creator.get("primary_platform", "instagram"),
            "youtube_handle": creator.get("youtube_handle"),
            "instagram_handle": creator.get("instagram_handle"),
            "tiktok_handle": creator.get("tiktok_handle"),
            "twitter_handle": creator.get("twitter_handle"),
            "website_url": creator.get("website_url"),
            "bio": creator.get("bio", "")[:1000],
            "content_themes": creator.get("content_themes", []),
            "pronouns": creator.get("pronouns"),
            "consent_status": "pending",  # Always starts as pending
            "discovery_notes": creator.get("discovery_notes", ""),
            "discovered_by": creator.get("discovered_by", "automated_discovery"),
            "discovery_date": datetime.utcnow().isoformat(),
        }

        result = self.client.table("channel_creators").insert(data).execute()
        return result.data[0]["id"] if result.data else None

    async def insert_creators_batch(self, creators: List[Dict[str, Any]]) -> Dict[str, int]:
        """Insert multiple creators, skipping duplicates"""
        inserted = 0
        skipped = 0

        for creator in creators:
            result = await self.insert_creator(creator)
            if result:
                inserted += 1
            else:
                skipped += 1

        return {"inserted": inserted, "skipped": skipped}


# Singleton
_db: Optional[DatabaseClient] = None


def get_database() -> DatabaseClient:
    global _db
    if _db is None:
        _db = DatabaseClient()
    return _db
