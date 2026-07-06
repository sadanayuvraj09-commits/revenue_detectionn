import asyncio

import bootstrap
from src.database import db

async def fix_dates():
    result = await db.detected_gaps.update_many(
        {"date": None},
        {"$set": {"date": "UNKNOWN"}}
    )
    print(f"Fixed {result.modified_count} gaps with missing dates")

if __name__ == "__main__":
    asyncio.run(fix_dates())
