"""
Grant Funding Research Agent

Discovers grant opportunities relevant to BLKOUT's mission:
- Black LGBTQ+ community support
- Participatory arts
- Gender justice
- Community wealth / cooperative economy
- Independent media
"""

import asyncio
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime, timedelta

from .llm import get_llm_client
from .search import SearchAgent
from .database import get_database
from .notifications import get_notifier

import sys
sys.path.append("..")
from configs.grants_config import (
    grant_search_queries,
    funder_websites,
    high_relevance_keywords,
    lgbtq_keywords,
    black_keywords,
    arts_keywords,
    community_wealth_keywords,
    relevance_threshold,
    funder_types,
    program_areas,
)


@dataclass
class DiscoveredGrant:
    """A discovered grant opportunity"""
    title: str
    funder_name: str
    url: str
    description: str
    deadline: Optional[str] = None
    amount_min: Optional[float] = None
    amount_max: Optional[float] = None
    funder_type: str = "trust_foundation"
    program_area: str = "community_development"
    relevance_score: int = 0
    fit_reasoning: str = ""
    geographic_scope: str = "UK"
    tags: List[str] = None


class GrantResearchAgent:
    """Agent for discovering grant funding opportunities"""

    def __init__(self):
        self.llm = get_llm_client()
        self.search = SearchAgent(max_results=15)
        self.db = get_database()

    def _quick_relevance_check(self, text: str) -> int:
        """Fast keyword-based relevance check"""
        text_lower = text.lower()

        # Check for high-relevance intersectional terms
        for term in high_relevance_keywords:
            if term in text_lower:
                return 95

        # Check category combinations
        has_lgbtq = any(kw in text_lower for kw in lgbtq_keywords)
        has_black = any(kw in text_lower for kw in black_keywords)
        has_arts = any(kw in text_lower for kw in arts_keywords)
        has_coop = any(kw in text_lower for kw in community_wealth_keywords)

        # Scoring based on alignment
        score = 30  # Base score for any grant

        if has_lgbtq and has_black:
            score = 90  # Perfect intersectional fit
        elif has_lgbtq:
            score += 25
        elif has_black:
            score += 25

        if has_arts:
            score += 15
        if has_coop:
            score += 15

        # Check for "open" or "deadline" indicating active opportunity
        if "open" in text_lower or "deadline" in text_lower or "apply" in text_lower:
            score += 10

        return min(100, score)

    async def _analyze_grant_with_llm(self, title: str, snippet: str, url: str) -> Dict[str, Any]:
        """Use LLM to analyze grant fit for BLKOUT"""
        prompt = f"""Analyze this grant opportunity for BLKOUT - a community-owned liberation platform for Black queer men in the UK.

BLKOUT's focus areas:
- Black LGBTQ+ community wellbeing and connection
- Participatory arts and storytelling
- Community wealth building / cooperative ownership
- Independent media and journalism
- Gender justice and trans inclusion

Grant: {title}
Description: {snippet}
URL: {url}

Respond in JSON format:
{{
    "relevance_score": 0-100,
    "fit_reasoning": "Why this is/isn't a good fit for BLKOUT",
    "funder_type": "one of: trust_foundation, lottery, arts_council, lgbtq_specific, racial_justice, gender_justice, community_wealth, media_journalism, corporate, government",
    "program_area": "one of: community_development, arts_culture, health_wellbeing, racial_justice, lgbtq_rights, gender_justice, media_communications, cooperative_economy, youth, mental_health, capacity_building, core_costs",
    "estimated_amount_range": "e.g. '5000-20000' or 'unknown'",
    "deadline_mentioned": "date if found, else null",
    "priority": "high/medium/low",
    "tags": ["relevant", "tags"]
}}"""

        try:
            response = await self.llm.complete(prompt)
            # Parse JSON from response
            import json
            # Find JSON in response
            start = response.find("{")
            end = response.rfind("}") + 1
            if start >= 0 and end > start:
                return json.loads(response[start:end])
        except Exception as e:
            print(f"[GrantAgent] LLM analysis error: {e}")

        return {}

    async def research(self, time_range: str = "m") -> List[DiscoveredGrant]:
        """Execute grant research across all configured queries"""
        print(f"[GrantAgent] Starting research with {len(grant_search_queries)} queries...")

        # Phase 1: Search
        all_results = await self.search.multi_search(
            grant_search_queries,
            search_type="web",
            time_range=time_range,
        )
        print(f"[GrantAgent] Found {len(all_results)} raw results")

        # Phase 2: Quick filter
        candidates = []
        for result in all_results:
            combined_text = f"{result.title} {result.snippet}"
            quick_score = self._quick_relevance_check(combined_text)
            if quick_score >= 40:  # Worth deeper analysis
                candidates.append((result, quick_score))

        print(f"[GrantAgent] {len(candidates)} candidates passed quick filter")

        # Phase 3: LLM analysis for promising opportunities
        discovered = []
        for result, quick_score in candidates:
            if quick_score >= 75:
                # High confidence, do LLM analysis for details
                analysis = await self._analyze_grant_with_llm(
                    result.title, result.snippet, result.url
                )

                # Parse amount range
                amount_min, amount_max = None, None
                if analysis.get("estimated_amount_range") and analysis["estimated_amount_range"] != "unknown":
                    try:
                        parts = analysis["estimated_amount_range"].replace("£", "").replace(",", "").split("-")
                        if len(parts) == 2:
                            amount_min = float(parts[0].strip())
                            amount_max = float(parts[1].strip())
                    except:
                        pass

                discovered.append(DiscoveredGrant(
                    title=result.title,
                    funder_name=self._extract_funder_name(result.title, result.source),
                    url=result.url,
                    description=result.snippet,
                    deadline=analysis.get("deadline_mentioned"),
                    amount_min=amount_min,
                    amount_max=amount_max,
                    funder_type=analysis.get("funder_type", "trust_foundation"),
                    program_area=analysis.get("program_area", "community_development"),
                    relevance_score=analysis.get("relevance_score", quick_score),
                    fit_reasoning=analysis.get("fit_reasoning", ""),
                    tags=analysis.get("tags", []),
                ))
            elif quick_score >= relevance_threshold:
                # Medium confidence, include with basic info
                discovered.append(DiscoveredGrant(
                    title=result.title,
                    funder_name=self._extract_funder_name(result.title, result.source),
                    url=result.url,
                    description=result.snippet,
                    relevance_score=quick_score,
                    fit_reasoning="Keyword match - needs manual review",
                ))

        # Sort by relevance
        discovered.sort(key=lambda x: x.relevance_score, reverse=True)
        print(f"[GrantAgent] Discovered {len(discovered)} relevant grant opportunities")

        return discovered

    def _extract_funder_name(self, title: str, source: str) -> str:
        """Extract funder name from title or source"""
        # Check against known funders
        known_funders = [
            "National Lottery", "Arts Council", "Tudor Trust", "Esmée Fairbairn",
            "Paul Hamlyn", "Comic Relief", "Joseph Rowntree", "Lankelly Chase",
            "Baring Foundation", "City Bridge", "Trust for London", "Power to Change",
            "Elton John", "LGBT Foundation", "Stonewall",
        ]

        text = f"{title} {source}".lower()
        for funder in known_funders:
            if funder.lower() in text:
                return funder

        # Default to source domain
        return source.split(".")[0].title() if source else "Unknown Funder"

    async def research_and_save(self, time_range: str = "m") -> Dict[str, Any]:
        """Research and save grants to database"""
        grants = await self.research(time_range)

        # Convert to dict format for database
        inserted = 0
        skipped = 0

        for grant in grants:
            try:
                result = await self._insert_grant(grant)
                if result:
                    inserted += 1
                else:
                    skipped += 1
            except Exception as e:
                print(f"[GrantAgent] Insert error: {e}")
                skipped += 1

        # Log the run
        await self.db.log_discovery_run("grants", {
            "total_found": len(grants),
            "inserted": inserted,
            "skipped": skipped,
        })

        return {
            "discovered": len(grants),
            "inserted": inserted,
            "skipped": skipped,
        }

    async def _insert_grant(self, grant: DiscoveredGrant) -> Optional[str]:
        """Insert a grant opportunity into the database"""
        # Check for duplicate by URL
        url_hash = self.db._generate_hash(grant.url)
        existing = self.db.client.table("grants").select("id").eq("application_url", grant.url).execute()

        if existing.data:
            return None  # Already exists

        data = {
            "title": grant.title[:500],
            "funder_name": grant.funder_name,
            "funder_type": grant.funder_type,
            "program_area": grant.program_area,
            "application_url": grant.url,
            "notes": grant.description,
            "deadline_date": grant.deadline,
            "fit_score": grant.relevance_score,
            "funder_advice": grant.fit_reasoning,
            "geographic_scope": grant.geographic_scope,
            "tags": grant.tags or [],
            "status": "researching",  # Requires human review
            "priority": "high" if grant.relevance_score >= 80 else "medium" if grant.relevance_score >= 60 else "low",
            "metadata": {
                "discovery_method": "research_agent",
                "discovered_at": datetime.utcnow().isoformat(),
            },
        }

        # Add amount if known
        if grant.amount_min:
            data["min_viable_budget"] = grant.amount_min
        if grant.amount_max:
            data["max_potential_budget"] = grant.amount_max

        result = self.db.client.table("grants").insert(data).execute()
        return result.data[0]["id"] if result.data else None


class GrantPlanningAgent:
    """Coordinates grant research with campaign planning"""

    def __init__(self):
        self.grant_agent = GrantResearchAgent()
        self.db = get_database()
        self.notifier = get_notifier()

    async def run_weekly_research(self) -> Dict[str, Any]:
        """Run weekly grant opportunity research"""
        print("[GrantPlanning] Starting weekly grant research...")

        results = {
            "timestamp": datetime.utcnow().isoformat(),
            "grants": {},
            "errors": [],
        }

        try:
            results["grants"] = await self.grant_agent.research_and_save(time_range="m")

            # Send email notification with new grants and top priorities
            await self._send_digest_email(results["grants"])

        except Exception as e:
            results["errors"].append(f"Grant research failed: {str(e)}")
            print(f"[GrantPlanning] Error: {e}")

        print(f"[GrantPlanning] Research complete: {results}")
        return results

    async def _send_digest_email(self, run_stats: Dict[str, Any]) -> None:
        """Send email digest with new discoveries and top priorities"""
        try:
            # Get newly discovered grants (last 24 hours, high relevance)
            new_grants = await self._get_recent_discoveries()

            # Get top 10 priority grants overall
            top_priority = await self._get_top_priority_grants()

            # Send digest
            await self.notifier.send_grants_digest(
                new_grants=new_grants,
                top_priority=top_priority,
                run_stats=run_stats,
            )
        except Exception as e:
            print(f"[GrantPlanning] Email notification error: {e}")

    async def _get_recent_discoveries(self) -> list:
        """Get grants discovered in the last run"""
        try:
            response = self.db.client.table("grants")\
                .select("title, funder_name, application_url, deadline_date, fit_score, funder_advice, priority, notes")\
                .eq("status", "researching")\
                .gte("fit_score", 60)\
                .order("created_at", desc=True)\
                .limit(20)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"[GrantPlanning] Error fetching recent grants: {e}")
            return []

    async def _get_top_priority_grants(self) -> list:
        """Get top 10 highest priority grant opportunities"""
        try:
            response = self.db.client.table("grants")\
                .select("title, funder_name, application_url, deadline_date, fit_score, funder_advice, priority")\
                .neq("status", "declined")\
                .neq("status", "submitted")\
                .order("fit_score", desc=True)\
                .limit(10)\
                .execute()
            return response.data if response.data else []
        except Exception as e:
            print(f"[GrantPlanning] Error fetching top priority grants: {e}")
            return []

    async def run_deadline_check(self) -> Dict[str, Any]:
        """Check for upcoming grant deadlines"""
        print("[GrantPlanning] Checking upcoming deadlines...")

        # Get grants with deadlines in next 30 days
        today = datetime.utcnow().date().isoformat()
        month_ahead = (datetime.utcnow() + timedelta(days=30)).date().isoformat()

        response = self.db.client.table("grants")\
            .select("title, funder_name, deadline_date, status, priority")\
            .gte("deadline_date", today)\
            .lte("deadline_date", month_ahead)\
            .neq("status", "submitted")\
            .neq("status", "declined")\
            .order("deadline_date", desc=False)\
            .execute()

        upcoming = response.data if response.data else []

        return {
            "upcoming_deadlines": len(upcoming),
            "grants": upcoming,
        }
