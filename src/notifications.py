"""
Email Notifications for Research Agent

Sends digest emails for:
- New grant discoveries
- Top priority opportunities
"""

import os
import httpx
from typing import List, Dict, Any, Optional
from datetime import datetime


class EmailNotifier:
    """Send email notifications via Resend"""

    def __init__(self):
        self.api_key = os.getenv("RESEND_API_KEY")
        self.from_email = os.getenv("NOTIFICATION_FROM_EMAIL", "research@blkoutuk.com")
        self.to_email = os.getenv("NOTIFICATION_TO_EMAIL", "hello@blkoutuk.com")
        self.api_url = "https://api.resend.com/emails"

    async def send_email(self, subject: str, html_content: str) -> bool:
        """Send an email via Resend API"""
        if not self.api_key:
            print("[Notifications] RESEND_API_KEY not configured, skipping email")
            return False

        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                    },
                    json={
                        "from": self.from_email,
                        "to": [self.to_email],
                        "subject": subject,
                        "html": html_content,
                    },
                    timeout=30.0,
                )

                if response.status_code == 200:
                    print(f"[Notifications] Email sent: {subject}")
                    return True
                else:
                    print(f"[Notifications] Email failed: {response.status_code} - {response.text}")
                    return False

        except Exception as e:
            print(f"[Notifications] Email error: {e}")
            return False

    async def send_grants_digest(
        self,
        new_grants: List[Dict[str, Any]],
        top_priority: List[Dict[str, Any]],
        run_stats: Dict[str, Any],
    ) -> bool:
        """Send grant research digest email"""

        if not new_grants and not top_priority:
            print("[Notifications] No grants to report, skipping email")
            return False

        subject = f"BLKOUT Grants Digest: {len(new_grants)} new opportunities found"

        html = self._build_grants_email(new_grants, top_priority, run_stats)

        return await self.send_email(subject, html)

    def _build_grants_email(
        self,
        new_grants: List[Dict[str, Any]],
        top_priority: List[Dict[str, Any]],
        run_stats: Dict[str, Any],
    ) -> str:
        """Build HTML email for grants digest"""

        now = datetime.utcnow().strftime("%d %B %Y, %H:%M UTC")

        html = f"""
<!DOCTYPE html>
<html>
<head>
    <style>
        body {{ font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif; line-height: 1.6; color: #333; max-width: 600px; margin: 0 auto; padding: 20px; }}
        .header {{ background: #1a1a2e; color: white; padding: 20px; border-radius: 8px 8px 0 0; }}
        .header h1 {{ margin: 0; font-size: 24px; }}
        .header p {{ margin: 5px 0 0; opacity: 0.8; font-size: 14px; }}
        .section {{ background: #f8f9fa; padding: 20px; margin-bottom: 2px; }}
        .section h2 {{ color: #1a1a2e; margin-top: 0; font-size: 18px; border-bottom: 2px solid #e74c3c; padding-bottom: 8px; }}
        .grant {{ background: white; padding: 15px; margin-bottom: 10px; border-radius: 6px; border-left: 4px solid #3498db; }}
        .grant.high {{ border-left-color: #e74c3c; }}
        .grant.medium {{ border-left-color: #f39c12; }}
        .grant h3 {{ margin: 0 0 8px; font-size: 16px; }}
        .grant h3 a {{ color: #1a1a2e; text-decoration: none; }}
        .grant h3 a:hover {{ text-decoration: underline; }}
        .grant .meta {{ font-size: 13px; color: #666; margin-bottom: 8px; }}
        .grant .score {{ display: inline-block; background: #e74c3c; color: white; padding: 2px 8px; border-radius: 12px; font-size: 12px; font-weight: bold; }}
        .grant .description {{ font-size: 14px; color: #555; }}
        .stats {{ background: #1a1a2e; color: white; padding: 15px 20px; border-radius: 0 0 8px 8px; }}
        .stats span {{ margin-right: 20px; }}
        .footer {{ text-align: center; padding: 20px; color: #888; font-size: 12px; }}
    </style>
</head>
<body>
    <div class="header">
        <h1>BLKOUT Grant Research</h1>
        <p>{now}</p>
    </div>
"""

        # New discoveries section
        if new_grants:
            html += """
    <div class="section">
        <h2>New Discoveries</h2>
"""
            for grant in new_grants[:10]:  # Limit to 10
                priority_class = "high" if grant.get("priority") == "high" else "medium" if grant.get("priority") == "medium" else ""
                score = grant.get("fit_score", 0)

                html += f"""
        <div class="grant {priority_class}">
            <h3><a href="{grant.get('application_url', '#')}">{grant.get('title', 'Untitled')[:80]}</a></h3>
            <div class="meta">
                <strong>{grant.get('funder_name', 'Unknown Funder')}</strong>
                {f" &bull; Deadline: {grant.get('deadline_date')}" if grant.get('deadline_date') else ""}
                &bull; <span class="score">{score}% fit</span>
            </div>
            <div class="description">{(grant.get('notes', '') or '')[:200]}...</div>
        </div>
"""
            html += "    </div>"

        # Top priority section
        if top_priority:
            html += """
    <div class="section">
        <h2>Top 10 Priority Opportunities</h2>
"""
            for i, grant in enumerate(top_priority[:10], 1):
                priority_class = "high" if grant.get("priority") == "high" else "medium"
                score = grant.get("fit_score", 0)
                deadline = grant.get("deadline_date")
                deadline_text = f" &bull; <strong>Deadline: {deadline}</strong>" if deadline else ""

                html += f"""
        <div class="grant {priority_class}">
            <h3>#{i} <a href="{grant.get('application_url', '#')}">{grant.get('title', 'Untitled')[:80]}</a></h3>
            <div class="meta">
                <strong>{grant.get('funder_name', 'Unknown Funder')}</strong>
                {deadline_text}
                &bull; <span class="score">{score}% fit</span>
            </div>
            {f"<div class='description'>{grant.get('funder_advice', '')[:150]}...</div>" if grant.get('funder_advice') else ""}
        </div>
"""
            html += "    </div>"

        # Stats footer
        html += f"""
    <div class="stats">
        <span>Discovered: {run_stats.get('discovered', 0)}</span>
        <span>New: {run_stats.get('inserted', 0)}</span>
        <span>Duplicates: {run_stats.get('skipped', 0)}</span>
    </div>

    <div class="footer">
        <p>BLKOUT Research Agent &bull; Automated grant discovery</p>
        <p>Review all opportunities at your Supabase dashboard</p>
    </div>
</body>
</html>
"""
        return html


# Singleton
_notifier: Optional[EmailNotifier] = None


def get_notifier() -> EmailNotifier:
    global _notifier
    if _notifier is None:
        _notifier = EmailNotifier()
    return _notifier
