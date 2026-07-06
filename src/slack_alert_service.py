import os

import httpx
from dotenv import load_dotenv


load_dotenv()


async def send_gap_alert(gap: dict) -> None:
    webhook_url = os.getenv("SLACK_WEBHOOK_URL")
    if not webhook_url:
        print("Warning: SLACK_WEBHOOK_URL is not set. Skipping Slack gap alert.")
        return

    summary = gap.get("summary") or "No summary available yet."
    message = {
        "text": (
            "🚨 *Unbilled Hours Detected*\n"
            f"👤 Developer: {gap.get('developer_id', 'UNKNOWN')}\n"
            f"📅 Date: {gap.get('date', 'UNKNOWN')}\n"
            f"💻 GitHub Commits: {gap.get('github_count', 0)}\n"
            f"⏱ Hours Logged: {gap.get('hours_logged', 0)}\n"
            f"❓ Reason: {gap.get('reason', 'Unknown')}\n"
            f"📝 Summary: {summary}"
        )
    }

    try:
        async with httpx.AsyncClient(timeout=10) as client:
            response = await client.post(webhook_url, json=message)
            if response.status_code != 200:
                print(f"Slack gap alert failed: {response.status_code} - {response.text}")
    except Exception as exc:
        print(f"Slack gap alert error: {exc}")
