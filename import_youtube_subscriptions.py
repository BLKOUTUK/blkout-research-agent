#!/usr/bin/env python3
"""
Import BLKOUT YouTube Subscriptions - Filter relevant Black queer creators
Uses AI to analyze which subscriptions are individual creators vs. organizations

Usage:
    python import_youtube_subscriptions.py --file ../apps/channel-blkout/database/seed-data/blkout-youtube-subscriptions.csv
    python import_youtube_subscriptions.py --dry-run  # Test mode
"""

import asyncio
import csv
import sys
import os
from pathlib import Path
from dotenv import load_dotenv
from typing import List, Dict, Any, Optional

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.llm import get_llm_client
from src.database import get_database


class YouTubeSubscriptionImporter:
    """Import and filter BLKOUT YouTube subscriptions for relevant creators"""

    def __init__(self):
        self.llm = get_llm_client()
        self.db = get_database()

    async def analyze_channel(self, channel_title: str, channel_url: str) -> Optional[Dict[str, Any]]:
        """Use AI to determine if this is a relevant creator"""

        system_prompt = """You are analyzing YouTube channels subscribed to by BLKOUT UK (a Black queer community platform) to identify individual Black LGBTQ+ creators vs. organizations/non-relevant channels.

Analyze the channel title and determine:
1. Is this an individual Black LGBTQ+ content creator? (not an organization, news outlet, or tech channel)
2. What type is it? (individual_creator, organization, media, non_relevant)
3. What's their likely location? (UK-based or international)
4. What content themes do they likely cover?
5. Relevance score (0-100) for The Channel project

Categories:
- **individual_creator**: Personal channels (TeeAndDrew, Get The Belt Podcast, MrClarkKentUK)
- **uk_black_queer_org**: UK Black queer organizations (UK Black Pride, FGUK Magazine, Nubian Voices LGBT UK)
- **general_lgbt_org**: General LGBTQ+ orgs (not Black-specific)
- **mainstream_media**: News/media outlets (The Guardian, BBC, Wall Street Journal)
- **non_relevant**: Tech, business, unrelated (AppSumo, Better Stack, Thomas Frank)

Respond with JSON:
{
  "is_relevant": true/false,
  "channel_type": "individual_creator" | "uk_black_queer_org" | "general_lgbt_org" | "mainstream_media" | "non_relevant",
  "location": "London" or "UK" or "International" or null,
  "content_themes": ["theme1", "theme2"],
  "relevance_score": 0-100,
  "reasoning": "Brief explanation"
}

Score 90-100: Individual Black LGBTQ+ creator or UK Black queer organization
Score 70-89: Relevant individual or organization
Score 50-69: General LGBTQ+ (not Black-specific)
Score 0-49: Not relevant (mainstream media, tech, unrelated)
"""

        prompt = f"""Analyze this YouTube channel from BLKOUT UK's subscriptions:

Channel Title: {channel_title}
Channel URL: {channel_url}

Is this an individual Black LGBTQ+ content creator suitable for The Channel video essay project?"""

        try:
            result = await self.llm.complete_json(
                prompt=prompt,
                system_prompt=system_prompt,
                model="llama-3.3-70b-versatile"
            )

            return result

        except Exception as e:
            print(f"  ⚠️  AI analysis failed for {channel_title}: {e}")
            return None

    async def import_subscriptions(
        self,
        csv_file: str,
        dry_run: bool = False,
        min_score: int = 70
    ) -> Dict[str, Any]:
        """Import YouTube subscriptions, filtering for relevant creators"""

        print(f"\n📺 Importing BLKOUT YouTube Subscriptions")
        print(f"   File: {csv_file}")
        print(f"   Min score: {min_score}")
        print(f"   Dry run: {dry_run}\n")

        # Read CSV
        channels = []
        with open(csv_file, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            channels = list(reader)

        print(f"📊 Total subscriptions: {len(channels)}\n")

        # Analyze each channel
        relevant_creators = []
        organizations = []
        non_relevant = []

        for i, channel in enumerate(channels, 1):
            title = channel['channel_title']
            url = channel['channel_url']
            channel_id = channel['channel_id']

            print(f"[{i}/{len(channels)}] Analyzing: {title}")

            # AI analysis
            analysis = await self.analyze_channel(title, url)

            if not analysis:
                print(f"  ⏭️  Skipped (analysis failed)\n")
                continue

            score = analysis.get('relevance_score', 0)
            channel_type = analysis.get('channel_type', 'non_relevant')

            # Categorize - Include both individual creators AND UK Black queer organizations
            if analysis.get('is_relevant') and score >= min_score:
                # Accept: individual_creator OR uk_black_queer_org
                if channel_type in ['individual_creator', 'uk_black_queer_org']:
                    relevant_creators.append({
                        'channel_title': title,
                        'channel_url': url,
                        'channel_id': channel_id,
                        'analysis': analysis
                    })
                    emoji = "✅" if channel_type == 'individual_creator' else "🏛️"
                    print(f"  {emoji} RELEVANT - Score: {score} ({channel_type})")
                    print(f"     Location: {analysis.get('location', 'Unknown')}")
                    print(f"     Themes: {', '.join(analysis.get('content_themes', [])[:3])}\n")
                else:
                    # General LGBT org (not Black-specific) - still track
                    organizations.append({
                        'channel_title': title,
                        'score': score,
                        'type': channel_type
                    })
                    print(f"  📋 {channel_type} - Score: {score}")
                    print(f"     {analysis.get('reasoning', '')}\n")

            elif channel_type == 'general_lgbt_org' and score >= 60:
                organizations.append({
                    'channel_title': title,
                    'score': score,
                    'type': channel_type
                })
                print(f"  📋 General LGBT org - Score: {score}")
                print(f"     {analysis.get('reasoning', '')}\n")

            else:
                non_relevant.append({
                    'channel_title': title,
                    'channel_type': channel_type,
                    'score': score
                })
                print(f"  ⏭️  Not relevant - Score: {score} ({channel_type})\n")

            # Rate limit protection (GROQ free tier: 30 req/min)
            if i % 25 == 0:
                print("⏸️  Pausing 60s to respect rate limits...\n")
                await asyncio.sleep(60)

        # Summary
        print(f"\n{'='*60}")
        print(f"📊 Analysis Complete")
        print(f"{'='*60}")
        print(f"✅ Relevant creators: {len(relevant_creators)}")
        print(f"📋 Organizations: {len(organizations)}")
        print(f"⏭️  Non-relevant: {len(non_relevant)}")
        print(f"\n")

        # Save to database
        if not dry_run and relevant_creators:
            print(f"💾 Saving {len(relevant_creators)} creators to database...\n")

            saved = await self._save_creators(relevant_creators)

            print(f"✅ Saved {saved['inserted']} creators")
            print(f"⏭️  Skipped {saved['skipped']} duplicates\n")

            return {
                'analyzed': len(channels),
                'relevant': len(relevant_creators),
                'saved': saved['inserted'],
                'skipped': saved['skipped']
            }
        else:
            print(f"[DRY RUN] Would save {len(relevant_creators)} creators\n")

            return {
                'analyzed': len(channels),
                'relevant': len(relevant_creators),
                'saved': 0,
                'skipped': 0
            }

    async def _save_creators(self, creators: List[Dict[str, Any]]) -> Dict[str, int]:
        """Save creators to database"""

        creator_dicts = []

        for item in creators:
            analysis = item['analysis']
            channel_id = item['channel_id']

            # Extract handle from channel URL (@username format)
            youtube_handle = f"@{channel_id}"  # Will update to proper @handle if found

            creator_data = {
                "creator_name": item['channel_title'],
                "location": analysis.get('location') or 'UK',
                "primary_platform": "youtube",
                "youtube_handle": youtube_handle,
                "bio": analysis.get('reasoning', '')[:1000],
                "content_themes": analysis.get('content_themes', []),
                "discovery_notes": f"Imported from BLKOUT UK YouTube subscriptions. Score: {analysis.get('relevance_score')}",
                "discovered_by": "blkout_subscriptions",
            }

            creator_dicts.append(creator_data)

        # Batch insert
        result = await self.db.insert_creators_batch(creator_dicts)
        return result


async def main():
    """CLI entry point"""
    import argparse

    parser = argparse.ArgumentParser(description='Import BLKOUT YouTube subscriptions')
    parser.add_argument(
        '--file',
        type=str,
        default='../apps/channel-blkout/database/seed-data/blkout-youtube-subscriptions.csv',
        help='CSV file path'
    )
    parser.add_argument('--dry-run', action='store_true', help='Test mode - no database writes')
    parser.add_argument('--min-score', type=int, default=70, help='Minimum relevance score (default: 70)')

    args = parser.parse_args()

    importer = YouTubeSubscriptionImporter()

    result = await importer.import_subscriptions(
        csv_file=args.file,
        dry_run=args.dry_run,
        min_score=args.min_score
    )

    # Final summary
    print(f"{'='*60}")
    print(f"🎉 Import Complete")
    print(f"{'='*60}")
    print(f"Analyzed: {result['analyzed']} channels")
    print(f"Relevant creators: {result['relevant']}")
    print(f"Saved to database: {result['saved']}")
    print(f"Duplicates skipped: {result['skipped']}")
    print(f"{'='*60}\n")

    return result


if __name__ == "__main__":
    asyncio.run(main())
