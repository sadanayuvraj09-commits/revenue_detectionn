import bootstrap
from src.config import get_settings
from src.activity_utils import DEVELOPER_ALIASES
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError

settings = get_settings()
client = MongoClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

for collection_name in ["activity_logs", "detected_gaps", "timesheet_entries"]:
    coll = db[collection_name]
    for old_id, canonical_id in DEVELOPER_ALIASES.items():
        if old_id == canonical_id:
            continue

        docs = list(coll.find({"developer_id": old_id}))
        updated = 0
        deleted_dupes = 0

        for doc in docs:
            try:
                coll.update_one(
                    {"_id": doc["_id"]},
                    {"$set": {"developer_id": canonical_id}}
                )
                updated += 1
            except DuplicateKeyError:
                # A canonical record already exists for this developer+date.
                # The old duplicate is redundant, so remove it instead.
                coll.delete_one({"_id": doc["_id"]})
                deleted_dupes += 1

        print(f"{collection_name}: {old_id} -> {canonical_id} "
              f"({updated} updated, {deleted_dupes} duplicates removed)")