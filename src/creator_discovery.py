"""
Creator Discovery Agent - Automated discovery of UK Black queer creators
Extends the research-agent infrastructure for The Channel video essay project
"""

import asyncio
import re
import json
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
from urllib.parse import urlparse, quote_plus

from .llm import get_llm_client, LLMClient
from .search import SearchAgent
from .database import get_database

# Platform-specific patterns
YOUTUBE_CHANNEL_PATTERNS = [
    r'youtube\.com/@([^/?]+)',
    r'youtube\.com/c/([^/?]+)',
    r'youtube\.com/channel/([^/?]+)',
    r'youtube\.com/user/([^/?]+)',
]

INSTAGRAM_HANDLE_PATTERN = r'instagram\.com/([^/?]+)'
TIKTOK_HANDLE_PATTERN = r'tiktok\.com/@([^/?]+)'
TWITTER_HANDLE_PATTERN = r'(?:twitter|x)\.com/([^/?]+)'


@dataclass
class DiscoveredCreator:
    """Discovered creator data structure"""
    creator_name: str
    location: str
    primary_platform: str

    # Platform handles
    youtube_handle: Optional[str] = None
    instagram_handle: Optional[str] = None
    tiktok_handle: Optional[str] = None
    twitter_handle: Optional[str] = None
    website_url: Optional[str] = None

    # Metadata
    bio: Optional[str] = None
    content_themes: List[str] = None
    pronouns: Optional[str] = None

    # Discovery context
    discovery_method: str = "automated_search"
    discovery_notes: Optional[str] = None
    relevance_score: int = 0

    # Source data
    source_url: Optional[str] = None
    profile_image_url: Optional[str] = None
    follower_count: Optional[int] = None


class CreatorDiscoveryAgent:
    """
    Automated discovery of UK Black queer creators across platforms

    Discovery methods:
    1. YouTube channel search (via DuckDuckGo)
    2. Instagram profile discovery (via search)
    3. TikTok creator search (via search)
    4. Related creator networks (from existing creators)
    """

    def __init__(self):
        self.llm = get_llm_client()
        self.search = SearchAgent(max_results=20)
        self.db = get_database()

        # Search queries for discovery
        self.search_queries = [
            # YouTube - Identity variations
            'site:youtube.com "Black gay" UK',
            'site:youtube.com "Black bisexual" UK',
            'site:youtube.com "Black bi" London',
            'site:youtube.com "Black queer" UK',
            'site:youtube.com "Black LGBT" UK',
            'site:youtube.com "Black LGBTQ" British',
            'site:youtube.com "Black trans" UK',
            'site:youtube.com "Black non-binary" UK',
            'site:youtube.com "SGL" UK',  # Same Gender Loving
            'site:youtube.com "QTIPOC" UK',
            'site:youtube.com "African descent" gay UK',
            'site:youtube.com "Black British" queer',

            # Instagram - Hashtags + terms
            'site:instagram.com "#BlackGayUK"',
            'site:instagram.com "#BlackBisexual"',
            'site:instagram.com "#BlackQueerUK"',
            'site:instagram.com "#BlackLGBT"',
            'site:instagram.com "#BlackGayLondon"',
            'site:instagram.com "#BlackTransUK"',
            'site:instagram.com "#QTIPOC"',
            'site:instagram.com "Black queer" London',
            'site:instagram.com "SGL" UK',

            # TikTok - Hashtags
            'site:tiktok.com "#BlackGayUK"',
            'site:tiktok.com "#BlackBisexual"',
            'site:tiktok.com "#BlackQueerUK"',
            'site:tiktok.com "#BlackLGBT"',
            'site:tiktok.com "#BlackTransUK"',
            'site:tiktok.com "Black queer" UK',
            'site:tiktok.com "SGL" Black UK',

            # Twitter/X - Discourse
            'site:twitter.com "Black gay" UK',
            'site:twitter.com "Black bisexual" UK',
            'site:twitter.com "Black queer" London',
            'site:twitter.com "#BlackLGBT" UK',
            'site:twitter.com "SGL" Black British',

            # General - Community terms
            '"Black gay vlogger" UK',
            '"Black bisexual creator" London',
            '"Black LGBT influencer" UK',
            '"SGL content creator" UK',
            'UK Black Pride speakers',
            'BLKOUT community members',
            '"African Caribbean" LGBT UK',
            '"Black British" LGBT creator',
        ]

        # UK location keywords
        self.uk_locations = [
            'London', 'Manchester', 'Birmingham', 'Leeds', 'Glasgow',
            'Edinburgh', 'Bristol', 'Liverpool', 'Newcastle', 'Sheffield',
            'Cardiff', 'Belfast', 'UK', 'Britain', 'British', 'England',
            'Scotland', 'Wales', 'Northern Ireland'
        ]

        # Content theme keywords
        self.theme_keywords = {
            'mental_health': ['therapy', 'mental health', 'wellness', 'self-care', 'healing'],
            'joy': ['joy', 'celebration', 'happiness', 'fun', 'positive'],
            'dating': ['dating', 'relationships', 'love', 'romance', 'partner'],
            'workplace': ['career', 'workplace', 'professional', 'job', 'work'],
            'fashion': ['fashion', 'style', 'outfit', 'clothing', 'design'],
            'music': ['music', 'artist', 'singer', 'dj', 'producer', 'musician'],
            'politics': ['politics', 'activism', 'policy', 'rights', 'justice'],
            'activism': ['activist', 'organizing', 'community', 'protest', 'movement'],
            'trans_life': ['trans', 'transgender', 'non-binary', 'gender', 'transition'],
            'community': ['community', 'organizing', 'events', 'gathering', 'collective'],
        }

    async def discover_creators(
        self,
        max_creators: int = 50,
        platforms: List[str] = None,
        dry_run: bool = False
    ) -> List[DiscoveredCreator]:
        """
        Main discovery method - searches and analyzes potential creators

        Args:
            max_creators: Maximum number of creators to discover
            platforms: Limit to specific platforms (youtube, instagram, tiktok, twitter)
            dry_run: If True, don't write to database

        Returns:
            List of discovered creators
        """
        print(f"\n🔍 Starting creator discovery (target: {max_creators} creators)...")

        discovered = []
        seen_urls = set()

        # Filter search queries by platform if specified
        queries = self.search_queries
        if platforms:
            queries = [q for q in queries if any(p in q.lower() for p in platforms)]

        for query in queries:
            if len(discovered) >= max_creators:
                break

            print(f"\n📝 Searching: {query}")

            try:
                # Search using DuckDuckGo
                results = await self.search.search(query)

                for result in results:
                    if len(discovered) >= max_creators:
                        break

                    # Skip duplicates
                    if result.url in seen_urls:
                        continue
                    seen_urls.add(result.url)

                    # Check if this is a creator profile
                    creator = await self._analyze_search_result(result)

                    if creator and creator.relevance_score >= 70:
                        # Check if already exists in database
                        if not dry_run:
                            exists = await self._check_creator_exists(creator)
                            if exists:
                                print(f"  ⏭️  Already in database: {creator.creator_name}")
                                continue

                        discovered.append(creator)
                        print(f"  ✅ Discovered: {creator.creator_name} (@{creator.primary_platform}) - Score: {creator.relevance_score}")

            except Exception as e:
                print(f"  ❌ Error searching '{query}': {e}")
                continue

        print(f"\n✨ Discovery complete: Found {len(discovered)} new creators")

        # Save to database
        if not dry_run and discovered:
            saved = await self._save_creators(discovered)
            print(f"💾 Saved {saved} creators to database")

        return discovered

    async def _analyze_search_result(self, result) -> Optional[DiscoveredCreator]:
        """Analyze search result to determine if it's a valid creator profile"""

        # Extract platform from URL
        platform = self._detect_platform(result.url)
        if not platform:
            return None

        # Extract handle from URL
        handle = self._extract_handle(result.url, platform)
        if not handle:
            return None

        # Use LLM to analyze profile
        analysis = await self._llm_analyze_profile(
            url=result.url,
            title=result.title,
            snippet=result.snippet,
            platform=platform
        )

        if not analysis or analysis['relevance_score'] < 70:
            return None

        # Build creator object
        creator = DiscoveredCreator(
            creator_name=analysis.get('creator_name', result.title),
            location=analysis.get('location') or 'London',  # Ensure never null - default to London
            primary_platform=platform,
            bio=analysis.get('bio', result.snippet[:500]),
            content_themes=analysis.get('themes', []),
            pronouns=analysis.get('pronouns'),
            relevance_score=analysis['relevance_score'],
            discovery_method='automated_search',
            discovery_notes=f"Discovered via search: {result.title}",
            source_url=result.url,
        )

        # Set platform handle
        if platform == 'youtube':
            creator.youtube_handle = handle
        elif platform == 'instagram':
            creator.instagram_handle = handle
        elif platform == 'tiktok':
            creator.tiktok_handle = handle
        elif platform == 'twitter':
            creator.twitter_handle = handle
        elif platform == 'website':
            creator.website_url = result.url

        return creator

    async def _llm_analyze_profile(
        self,
        url: str,
        title: str,
        snippet: str,
        platform: str
    ) -> Optional[Dict[str, Any]]:
        """Use GROQ AI to analyze if this is a relevant UK Black queer creator"""

        system_prompt = """You are a creator profile analyzer for The Channel, a UK Black queer creator discovery project.

Analyze the profile and determine:
1. Is this a Black LGBTQ+ creator based in UK/Europe?
2. What is their creator name?
3. What location are they based in?
4. What content themes do they focus on?
5. What are their pronouns (if identifiable)?
6. Relevance score (0-100)

UK locations: London, Manchester, Birmingham, Leeds, Glasgow, Edinburgh, Bristol, Liverpool, Cardiff, Belfast, Dublin, Paris, Berlin, Amsterdam, Brussels

Content themes: mental_health, joy, dating, workplace, fashion, music, politics, activism, trans_life, community, photography, art, writing, performance

Respond with JSON:
{
  "is_relevant": true/false,
  "relevance_score": 0-100,
  "creator_name": "Name",
  "location": "City",
  "bio": "Brief description",
  "themes": ["theme1", "theme2"],
  "pronouns": "they/them" or null,
  "reasoning": "Why this creator is/isn't relevant"
}

Score 90-100: Explicitly UK Black queer creator
Score 70-89: Strong indicators (Black + queer, or Black UK + LGBTQ content)
Score 50-69: Possible but uncertain
Score 0-49: Not relevant
"""

        prompt = f"""Analyze this {platform} profile:

URL: {url}
Title: {title}
Description: {snippet}

Is this a UK-based Black LGBTQ+ content creator?"""

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                system_prompt=system_prompt,
                model="llama-3.3-70b-versatile"
            )

            if result.get('is_relevant') and result.get('relevance_score', 0) >= 70:
                return result
            return None

        except Exception as e:
            print(f"  ⚠️  LLM analysis failed: {e}")
            return None

    def _detect_platform(self, url: str) -> Optional[str]:
        """Detect platform from URL"""
        url_lower = url.lower()

        if 'youtube.com' in url_lower or 'youtu.be' in url_lower:
            return 'youtube'
        elif 'instagram.com' in url_lower:
            return 'instagram'
        elif 'tiktok.com' in url_lower:
            return 'tiktok'
        elif 'twitter.com' in url_lower or 'x.com' in url_lower:
            return 'twitter'
        else:
            # Generic website
            return 'website'

    def _extract_handle(self, url: str, platform: str) -> Optional[str]:
        """Extract creator handle from URL"""

        if platform == 'youtube':
            for pattern in YOUTUBE_CHANNEL_PATTERNS:
                match = re.search(pattern, url)
                if match:
                    return f"@{match.group(1)}"

        elif platform == 'instagram':
            match = re.search(INSTAGRAM_HANDLE_PATTERN, url)
            if match:
                return f"@{match.group(1)}"

        elif platform == 'tiktok':
            match = re.search(TIKTOK_HANDLE_PATTERN, url)
            if match:
                return match.group(1)  # Already includes @

        elif platform == 'twitter':
            match = re.search(TWITTER_HANDLE_PATTERN, url)
            if match:
                return f"@{match.group(1)}"

        return None

    async def _check_creator_exists(self, creator: DiscoveredCreator) -> bool:
        """Check if creator already exists in database"""

        return await self.db.creator_exists(
            youtube_handle=creator.youtube_handle,
            instagram_handle=creator.instagram_handle,
            tiktok_handle=creator.tiktok_handle,
            twitter_handle=creator.twitter_handle
        )

    async def _save_creators(self, creators: List[DiscoveredCreator]) -> int:
        """Save discovered creators to database"""

        # Convert DiscoveredCreator objects to dicts
        creator_dicts = []
        for creator in creators:
            creator_dicts.append({
                "creator_name": creator.creator_name,
                "location": creator.location,
                "primary_platform": creator.primary_platform,
                "youtube_handle": creator.youtube_handle,
                "instagram_handle": creator.instagram_handle,
                "tiktok_handle": creator.tiktok_handle,
                "twitter_handle": creator.twitter_handle,
                "website_url": creator.website_url,
                "bio": creator.bio,
                "content_themes": creator.content_themes or [],
                "pronouns": creator.pronouns,
                "discovery_notes": creator.discovery_notes,
                "discovered_by": creator.discovery_method,
            })

        # Use database client batch insert
        result = await self.db.insert_creators_batch(creator_dicts)
        return result['inserted']

    async def discover_related_creators(
        self,
        seed_creator_handle: str,
        platform: str,
        max_related: int = 10
    ) -> List[DiscoveredCreator]:
        """
        Discover related creators from a seed creator
        (e.g., YouTube recommended channels, Instagram following)

        Note: This requires API access or web scraping - Phase 2 feature
        """
        # TODO: Implement in Phase 2
        # - YouTube: Scrape "Channels" tab or use YouTube Data API
        # - Instagram: Scrape "Following" list (requires authentication)
        # - TikTok: Scrape "Following" or suggested creators
        pass


# CLI interface
async def main():
    """CLI entry point for creator discovery"""
    import argparse

    parser = argparse.ArgumentParser(description='Discover UK Black queer creators')
    parser.add_argument('--max', type=int, default=50, help='Max creators to discover')
    parser.add_argument('--platform', choices=['youtube', 'instagram', 'tiktok', 'twitter'], help='Limit to specific platform')
    parser.add_argument('--dry-run', action='store_true', help='Test mode - no database writes')

    args = parser.parse_args()

    agent = CreatorDiscoveryAgent()

    platforms = [args.platform] if args.platform else None

    creators = await agent.discover_creators(
        max_creators=args.max,
        platforms=platforms,
        dry_run=args.dry_run
    )

    print(f"\n📊 Discovery Summary:")
    print(f"   Total discovered: {len(creators)}")

    if creators:
        print(f"\n🎯 Top discoveries:")
        for i, creator in enumerate(creators[:10], 1):
            print(f"   {i}. {creator.creator_name} (@{creator.primary_platform}) - Score: {creator.relevance_score}")

    return creators


if __name__ == "__main__":
    asyncio.run(main())
