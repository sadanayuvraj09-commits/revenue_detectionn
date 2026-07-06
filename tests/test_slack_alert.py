import os
import httpx
from dotenv import load_dotenv

load_dotenv()

WEBHOOK_URL = os.getenv("SLACK_WEBHOOK_URL")

async def send_test_alert():
    message = {
        "text": " *Unbilled Revenue Detective* — Slack connection test successful!\n\n*Test Gap Detected:*\n• Developer: YUVRAJ\n• Date: 2026-06-23\n• GitHub Commits: 4\n• Hours Logged: 0\n• Summary: Developer made 4 commits but logged 0 hours."
    }
    async with httpx.AsyncClient() as client:
        response = await client.post(WEBHOOK_URL, json=message)
        if response.status_code == 200:
            print(" Slack alert sent successfully!")
        else:
            print(f" Failed: {response.status_code} - {response.text}")

import asyncio
asyncio.run(send_test_alert())