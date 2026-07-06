import asyncio

import bootstrap
from src.database import db

async def check_gaps():
    docs = await db.detected_gaps.find().to_list(10)
    for d in docs:
        print(d)

if __name__ == "__main__":
    asyncio.run(check_gaps())
