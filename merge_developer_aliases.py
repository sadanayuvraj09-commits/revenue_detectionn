import bootstrap
from src.config import get_settings
from src.activity_utils import DEVELOPER_ALIASES
from pymongo import MongoClient

settings = get_settings()
client = MongoClient(settings.mongo_uri)
db = client[settings.mongo_db_name]

for collection_name in ["activity_logs", "detected_gaps", "timesheet_entries"]:
    coll = db[collection_name]
    for old_id, canonical_id in DEVELOPER_ALIASES.items():
        if old_id == canonical_id:
            continue
        result = coll.update_many({"developer_id": old_id}, {"$set": {"developer_id": canonical_id}})
        print(f"{collection_name}: {old_id} -> {canonical_id} ({result.modified_count} updated)")