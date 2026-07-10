import bootstrap
from src.database import db
import asyncio


async def main():
    result = await db["detected_gaps_snapshot"].delete_many({})
    print(f"Cleared detected_gaps_snapshot ({result.deleted_count} removed)")


asyncio.run(main())