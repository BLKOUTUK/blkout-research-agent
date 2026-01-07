#!/usr/bin/env python3
"""
Test script for OutSavvy scraper fixes
"""

import asyncio
import sys
from src.scraper import ScraperAgent


async def test_outsavvy_scraper():
    """Test OutSavvy scraping with new selectors"""
    print("=" * 60)
    print("TESTING OUTSAVVY SCRAPER")
    print("=" * 60)

    async with ScraperAgent(headless=True, timeout=30000) as scraper:
        print("\n1. Testing OutSavvy search for 'Black LGBTQ'...")
        events = await scraper.scrape_outsavvy("Black LGBTQ")

        print(f"\n✓ Found {len(events)} events from OutSavvy")

        if events:
            print("\n--- Sample Event Data ---")
            sample = events[0]
            print(f"Name: {sample.name}")
            print(f"URL: {sample.url}")
            print(f"Date: {sample.date}")
            print(f"Venue: {sample.venue}")
            print(f"Price: {sample.price}")
            print(f"Description: {sample.description[:100] if sample.description else 'N/A'}...")
            print(f"Platform: {sample.source_platform}")

            # Show all event names
            print("\n--- All Events Found ---")
            for i, event in enumerate(events[:10], 1):
                print(f"{i}. {event.name}")
            if len(events) > 10:
                print(f"... and {len(events) - 10} more events")
        else:
            print("\n⚠ Warning: No events found!")
            print("This could indicate:")
            print("- Selector issues (check OutSavvy HTML structure)")
            print("- Network/timeout issues")
            print("- No matching events for this query")
            return False

    return len(events) > 0


async def test_all_platforms():
    """Test scraping all platforms with error isolation"""
    print("\n" + "=" * 60)
    print("TESTING ALL PLATFORMS WITH ERROR ISOLATION")
    print("=" * 60)

    async with ScraperAgent(headless=True, timeout=30000) as scraper:
        events = await scraper.scrape_all_platforms()

        print(f"\n✓ Total unique events discovered: {len(events)}")

        # Group by platform
        by_platform = {}
        for event in events:
            platform = event.source_platform or "Unknown"
            by_platform[platform] = by_platform.get(platform, 0) + 1

        print("\n--- Events by Platform ---")
        for platform, count in sorted(by_platform.items()):
            print(f"{platform}: {count} events")

        return len(events) > 0


if __name__ == "__main__":
    print("Starting scraper tests...\n")

    try:
        # Test OutSavvy specifically
        success = asyncio.run(test_outsavvy_scraper())

        if not success:
            print("\n❌ OutSavvy test FAILED")
            sys.exit(1)

        # Test all platforms
        print("\n")
        success = asyncio.run(test_all_platforms())

        if success:
            print("\n✓ All tests PASSED!")
            sys.exit(0)
        else:
            print("\n⚠ Tests completed but no events found")
            sys.exit(1)

    except Exception as e:
        print(f"\n❌ Test FAILED with error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
