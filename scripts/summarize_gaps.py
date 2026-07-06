import asyncio

import bootstrap
from src.database import db

async def summarize_pending_gaps():
    """
    Fetch gaps with status = 'pending', generate summaries,
    and update them in MongoDB with status = 'summarized'.
    """
    gaps = await db.detected_gaps.find({"status": "pending"}).to_list(100)

    if not gaps:
        print("No pending gaps found.")
        return

    for gap in gaps:
        # Ensure date fallback (handles None, "None", empty string)
        raw_date = gap.get("date")
        if not raw_date or str(raw_date).strip().lower() in ["none", "null", ""]:
            date = "UNKNOWN"
        else:
            date = str(raw_date)

        # Build summary text
        summary = (
            f"On {date}, {gap.get('developer_id', 'UNKNOWN')} had "
            f"{gap.get('github_count', 0)} GitHub commits, "
            f"{gap.get('slack_count', 0)} Slack messages, "
            f"{gap.get('jira_count', 0)} Jira updates, "
            f"but logged {gap.get('hours_logged', 0)} hours in timesheets."
        )

        # Update MongoDB record
        await db.detected_gaps.update_one(
            {"_id": gap["_id"]},
            {"$set": {"summary": summary, "status": "summarized"}}
        )

        print(f"Summarized gap for {gap.get('developer_id', 'UNKNOWN')} on {date}")

if __name__ == "__main__":
    asyncio.run(summarize_pending_gaps())
