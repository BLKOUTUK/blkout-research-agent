"""
IVOR Intelligence Sync Module

Syncs discovered news and events to ivor_intelligence table,
enabling IVOR to confidently discuss current community happenings.
"""

import os
import json
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from supabase import create_client, Client


class IVORSync:
    """Syncs research agent discoveries to IVOR's intelligence system."""

    def __init__(self):
        self.client: Client = create_client(
            os.getenv("SUPABASE_URL"),
            os.getenv("SUPABASE_SERVICE_ROLE_KEY")
        )

    async def sync_daily_discoveries(self, discovery_stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        After each discovery run, sync a summary to ivor_intelligence.
        IVOR can then confidently discuss recent news and upcoming events.
        """
        results = {
            "news_synced": False,
            "events_synced": False,
            "errors": []
        }

        try:
            # Sync recent news summary
            news_result = await self._sync_news_intelligence()
            results["news_synced"] = news_result.get("success", False)

            # Sync upcoming events summary
            events_result = await self._sync_events_intelligence()
            results["events_synced"] = events_result.get("success", False)

            # Sync discovery run metadata
            await self._sync_discovery_metadata(discovery_stats)

        except Exception as e:
            results["errors"].append(str(e))

        return results

    async def _sync_news_intelligence(self) -> Dict[str, Any]:
        """
        Create/update news intelligence entry for IVOR.
        Summarizes recent high-relevance articles.
        """
        try:
            # Get recent high-relevance news (last 7 days)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()

            response = self.client.table("news_articles")\
                .select("title, excerpt, source_name, category, created_at")\
                .eq("discovery_method", "research_agent")\
                .gte("created_at", week_ago)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()

            articles = response.data if response.data else []

            if not articles:
                return {"success": True, "message": "No recent news to sync"}

            # Build intelligence summary
            intelligence_data = {
                "total_articles": len(articles),
                "categories": self._count_by_field(articles, "category"),
                "sources": self._count_by_field(articles, "source_name"),
                "recent_headlines": [
                    {
                        "title": a["title"],
                        "source": a["source_name"],
                        "category": a["category"]
                    }
                    for a in articles[:10]
                ],
                "last_updated": datetime.utcnow().isoformat()
            }

            key_insights = self._extract_news_insights(articles)

            # Upsert to ivor_intelligence
            self.client.table("ivor_intelligence").upsert({
                "intelligence_type": "community_needs",
                "ivor_service": "research_agent",
                "ivor_endpoint": "/discovery/news",
                "intelligence_data": intelligence_data,
                "summary": f"Discovered {len(articles)} relevant news articles this week covering Black LGBTQ+ UK community.",
                "key_insights": key_insights,
                "actionable_items": [
                    "Share trending stories with community",
                    "Highlight underreported topics",
                    "Connect news to upcoming events"
                ],
                "relevance_score": 0.85,
                "priority": "high",
                "data_timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(days=1)).isoformat(),
                "is_stale": False,
                "tags": ["news", "community", "current_events", "research_agent"]
            }, on_conflict="intelligence_type,ivor_service").execute()

            return {"success": True, "articles_synced": len(articles)}

        except Exception as e:
            print(f"[IVOR Sync] News sync error: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_events_intelligence(self) -> Dict[str, Any]:
        """
        Create/update events intelligence entry for IVOR.
        Summarizes upcoming community events.
        """
        try:
            # Get upcoming events (next 30 days)
            today = datetime.utcnow().date().isoformat()
            month_ahead = (datetime.utcnow() + timedelta(days=30)).date().isoformat()

            response = self.client.table("events")\
                .select("title, description, date, location, organizer, source")\
                .eq("discovery_method", "research_agent")\
                .gte("date", today)\
                .lte("date", month_ahead)\
                .order("date", desc=False)\
                .limit(30)\
                .execute()

            events = response.data if response.data else []

            if not events:
                return {"success": True, "message": "No upcoming events to sync"}

            # Build intelligence summary
            intelligence_data = {
                "total_events": len(events),
                "locations": self._count_by_field(events, "location"),
                "organizers": self._count_by_field(events, "organizer"),
                "upcoming_events": [
                    {
                        "title": e["title"],
                        "date": e["date"],
                        "location": e["location"],
                        "organizer": e["organizer"]
                    }
                    for e in events[:15]
                ],
                "this_week": [e for e in events if self._is_this_week(e.get("date"))],
                "last_updated": datetime.utcnow().isoformat()
            }

            key_insights = self._extract_events_insights(events)

            # Upsert to ivor_intelligence
            self.client.table("ivor_intelligence").upsert({
                "intelligence_type": "organizing_events",
                "ivor_service": "research_agent",
                "ivor_endpoint": "/discovery/events",
                "intelligence_data": intelligence_data,
                "summary": f"Found {len(events)} upcoming Black LGBTQ+ events in the next 30 days.",
                "key_insights": key_insights,
                "actionable_items": [
                    "Promote events to community members",
                    "Suggest events based on interests",
                    "Connect members with similar event preferences"
                ],
                "relevance_score": 0.90,
                "priority": "high",
                "urgency": "elevated" if len([e for e in events if self._is_this_week(e.get("date"))]) > 0 else "normal",
                "data_timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=12)).isoformat(),
                "is_stale": False,
                "tags": ["events", "community", "upcoming", "research_agent"]
            }, on_conflict="intelligence_type,ivor_service").execute()

            return {"success": True, "events_synced": len(events)}

        except Exception as e:
            print(f"[IVOR Sync] Events sync error: {e}")
            return {"success": False, "error": str(e)}

    async def _sync_discovery_metadata(self, stats: Dict[str, Any]) -> None:
        """Sync discovery run metadata for IVOR's awareness of agent activity."""
        try:
            self.client.table("ivor_intelligence").upsert({
                "intelligence_type": "resources",
                "ivor_service": "research_agent",
                "ivor_endpoint": "/discovery/status",
                "intelligence_data": {
                    "last_run": datetime.utcnow().isoformat(),
                    "stats": stats,
                    "agent_status": "active",
                    "next_scheduled_run": self._get_next_run_time()
                },
                "summary": f"Research agent last ran at {datetime.utcnow().strftime('%Y-%m-%d %H:%M')} UTC",
                "key_insights": [
                    f"Discovered {stats.get('news', {}).get('discovered', 0)} news articles",
                    f"Found {stats.get('events', {}).get('discovered', 0)} events",
                    "Agent is actively monitoring community content"
                ],
                "relevance_score": 0.70,
                "priority": "medium",
                "data_timestamp": datetime.utcnow().isoformat(),
                "expires_at": (datetime.utcnow() + timedelta(hours=24)).isoformat(),
                "is_stale": False,
                "tags": ["agent_status", "research_agent", "metadata"]
            }, on_conflict="intelligence_type,ivor_service").execute()

        except Exception as e:
            print(f"[IVOR Sync] Metadata sync error: {e}")

    def _count_by_field(self, items: List[Dict], field: str) -> Dict[str, int]:
        """Count occurrences by field value."""
        counts = {}
        for item in items:
            value = item.get(field, "Unknown")
            if value:
                counts[value] = counts.get(value, 0) + 1
        return counts

    def _is_this_week(self, date_str: Optional[str]) -> bool:
        """Check if date is within this week."""
        if not date_str:
            return False
        try:
            date = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
            week_end = datetime.utcnow() + timedelta(days=7)
            return date <= week_end
        except:
            return False

    def _extract_news_insights(self, articles: List[Dict]) -> List[str]:
        """Extract key insights from news articles."""
        insights = []

        # Category distribution
        categories = self._count_by_field(articles, "category")
        if categories:
            top_category = max(categories, key=categories.get)
            insights.append(f"Most coverage in {top_category} ({categories[top_category]} articles)")

        # Source diversity
        sources = self._count_by_field(articles, "source_name")
        insights.append(f"Content from {len(sources)} different sources")

        # Recent activity
        insights.append(f"{len(articles)} relevant articles discovered this week")

        return insights[:5]

    def _extract_events_insights(self, events: List[Dict]) -> List[str]:
        """Extract key insights from events."""
        insights = []

        # This week's events
        this_week = [e for e in events if self._is_this_week(e.get("date"))]
        if this_week:
            insights.append(f"{len(this_week)} events happening this week")

        # Location distribution
        locations = self._count_by_field(events, "location")
        if locations:
            top_location = max(locations, key=locations.get)
            insights.append(f"Most events in {top_location}")

        # Organizer activity
        organizers = self._count_by_field(events, "organizer")
        insights.append(f"Events from {len(organizers)} different organizers")

        return insights[:5]

    def _get_next_run_time(self) -> str:
        """Calculate next scheduled run time."""
        now = datetime.utcnow()
        # Next 6 AM run
        next_run = now.replace(hour=6, minute=0, second=0, microsecond=0)
        if now.hour >= 6:
            next_run += timedelta(days=1)
        return next_run.isoformat()
