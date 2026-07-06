import os
from dotenv import load_dotenv
from pymongo import MongoClient

import bootstrap
from src.config import get_settings

# Load environment variables
load_dotenv()

settings = get_settings()
MONGO_URI = settings.mongo_uri or os.getenv("MONGO_URI")

# Connect to MongoDB
client = MongoClient(MONGO_URI)
db = client[settings.mongo_db_name]

# Delete old commit documents without commit_id
result = db.activity_logs.delete_many({"commit_id": {"$exists": False}})
print(f"Deleted {result.deleted_count} old commit documents.")

# Show remaining documents
for doc in db.activity_logs.find().limit(5):
    print(doc)
