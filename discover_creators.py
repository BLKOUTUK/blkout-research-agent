#!/usr/bin/env python3
"""
Creator Discovery CLI - Find UK Black queer creators automatically

Usage:
    python discover_creators.py --max 50
    python discover_creators.py --platform youtube --max 20
    python discover_creators.py --dry-run  # Test mode, no database writes
"""

import asyncio
import sys
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from src.creator_discovery import CreatorDiscoveryAgent, main

if __name__ == "__main__":
    print("🎬 The Channel - Creator Discovery Agent")
    print("=========================================\n")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n\n⏸️  Discovery interrupted by user")
        sys.exit(0)
    except Exception as e:
        print(f"\n❌ Fatal error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
