import os
from dotenv import load_dotenv
from pymongo import MongoClient

import bootstrap
from src.config import get_settings

# Load environment variables
load_dotenv()
settings = get_settings()
MONGO_URI = settings.mongo_uri or os.getenv("MONGO_URI")

client = MongoClient(MONGO_URI)
db = client[settings.mongo_db_name]

developers = [
    {
        "developer_id": "YUVRAJ SADANA",
        "name": "Yuvraj Sadana",
        "email": "yuvraj@example.com",
        "role": "Backend Engineer",
        "team": "API Integration",
        "joined_date": "2026-06-01",
        "status": "active"
    },
    {
        "developer_id": "Dev002",
        "name": "Alice Sharma",
        "email": "alice@example.com",
        "role": "Frontend Engineer",
        "team": "UI/UX",
        "joined_date": "2026-06-10",
        "status": "active"
    }
]

db["developers"].insert_many(developers)
print("Inserted developers successfully")
