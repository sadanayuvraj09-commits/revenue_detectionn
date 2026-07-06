import asyncio

import bootstrap
from src.database import db

async def main():
    result = await db.activity_logs.insert_one({"test": "ok"})
    print("Inserted test document with id:", result.inserted_id)

if __name__ == "__main__":
    asyncio.run(main())
