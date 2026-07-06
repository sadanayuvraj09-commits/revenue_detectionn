import asyncio

import bootstrap
from src.database import db

async def reset_gaps():
    result = await db.detected_gaps.delete_many({})
    print(f"Deleted {result.deleted_count} old gap documents.")

if __name__ == "__main__":
    asyncio.run(reset_gaps())
