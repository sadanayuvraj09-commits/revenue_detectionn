import asyncio
import os

from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient


load_dotenv()

MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "unbilled_detective")


SAMPLE_TIMESHEETS = [
    {
        "developer_id": "YUVRAJ SADANA",
        "date": "2026-06-22",
        "hours_logged": 7.5,
        "project": "revenue_detective_test",
        "notes": "Backend integration work logged.",
    },
    {
        "developer_id": "YUVRAJ SADANA",
        "date": "2026-06-23",
        "hours_logged": 0,
        "project": "revenue_detective_test",
        "notes": "Activity exists but no billable time entered.",
    },
    {
        "developer_id": "YUVRAJ SADANA",
        "date": "2026-06-24",
        "hours_logged": 6.0,
        "project": "revenue_detective_test",
        "notes": "Follow-up implementation work.",
    },
    {
        "developer_id": "YUVRAJ",
        "date": "2026-06-22",
        "hours_logged": 0,
        "project": "revenue_detective_test",
        "notes": "Zero-hour entry for gap detection testing.",
    },
    {
        "developer_id": "YUVRAJ",
        "date": "2026-06-23",
        "hours_logged": 7.5,
        "project": "revenue_detective_test",
        "notes": "Normal full-day entry for comparison testing.",
    },
]


async def seed_timesheets() -> None:
    if not MONGO_URI:
        raise RuntimeError("MONGO_URI is not configured. Add it to your .env file.")

    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]

    inserted = 0
    updated = 0

    for entry in SAMPLE_TIMESHEETS:
        result = await db.timesheet_entries.update_one(
            {"developer_id": entry["developer_id"], "date": entry["date"]},
            {"$set": entry},
            upsert=True,
        )
        if result.upserted_id:
            inserted += 1
        else:
            updated += 1

    print(f"Seeded timesheets: inserted={inserted}, updated={updated}, total={len(SAMPLE_TIMESHEETS)}")
    client.close()


if __name__ == "__main__":
    asyncio.run(seed_timesheets())
