import asyncio, os
from dotenv import load_dotenv
from motor.motor_asyncio import AsyncIOMotorClient
from src.activity_utils import normalize_repo_id

load_dotenv()
MONGO_URI = os.getenv("MONGO_URI")
DB_NAME = os.getenv("MONGO_DB_NAME", "unbilled_detective")

COLLECTIONS = ["activity_logs", "developers", "timesheet_entries",
               "detected_gaps", "detected_gaps_snapshot", "alerts"]

async def backfill_repo_id():
    default_repo_id = normalize_repo_id(os.getenv("GITHUB_OWNER"), os.getenv("GITHUB_REPO"))
    client = AsyncIOMotorClient(MONGO_URI)
    db = client[DB_NAME]
    for name in COLLECTIONS:
        result = await db[name].update_many(
            {"repo_id": {"$exists": False}},
            {"$set": {"repo_id": default_repo_id}},
        )
        print(f"{name}: matched={result.matched_count}, modified={result.modified_count}")
    client.close()

if __name__ == "__main__":
    asyncio.run(backfill_repo_id())