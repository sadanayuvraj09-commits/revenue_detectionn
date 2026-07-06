import asyncio

import bootstrap
from src.database import db

async def fix_summaries():
    # Find all docs where summary contains "On None"
    docs = await db.detected_gaps.find({"summary": {"$regex": "On None"}}).to_list(100)

    if not docs:
        print("No summaries with 'On None' found.")
        return

    for gap in docs:
        # Replace "On None" with "On UNKNOWN"
        new_summary = gap["summary"].replace("On None", "On UNKNOWN")

        await db.detected_gaps.update_one(
            {"_id": gap["_id"]},
            {"$set": {"summary": new_summary}}
        )

        print(f"Fixed summary for {gap.get('developer_id')}")

if __name__ == "__main__":
    asyncio.run(fix_summaries())
