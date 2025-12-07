"""
Scheduler - Automated execution of discovery agents
"""

import asyncio
import os
from datetime import datetime
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from .agents import PlanningAgent
from .grants_agent import GrantPlanningAgent


class DiscoveryScheduler:
    """Schedules and runs discovery agents"""

    def __init__(self):
        self.scheduler = AsyncIOScheduler(timezone="Europe/London")
        self.agent = PlanningAgent()
        self.grants_agent = GrantPlanningAgent()

    def setup_schedules(self):
        """Configure all scheduled jobs"""

        # Daily news + events discovery at 6 AM
        self.scheduler.add_job(
            self._run_daily,
            CronTrigger(hour=6, minute=0),
            id="daily_discovery",
            name="Daily News & Events Discovery",
            replace_existing=True,
        )

        # Second events check at 6 PM (events often posted during day)
        self.scheduler.add_job(
            self._run_events_only,
            CronTrigger(hour=18, minute=0),
            id="evening_events",
            name="Evening Events Check",
            replace_existing=True,
        )

        # Weekly deep research on Sunday at 3 AM
        self.scheduler.add_job(
            self._run_weekly,
            CronTrigger(day_of_week="sun", hour=3, minute=0),
            id="weekly_deep_research",
            name="Weekly Deep Research",
            replace_existing=True,
        )

        # Weekly grant research on Monday at 9 AM
        self.scheduler.add_job(
            self._run_grants,
            CronTrigger(day_of_week="mon", hour=9, minute=0),
            id="weekly_grants",
            name="Weekly Grant Research",
            replace_existing=True,
        )

        # Mid-week grant research on Wednesday at 2 PM
        self.scheduler.add_job(
            self._run_grants,
            CronTrigger(day_of_week="wed", hour=14, minute=0),
            id="midweek_grants",
            name="Mid-week Grant Research",
            replace_existing=True,
        )

        print("[Scheduler] Jobs configured:")
        for job in self.scheduler.get_jobs():
            print(f"  - {job.name}: {job.trigger}")

    async def _run_daily(self):
        """Execute daily discovery"""
        print(f"[Scheduler] Running daily discovery at {datetime.now()}")
        try:
            results = await self.agent.run_daily_discovery()
            print(f"[Scheduler] Daily results: {results}")
        except Exception as e:
            print(f"[Scheduler] Daily discovery error: {e}")

    async def _run_events_only(self):
        """Execute events-only discovery"""
        print(f"[Scheduler] Running evening events check at {datetime.now()}")
        try:
            results = await self.agent.events_agent.discover_and_save()
            print(f"[Scheduler] Events results: {results}")
        except Exception as e:
            print(f"[Scheduler] Events discovery error: {e}")

    async def _run_weekly(self):
        """Execute weekly deep research"""
        print(f"[Scheduler] Running weekly deep research at {datetime.now()}")
        try:
            results = await self.agent.run_weekly_deep_research()
            print(f"[Scheduler] Weekly results: {results}")
        except Exception as e:
            print(f"[Scheduler] Weekly research error: {e}")

    async def _run_grants(self):
        """Execute weekly grant research"""
        print(f"[Scheduler] Running grant research at {datetime.now()}")
        try:
            results = await self.grants_agent.run_weekly_research()
            print(f"[Scheduler] Grants results: {results}")
        except Exception as e:
            print(f"[Scheduler] Grant research error: {e}")

    def start(self):
        """Start the scheduler"""
        self.setup_schedules()
        self.scheduler.start()
        print("[Scheduler] Started")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("[Scheduler] Stopped")

    async def run_now(self, job_type: str = "daily"):
        """Manually trigger a job"""
        if job_type == "daily":
            await self._run_daily()
        elif job_type == "events":
            await self._run_events_only()
        elif job_type == "weekly":
            await self._run_weekly()
        elif job_type == "grants":
            await self._run_grants()
        else:
            print(f"Unknown job type: {job_type}")


async def run_scheduler():
    """Run the scheduler as main process"""
    scheduler = DiscoveryScheduler()
    scheduler.start()

    try:
        # Keep running
        while True:
            await asyncio.sleep(60)
    except KeyboardInterrupt:
        scheduler.stop()


if __name__ == "__main__":
    asyncio.run(run_scheduler())
