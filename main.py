#!/usr/bin/env python3
"""
BLKOUT Research Agent - Main Entry Point

Usage:
    python main.py                    # Run scheduler (daemon mode)
    python main.py --run-now daily    # Run daily discovery immediately
    python main.py --run-now events   # Run events discovery immediately
    python main.py --run-now weekly   # Run weekly deep research immediately
    python main.py --run-now grants   # Run grant research immediately
    python main.py --test             # Test mode (no database writes)
"""

import asyncio
import argparse
import os
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


def check_config():
    """Verify required configuration"""
    required = ["GROQ_API_KEY", "SUPABASE_URL", "SUPABASE_SERVICE_ROLE_KEY"]
    missing = [var for var in required if not os.getenv(var)]

    if missing:
        print("Missing required environment variables:")
        for var in missing:
            print(f"  - {var}")
        print("\nCopy .env.template to .env and fill in your values.")
        return False
    return True


async def run_test():
    """Test mode - run discovery without saving to database"""
    from src.agents import NewsResearchAgent, EventsDiscoveryAgent

    print("=" * 60)
    print("BLKOUT Research Agent - Test Mode")
    print("=" * 60)

    # Test news research
    print("\n[TEST] News Research Agent")
    print("-" * 40)
    news_agent = NewsResearchAgent()
    articles = await news_agent.research(time_range="w")

    print(f"\nFound {len(articles)} relevant articles:")
    for i, article in enumerate(articles[:10], 1):
        print(f"\n{i}. [{article.relevance_score}] {article.title[:60]}...")
        print(f"   Source: {article.source}")
        print(f"   URL: {article.url[:80]}...")

    # Test events discovery (search only, no scraping in test)
    print("\n" + "=" * 60)
    print("[TEST] Events Discovery Agent (Search Only)")
    print("-" * 40)
    events_agent = EventsDiscoveryAgent()
    events = await events_agent.discover_from_search()

    print(f"\nFound {len(events)} events:")
    for i, event in enumerate(events[:10], 1):
        print(f"\n{i}. {event.name[:60]}...")
        print(f"   Platform: {event.source_platform}")
        print(f"   URL: {event.url[:80]}...")

    print("\n" + "=" * 60)
    print("Test complete. No data was saved to database.")
    print("=" * 60)


async def run_immediate(job_type: str):
    """Run a specific job immediately"""
    from src.scheduler import DiscoveryScheduler

    scheduler = DiscoveryScheduler()
    await scheduler.run_now(job_type)


async def run_daemon():
    """Run scheduler in daemon mode"""
    from src.scheduler import run_scheduler

    print("=" * 60)
    print("BLKOUT Research Agent - Daemon Mode")
    print("=" * 60)
    print("\nScheduled jobs:")
    print("  - Daily discovery: 6:00 AM London time")
    print("  - Evening events: 6:00 PM London time")
    print("  - Weekly deep research: Sunday 3:00 AM")
    print("  - Weekly grant research: Monday 9:00 AM")
    print("\nPress Ctrl+C to stop.")
    print("=" * 60)

    await run_scheduler()


def main():
    parser = argparse.ArgumentParser(description="BLKOUT Research Agent")
    parser.add_argument(
        "--run-now",
        choices=["daily", "events", "weekly", "grants"],
        help="Run a specific job immediately",
    )
    parser.add_argument(
        "--test",
        action="store_true",
        help="Test mode (no database writes)",
    )

    args = parser.parse_args()

    # Check configuration
    if not args.test and not check_config():
        return 1

    # Run appropriate mode
    if args.test:
        asyncio.run(run_test())
    elif args.run_now:
        asyncio.run(run_immediate(args.run_now))
    else:
        asyncio.run(run_daemon())

    return 0


if __name__ == "__main__":
    exit(main())
