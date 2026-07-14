import asyncio
import sys

import bootstrap
from src.config import get_settings
from src.alias_service import load_developer_aliases
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

settings = get_settings()
client = MongoClient(settings.mongo_uri)
db = client[settings.mongo_db_name]


def main(repo_id: str) -> None:
    aliases = asyncio.run(load_developer_aliases(repo_id))

    for collection_name in ["activity_logs", "detected_gaps", "timesheet_entries"]:
        coll = db[collection_name]
        for old_id, canonical_id in aliases.items():
            if old_id == canonical_id:
                continue

            docs = list(coll.find({"developer_id": old_id, "repo_id": repo_id}))
            updated = 0
            deleted_dupes = 0

            for doc in docs:
                try:
                    coll.update_one({"_id": doc["_id"]}, {"$set": {"developer_id": canonical_id}})
                    updated += 1
                except DuplicateKeyError:
                    coll.delete_one({"_id": doc["_id"]})
                    deleted_dupes += 1

            print(f"{collection_name}: {old_id} -> {canonical_id} ({updated} updated, {deleted_dupes} duplicates removed)")


if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Usage: python merge_developer_aliases.py <repo_id>")
        sys.exit(1)
    main(sys.argv[1])